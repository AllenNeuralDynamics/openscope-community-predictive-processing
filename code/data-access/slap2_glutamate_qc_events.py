#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Event-based signal/noise QC for SLAP2 glutamate imaging.

Computes per-synapse quality metrics from iGluSnFR4f dF/F traces using an
event-amplitude scheme that mirrors the mesoscope ophys QC agreed in
discussion #156, so the SLAP2 column of Figure 7 is directly comparable to
the mesoscope column:

  * events are detected, not stimulus-averaged;
  * every event amplitude is expressed in SDs above a *non-event* baseline;
  * each source is classified by the SD composition of its events, and the
    distribution panels are broken down by the resulting classes.

Event detection follows the temporal half of the SILo matched filter used for
SLAP2 source extraction (Methods): a decaying exponential matched to the
indicator (tau = 20 ms for iGluSnFR4f).

Two details differ from the mesoscope pipeline, both forced by the data:

  * The mesoscope reads OASIS deconvolved events straight out of the Allen
    pipeline. SLAP2 NWBs ship only dF/F and F0, so events are detected here.
  * Detection runs at 3 SD rather than the mesoscope's 2 SD floor. At 200 Hz a
    2 SD floor admits ~10% false positives; 3 SD holds them under 1%, measured
    per source from the negative-going peaks of the same filtered trace, which
    contain no glutamate events and so act as an empirical noise null. The
    >4 SD bin boundary is kept identical to the mesoscope scheme.

Baseline noise is estimated from the below-median half of the filtered trace,
which positive-going release events cannot contaminate. SILo extracts sources
with non-negative matrix factorisation, so a sparse source can sit at exactly
zero for more than half the session; its lower half then holds no noise and the
estimate collapses. Those sources are flagged `rectified_trace` and reported as
their own class rather than being given a fabricated SNR.
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# iGluSnFR4f decay constant used by the SLAP2 SILo source extractor (Methods).
TAU_IGLUSNFR4F_S = 0.020

# Event-amplitude thresholds, in SDs above the non-event baseline.
SD_DETECT = 3.0   # detection floor (false-positive controlled, see module docstring)
SD_LARGE = 4.0    # large-event boundary, identical to the mesoscope scheme (#156)


def sampling_interval(ts: np.ndarray) -> float:
    """Median sample interval, tolerant of gaps and missing timestamps.

    Some sessions carry NaN timestamps (sub-828409 2025-11-20 has 5883 of them
    on DMD2). A plain `np.median` propagates the NaN into the kernel length and
    the run dies on `int(nan)`, so take the nanmedian and validate.
    """
    dt = float(np.nanmedian(np.diff(np.asarray(ts, dtype=float))))
    if not np.isfinite(dt) or dt <= 0:
        raise ValueError(f"Could not determine a sampling interval (got {dt!r}).")
    return dt


def matched_filter_kernel(dt: float, tau: float = TAU_IGLUSNFR4F_S) -> np.ndarray:
    """Unit-energy causal exponential kernel matched to the indicator decay."""
    if not np.isfinite(dt) or dt <= 0:
        raise ValueError(f"matched_filter_kernel needs a positive dt, got {dt!r}.")
    n = max(3, int(np.ceil(5.0 * tau / dt)))
    k = np.exp(-np.arange(n) * dt / tau)
    return (k / np.linalg.norm(k)).astype(np.float32)


def interpolate_gaps(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Linearly interpolate NaN acquisition gaps.

    Returns (filled_trace, valid_mask). Filtering across a NaN would poison a
    whole kernel-width of output, so gaps are bridged before convolution and
    the interpolated samples are excluded from detection afterwards.
    """
    valid = np.isfinite(x)
    if valid.all():
        return x, valid
    filled = x.copy()
    if valid.any():
        filled[~valid] = np.interp(
            np.flatnonzero(~valid), np.flatnonzero(valid), x[valid]
        )
    else:
        filled[:] = 0.0
    return filled, valid


def baseline_noise(filtered: np.ndarray) -> tuple[float, float]:
    """Noise SD from the event-free (below-median) half of the trace.

    Glutamate release events are strictly positive-going, so the lower half of
    the filtered-trace distribution carries noise only. Estimating the SD there
    avoids the upward bias of a plain MAD and the downward bias of iteratively
    masking positive excursions.

    Returns (noise_sd, baseline_median).
    """
    x = filtered[np.isfinite(filtered)]
    if x.size < 100:
        return np.nan, np.nan
    med = float(np.median(x))
    lower = x[x < med]
    if lower.size < 50:
        return np.nan, med
    sd = float(1.4826 * np.median(med - lower))

    # SILo extracts sources with *non-negative* matrix factorisation, so a
    # sparse source can sit at exactly zero for more than half the session. Its
    # lower half then carries no noise at all and this estimator collapses
    # towards zero, which would turn every detection into a >4 SD "event" and
    # report SNRs of order 1e16. There is no noise left to measure in a
    # rectified trace, so report it as undefined and let the caller flag the
    # source rather than emit a fabricated number.
    scale = float(np.percentile(x, 95) - med)
    if sd <= 0 or (scale > 0 and sd < 1e-4 * scale):
        return np.nan, med
    return sd, med


def _local_maxima(z: np.ndarray, thr: float, refractory: int) -> np.ndarray:
    """Indices of local maxima above `thr`, thinned by a refractory period."""
    cand = np.flatnonzero(
        (z[1:-1] >= thr) & (z[1:-1] >= z[:-2]) & (z[1:-1] > z[2:])
    ) + 1
    keep: list[int] = []
    last = -np.inf
    for i in cand:
        if i - last >= refractory:
            keep.append(int(i))
            last = i
        elif keep and z[i] > z[keep[-1]]:
            keep[-1] = int(i)  # taller peak wins inside the refractory window
            last = i
    return np.asarray(keep, dtype=int)


def detect_events(trace: np.ndarray, dt: float, tau: float = TAU_IGLUSNFR4F_S):
    """Detect glutamate events on one dF/F trace.

    Returns a dict with event indices and amplitudes (in SD), the matched-filter
    z-scored trace, the noise SD, and the count of negative-going peaks that
    serves as the empirical false-positive estimate.
    """
    filled, valid = interpolate_gaps(np.asarray(trace, dtype=np.float32))
    kernel = matched_filter_kernel(dt, tau)
    filt = np.convolve(filled, kernel, mode="same")
    filt[~valid] = np.nan  # interpolated samples take no part in detection

    sd, med = baseline_noise(filt)
    if not np.isfinite(sd) or sd <= 0:
        empty = np.empty(0, dtype=int)
        return {"idx": empty, "amp_sd": np.empty(0), "z": filt,
                "noise_sd": np.nan, "n_false_pos": 0, "n_valid": int(valid.sum())}

    z = (filt - med) / sd
    refractory = max(1, int(round(tau / dt)))

    # Invalid samples must sit at -inf in whichever direction is being scanned,
    # so that a gap can never masquerade as a peak.
    z_pos = np.where(np.isfinite(z), z, -np.inf)
    z_neg = np.where(np.isfinite(z), -z, -np.inf)

    idx = _local_maxima(z_pos, SD_DETECT, refractory)
    n_false_pos = _local_maxima(z_neg, SD_DETECT, refractory).size

    return {"idx": idx, "amp_sd": z[idx], "z": z, "noise_sd": sd,
            "n_false_pos": int(n_false_pos), "n_valid": int(valid.sum())}


def event_amplitudes_raw(trace: np.ndarray, idx: np.ndarray, dt: float,
                         raw_noise: float, tau: float = TAU_IGLUSNFR4F_S):
    """Event amplitude measured on the raw dF/F, in units of raw-trace noise SD.

    Detection happens on the matched-filtered trace, where the SNR is best. But
    the filter has unit energy, so its noise SD sits on a different scale than
    the raw trace: a "4 SD event" measured there is not the same quantity the
    mesoscope pipeline reports, which measures peak dF/F above a local baseline
    in raw-trace MAD SDs (#156). Amplitude is therefore re-measured here on the
    raw trace so the >4 SD boundary means the same thing in both columns.

    This also separates detection from amplitude classification, exactly as the
    mesoscope does (OASIS detects; the SD bins classify). A detection can then
    legitimately land below 2 SD of raw noise, which is what makes the
    three-way <2 / 2-4 / >4 composition available at all.

    Local baseline is the median over [-3tau, -1tau] before the detection; the
    peak is the maximum over [0, +2tau] after it.
    """
    if idx.size == 0 or not np.isfinite(raw_noise) or raw_noise <= 0:
        return np.full(idx.size, np.nan)

    n = trace.size
    pre_a, pre_b = int(round(3 * tau / dt)), int(round(tau / dt))
    post = max(1, int(round(2 * tau / dt)))
    amps = np.full(idx.size, np.nan, dtype=float)
    for k, i in enumerate(idx):
        b0, b1 = max(0, i - pre_a), max(1, i - pre_b)
        base_win = trace[b0:b1]
        peak_win = trace[i:min(n, i + post + 1)]
        if base_win.size == 0 or peak_win.size == 0:
            continue
        base = np.nanmedian(base_win)
        peak = np.nanmax(peak_win)
        if np.isfinite(base) and np.isfinite(peak):
            amps[k] = (peak - base) / raw_noise
    return amps


def drop_untimed_events(idx: np.ndarray, amp: np.ndarray, ts: np.ndarray):
    """Discard detections whose timestamp is missing.

    A NaN timestamp cannot be placed in a stimulus context or counted toward a
    rate, so those detections are dropped rather than silently carried as NaN.
    """
    if idx.size == 0:
        return idx, amp
    keep = np.isfinite(np.asarray(ts, dtype=float)[idx])
    return idx[keep], amp[keep]


def resolve_layout(nwb) -> dict:
    """Locate the dF/F series, images and segmentation, whichever layout is used.

    DANDI 001424 ships three NWB layouts, and a loader that hardcodes one only
    works on a quarter of the archive:

    ``dff``          ``processing/ophys/dff/DMD{n}_dff`` — sub-794237 only.
    ``fluorescence`` ``processing/ophys/Fluorescence_DMD{n}/DMD{n}_dFF``.
    ``dual``         same, but ``DMD{n}_dFF_green`` (iGluSnFR4f glutamate) plus
                     ``DMD{n}_dFF_red`` (RCaMP3 calcium) over the same sources.

    Images and segmentation move too: the ``dff`` layout keeps them in
    ``acquisition`` with a single mean image, the others keep them in
    ``processing/ophys`` with per-channel mean images.

    Returns a dict of accessor callables plus the detected layout name; the
    glutamate channel is always what ``dff_series`` yields, so downstream code
    is layout-agnostic.
    """
    ophys = nwb.processing["ophys"]
    ifaces = ophys.data_interfaces

    layout, dff, calcium = None, {}, {}
    if "dff" in ifaces:
        layout = "dff"
        for dmd in (1, 2):
            key = f"DMD{dmd}_dff"
            if key in ifaces["dff"].roi_response_series:
                dff[dmd] = ifaces["dff"].roi_response_series[key]
    else:
        for dmd in (1, 2):
            name = f"Fluorescence_DMD{dmd}"
            if name not in ifaces:
                continue
            rrs = ifaces[name].roi_response_series
            if f"DMD{dmd}_dFF_green" in rrs:
                layout = "dual"
                dff[dmd] = rrs[f"DMD{dmd}_dFF_green"]
                if f"DMD{dmd}_dFF_red" in rrs:
                    calcium[dmd] = rrs[f"DMD{dmd}_dFF_red"]
            elif f"DMD{dmd}_dFF" in rrs:
                layout = layout or "fluorescence"
                dff[dmd] = rrs[f"DMD{dmd}_dFF"]
    if not dff:
        raise RuntimeError("No SLAP2 dF/F series found under processing['ophys'].")

    def image(dmd: int, kind: str):
        """Activity or mean image for one DMD, wherever this layout keeps it."""
        names = ([f"DMD{dmd}_{kind}_image"] if kind == "activity" else
                 [f"DMD{dmd}_mean_image", f"DMD{dmd}_mean_image_channel0",
                  f"DMD{dmd}_mean_image_channel1"])
        for src in (nwb.acquisition, ifaces):
            for n in names:
                if n in src:
                    # Stored shapes vary: (H, W), (1, H, W) and (1, H, W, 1) all
                    # appear across the archive. Squeeze first, then drop a
                    # leading frame axis if one genuinely remains.
                    data = np.squeeze(np.asarray(src[n].data))
                    return data[0] if data.ndim == 3 else data
        return None

    def segmentation(dmd: int):
        if "ImageSegmentation" not in ifaces:
            return None
        seg = ifaces["ImageSegmentation"].plane_segmentations
        for n in (f"DMD{dmd}_plane_segmentation", f"PlaneSegmentation_DMD{dmd}"):
            if n in seg:
                return seg[n]
        return None

    return {"layout": layout, "dff_series": dff, "calcium_series": calcium,
            "image": image, "segmentation": segmentation,
            "dmds": sorted(dff), "has_calcium": bool(calcium)}


def stimulus_table(nwb) -> pd.DataFrame:
    """Stimulus presentations with a context label, from whichever table exists.

    Older sessions pack every block into one ``stimulus_presentations`` (or
    ``gratings``) table, so context has to be inferred. Newer dual-channel
    sessions ship one interval table per block — ``motor_oddball``,
    ``standard_control``, ``rf_mapping`` and friends — which names the context
    directly and is far more reliable than inferring it.
    """
    iv = nwb.intervals
    single = next((n for n in ("stimulus_presentations", "gratings") if n in iv), None)
    named = [n for n in iv if n not in ("stimulus_presentations", "gratings", "epochs",
                                        "trials", "invalid_times")]

    if named:
        frames = []
        for name in sorted(named):
            df = iv[name].to_dataframe()
            if "start_time" not in df.columns or df.empty:
                continue
            df["context"] = name.replace("_", " ")
            df["block_table"] = name
            frames.append(df)
        if frames:
            out = pd.concat(frames, ignore_index=True).sort_values("start_time")
            out.attrs["context_source"] = "interval tables"
            return out.reset_index(drop=True)

    if single is None:
        raise RuntimeError("No stimulus interval table found.")
    out = label_contexts(iv[single].to_dataframe())
    out.attrs["context_source"] = "inferred from orientation statistics"
    return out


def label_contexts(stim: pd.DataFrame) -> pd.DataFrame:
    """Label each stimulus presentation with its experimental context.

    Splits the session into the control (random-orientation) blocks, the
    oddball block (dominant standard orientation plus rare deviants), and the
    receptive-field mapping block.
    """
    st = stim.copy().reset_index(drop=True)
    st["ori"] = st["orientation"].round(3)
    st["context"] = "unassigned"

    is_rf = st["diameter"] == 20
    st.loc[is_rf, "context"] = "RF mapping"

    ff_pos = np.flatnonzero(~is_rf.values)
    ori = st["ori"].values[ff_pos]
    standard = float(pd.Series(ori).value_counts().idxmax())

    # The oddball block is the stretch where the standard orientation dominates.
    frac_std = (
        pd.Series((ori == standard).astype(float))
        .rolling(101, center=True, min_periods=25).mean().values
    )
    in_oddball = frac_std > 0.5

    ctx = st["context"].values.astype(object)
    contrast = st["contrast"].values
    for pos, gi in enumerate(ff_pos):
        if contrast[gi] == 0:
            ctx[gi] = "Blank"
        elif in_oddball[pos]:
            ctx[gi] = "Oddball standard" if ori[pos] == standard else "Oddball deviant"
        else:
            ctx[gi] = "Control (random ori)"
    st["context"] = ctx
    st.attrs["standard_orientation"] = standard
    return st


def assign_event_contexts(event_times: np.ndarray, stim: pd.DataFrame) -> np.ndarray:
    """Map each event time onto the stimulus context it occurred in."""
    ctx = stim[["start_time", "stop_time", "context"]].sort_values("start_time")
    starts = ctx["start_time"].values
    stops = ctx["stop_time"].values
    names = ctx["context"].values

    labels = np.full(event_times.size, "Inter-stimulus", dtype=object)
    pos = np.searchsorted(starts, event_times, side="right") - 1
    ok = (pos >= 0) & (pos < starts.size)
    inside = np.zeros(event_times.size, dtype=bool)
    inside[ok] = event_times[ok] <= stops[pos[ok]]
    labels[inside] = names[pos[inside]]
    return labels


CLASS_FEATURES = ["frac_events_lt2sd", "frac_events_2_4sd", "frac_events_gt4sd"]
CLASS_NAMES = ["Low SNR", "Intermediate", "High SNR"]


def assign_classes(metrics: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    """Cluster sources into three quality classes from their event statistics.

    Mirrors the mesoscope approach of clustering ROIs on the SD composition of
    their events (#156): k-means (k = 3) on each source's fraction of events
    with raw amplitude < 2 SD, 2-4 SD and > 4 SD (standardised). Clusters are
    named Low / Intermediate / High SNR by their centroid's > 4 SD fraction, so
    the labels are stable across runs and sessions.

    Sources with no measurable baseline noise (rectified traces) have no
    meaningful SD-based amplitude; they are reported as
    "Excluded (no baseline noise)" instead of being clustered.
    """
    from scipy.cluster.vq import kmeans2

    df = metrics.copy()
    usable = df.get("qc_flag", pd.Series("ok", index=df.index)) == "ok"
    for col in CLASS_FEATURES:
        usable &= df[col].notna()

    df["quality_class"] = "Excluded (no baseline noise)"
    if usable.sum() < 3:
        return df

    feats = df.loc[usable, CLASS_FEATURES].to_numpy(dtype=float)
    mu, sigma = feats.mean(0), feats.std(0)
    sigma[sigma == 0] = 1.0
    centroids, labels = kmeans2((feats - mu) / sigma, 3, minit="++", seed=seed)
    order = np.argsort(centroids[:, -1])          # ascending > 4 SD fraction
    remap = {int(old): new for new, old in enumerate(order)}
    df.loc[usable, "quality_class"] = [CLASS_NAMES[remap[int(l)]] for l in labels]
    return df


def compute(nwb_path: Path, out_dir: Path) -> None:
    from pynwb import NWBHDF5IO

    out_dir.mkdir(parents=True, exist_ok=True)
    io = NWBHDF5IO(str(nwb_path), "r", load_namespaces=True)
    nwb = io.read()

    layout = resolve_layout(nwb)
    stim = stimulus_table(nwb)
    stim.to_csv(out_dir / "stimulus_contexts.csv", index=False)
    print(f"Layout: {layout['layout']}"
          f"{' (glutamate + calcium)' if layout['has_calcium'] else ' (glutamate only)'}"
          f" · DMDs {layout['dmds']}")
    print(f"Contexts ({stim.attrs.get('context_source', '?')}):")
    print(stim["context"].value_counts().to_string())
    if "standard_orientation" in stim.attrs:
        print(f"standard orientation = {stim.attrs['standard_orientation']:.3f} rad")
    print()

    metric_rows: list[dict] = []
    event_frames: list[pd.DataFrame] = []

    for dmd in layout["dmds"]:
        series = layout["dff_series"][dmd]
        ts = np.asarray(series.timestamps)
        dt = sampling_interval(ts)
        data = np.asarray(series.data, dtype=np.float32)
        n_t, n_roi = data.shape
        print(f"DMD{dmd}: {n_roi} sources, {n_t} samples, {1/dt:.1f} Hz, "
              f"{np.nanmax(ts)-np.nanmin(ts):.0f} s")

        for r in range(n_roi):
            trace = data[:, r]
            res = detect_events(trace, dt)
            idx, amp = drop_untimed_events(res["idx"], res["amp_sd"], ts)
            dur_valid = res["n_valid"] * dt
            n_ev = idx.size

            # 95/50 robust trace SNR, the portable metric proposed in #156.
            # Estimated wholly on the raw dF/F trace: the matched filter has
            # unit energy, so its noise SD is on a different scale and must not
            # be mixed with raw-trace percentiles.
            finite = trace[np.isfinite(trace)]
            if finite.size:
                p95, p50 = np.percentile(finite, [95, 50])
                raw_noise = baseline_noise(finite)[0]
                robust_snr = ((p95 - p50) / raw_noise
                              if raw_noise and np.isfinite(raw_noise) else np.nan)
            else:
                p95 = p50 = raw_noise = robust_snr = np.nan

            if n_ev:
                frac_large = float(np.mean(amp >= SD_LARGE))
                frac_mid = float(np.mean(amp < SD_LARGE))
                med_amp = float(np.median(amp))
                p90_amp = float(np.percentile(amp, 90))
            else:
                frac_large = frac_mid = med_amp = p90_amp = np.nan

            # Amplitudes re-measured on the raw trace, in raw-dF/F sigma, so the
            # bins mean the same thing as the mesoscope's (#156).
            amp_raw = event_amplitudes_raw(trace, idx, dt, raw_noise)
            fin = amp_raw[np.isfinite(amp_raw)]
            if fin.size:
                frac_lt2 = float(np.mean(fin < 2.0))
                frac_24 = float(np.mean((fin >= 2.0) & (fin < SD_LARGE)))
                frac_gt4_raw = float(np.mean(fin >= SD_LARGE))
                med_raw = float(np.median(fin))
            else:
                frac_lt2 = frac_24 = frac_gt4_raw = med_raw = np.nan

            metric_rows.append({
                "dmd": dmd,
                "roi": r,
                "n_events": n_ev,
                "event_rate_hz": n_ev / dur_valid if dur_valid > 0 else np.nan,
                "false_pos_rate_hz": res["n_false_pos"] / dur_valid if dur_valid > 0 else np.nan,
                "false_pos_frac": res["n_false_pos"] / n_ev if n_ev else np.nan,
                "noise_sd_filtered": res["noise_sd"],
                "noise_dff": raw_noise,
                "robust_snr": robust_snr,
                "qc_flag": "ok" if np.isfinite(res["noise_sd"]) else "rectified_trace",
                "median_event_sd": med_amp,
                "p90_event_sd": p90_amp,
                f"frac_events_{int(SD_DETECT)}_4sd_filtered": frac_mid,
                "frac_events_gt4sd_filtered": frac_large,
                "median_event_raw_sd": med_raw,
                "frac_events_lt2sd": frac_lt2,
                "frac_events_2_4sd": frac_24,
                "frac_events_gt4sd": frac_gt4_raw,
            })
            if n_ev:
                event_frames.append(pd.DataFrame({
                    "dmd": dmd, "roi": r, "time": ts[idx], "amp_sd": amp,
                }))
        del data

    metrics = assign_classes(pd.DataFrame(metric_rows))
    events = (pd.concat(event_frames, ignore_index=True) if event_frames
              else pd.DataFrame(columns=["dmd", "roi", "time", "amp_sd"]))
    events["context"] = assign_event_contexts(events["time"].values, stim)

    metrics.to_csv(out_dir / "slap2_event_metrics.csv", index=False)
    events.to_csv(out_dir / "slap2_events.csv", index=False)

    cols = ["event_rate_hz", "false_pos_frac", "robust_snr",
            "median_event_sd", "frac_events_gt4sd"]
    print("\nPer-source metrics (median by DMD):")
    print(metrics.groupby("dmd")[cols].median().round(3).to_string())
    print("\nQuality classes:")
    print(pd.crosstab(metrics["quality_class"], metrics["dmd"]).to_string())
    print(metrics.groupby("quality_class")[cols].median().round(3).to_string())
    print(f"\nWrote {out_dir}/  ({len(metrics)} sources, {len(events)} events)")
    io.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--nwb", required=True, type=Path)
    ap.add_argument("--output", type=Path,
                    default=Path("docs/notebooks/plots_figure7_slap2_glutamate"))
    args = ap.parse_args()
    compute(args.nwb, args.output)


if __name__ == "__main__":
    main()
