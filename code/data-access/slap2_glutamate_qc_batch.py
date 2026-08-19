#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the SLAP2 event-based QC over every session in DANDI 001424.

Downloads one session at a time to a local cache, computes per-synapse metrics
and per-context event rates, then deletes the NWB before moving on — so peak
disk stays around one session (~4 GB) rather than the archive's 43 GB.

The archive ships three NWB layouts and two context conventions; both are
handled by `resolve_layout` / `stimulus_table` in `slap2_glutamate_qc_events`.

Outputs, all keyed by subject and session:

  slap2_metrics_all_sessions.csv        one row per synapse
  slap2_context_rates_all_sessions.csv  one row per synapse x context
  slap2_session_summary.csv             one row per session

Per-event tables are not aggregated — at ~7.9 M events archive-wide that file
would be hundreds of MB, and the panels only need per-context counts.

Quality classes come in two flavours, both kept in the metrics table:

  quality_class_session   k-means fitted within each session (what
                          `slap2_glutamate_qc_events.compute` gives for a single file)
  quality_class           k-means fitted once per acquisition cohort — this is
                          the label the Figure 7 panels use, and the one copied
                          into the context-rate table.

The cohort split is forced by the archive: the 12 glutamate-only sessions ship
two-sided ΔF/F (about a quarter of the samples below zero), while the 8
glutamate + calcium sessions ship non-negative, NMF-denoised traces. The two are
on different noise scales, so one fit over all 20 sessions would mostly sort
synapses by pipeline rather than by signal quality.

Usage:
    python slap2_glutamate_qc_batch.py --output docs/notebooks/plots_figure7_slap2_glutamate \
        [--cache /tmp/slap2_cache] [--limit N] [--keep-downloads]
    python slap2_glutamate_qc_batch.py --output <dir> --refit-only   # classes only, no NWB access
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
import urllib.request
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from slap2_glutamate_qc_events import (  # noqa: E402
    SD_LARGE, assign_classes, assign_event_contexts,
    baseline_noise, detect_events, drop_untimed_events, event_amplitudes_raw,
    resolve_layout, sampling_interval, stimulus_table,
)

DANDISET = "001424"
API = (f"https://api.dandiarchive.org/api/dandisets/{DANDISET}"
       f"/versions/draft/assets/")
UA = {"User-Agent": "Mozilla/5.0"}


def api_get(url: str) -> dict:
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=120).read())


def list_assets() -> list[dict]:
    url, out = API + "?page_size=1000", []
    while url:
        page = api_get(url)
        out += page["results"]
        url = page.get("next")
    return sorted(out, key=lambda a: a["path"])


def fetch(asset: dict, cache: Path) -> Path:
    """Download one asset to the cache, resuming nothing — atomic via .part."""
    dest = cache / Path(asset["path"]).name
    if dest.exists() and dest.stat().st_size == asset["size"]:
        print(f"    cached ({dest.stat().st_size/1e9:.2f} GB)", flush=True)
        return dest
    dl = API + f"{asset['asset_id']}/download/"
    part = dest.with_suffix(dest.suffix + ".part")
    t0 = time.time()
    with urllib.request.urlopen(urllib.request.Request(dl, headers=UA),
                                timeout=300) as r, open(part, "wb") as f:
        shutil.copyfileobj(r, f, length=8 << 20)
    part.rename(dest)
    gb = dest.stat().st_size / 1e9
    print(f"    downloaded {gb:.2f} GB in {time.time()-t0:.0f}s", flush=True)
    return dest


def sample_contexts(ts: np.ndarray, stim: pd.DataFrame) -> pd.Categorical:
    """Stimulus context of every sample of a DMD; NaN timestamps get no label.

    Used to count how long each source actually recorded in each context.
    The two DMDs of a session do not always run for the same time, and both
    carry acquisition gaps, so charging every source with the nominal block
    durations would understate its rates; counting its own valid samples per
    context does not. Samples outside every presentation are "Inter-stimulus"
    (the grey-screen ITIs plus any gaps between blocks).
    """
    ts = np.asarray(ts, dtype=float)
    labels = np.full(ts.size, None, dtype=object)
    ok = np.isfinite(ts)
    labels[ok] = assign_event_contexts(ts[ok], stim)
    return pd.Categorical(labels)


def context_seconds(codes: np.ndarray, categories, valid: np.ndarray, dt: float) -> dict:
    """Seconds per context for one source, from its valid samples."""
    counts = np.bincount(codes[valid & (codes >= 0)], minlength=len(categories))
    return {str(c): float(n * dt) for c, n in zip(categories, counts) if n}


def process(nwb_path: Path, subject: str, session: str):
    """Per-synapse metrics and per-synapse-per-context event rates."""
    from pynwb import NWBHDF5IO

    io = NWBHDF5IO(str(nwb_path), "r", load_namespaces=True)
    try:
        nwb = io.read()
        layout = resolve_layout(nwb)
        stim = stimulus_table(nwb)
        ctx_source = stim.attrs.get("context_source", "?")

        metric_rows, ctx_rows = [], []
        session_dur = np.nan
        for dmd in layout["dmds"]:
            series = layout["dff_series"][dmd]
            ts = np.asarray(series.timestamps)
            dt = sampling_interval(ts)
            data = np.asarray(series.data, dtype=np.float32)
            span = float(np.nanmax(ts) - np.nanmin(ts))
            session_dur = max(session_dur, span) if np.isfinite(session_dur) else span
            ctx_of_sample = sample_contexts(ts, stim)
            ctx_codes, ctx_names = ctx_of_sample.codes, list(ctx_of_sample.categories)

            for r in range(data.shape[1]):
                trace = data[:, r]
                res = detect_events(trace, dt)
                idx, amp = drop_untimed_events(res["idx"], res["amp_sd"], ts)
                dur_valid = res["n_valid"] * dt
                n_ev = idx.size

                finite = trace[np.isfinite(trace)]
                if finite.size:
                    p95, p50 = np.percentile(finite, [95, 50])
                    raw_noise = baseline_noise(finite)[0]
                    robust_snr = ((p95 - p50) / raw_noise
                                  if raw_noise and np.isfinite(raw_noise) else np.nan)
                else:
                    raw_noise = robust_snr = np.nan

                # Amplitudes in raw-dF/F sigma, comparable to the mesoscope's
                # bins; the filtered-sigma values stay for the detection story.
                amp_raw = event_amplitudes_raw(trace, idx, dt, raw_noise)
                fin = amp_raw[np.isfinite(amp_raw)]
                if fin.size:
                    frac_lt2 = float(np.mean(fin < 2.0))
                    frac_24 = float(np.mean((fin >= 2.0) & (fin < SD_LARGE)))
                    frac_gt4 = float(np.mean(fin >= SD_LARGE))
                    med_raw = float(np.median(fin))
                else:
                    frac_lt2 = frac_24 = frac_gt4 = med_raw = np.nan

                metric_rows.append({
                    "subject": subject, "session": session, "layout": layout["layout"],
                    "has_calcium": layout["has_calcium"], "dmd": dmd, "roi": r,
                    "n_events": n_ev,
                    "duration_valid_s": dur_valid,
                    "event_rate_hz": n_ev / dur_valid if dur_valid > 0 else np.nan,
                    "false_pos_frac": res["n_false_pos"] / n_ev if n_ev else np.nan,
                    "noise_dff": raw_noise, "robust_snr": robust_snr,
                    "qc_flag": ("ok" if np.isfinite(res["noise_sd"])
                                else "rectified_trace"),
                    "median_event_sd": float(np.median(amp)) if n_ev else np.nan,
                    "frac_events_gt4sd_filtered": (float(np.mean(amp >= SD_LARGE))
                                                   if n_ev else np.nan),
                    "median_event_raw_sd": med_raw,
                    "frac_events_lt2sd": frac_lt2,
                    "frac_events_2_4sd": frac_24,
                    "frac_events_gt4sd": frac_gt4,
                })

                if n_ev:
                    valid = np.isfinite(trace) & np.isfinite(ts)
                    ctx_dur = context_seconds(ctx_codes, ctx_names, valid, dt)
                    labels = assign_event_contexts(ts[idx], stim)
                    for ctx, cnt in pd.Series(labels).value_counts().items():
                        secs = ctx_dur.get(ctx, np.nan)
                        ctx_rows.append({
                            "subject": subject, "session": session, "dmd": dmd,
                            "roi": r, "context": ctx, "n_events": int(cnt),
                            "seconds": secs,
                            "rate_hz": cnt / secs if secs and secs > 0 else np.nan,
                        })
            del data

        metrics = (assign_classes(pd.DataFrame(metric_rows))
                   .rename(columns={"quality_class": "quality_class_session"}))
        ctx_df = pd.DataFrame(ctx_rows)

        # Session medians are taken over usable sources only; a rectified trace
        # has no defined SNR and would otherwise drag the summary anywhere.
        ok = metrics[metrics.qc_flag == "ok"]
        summary = {
            "subject": subject, "session": session, "layout": layout["layout"],
            "has_calcium": layout["has_calcium"], "context_source": ctx_source,
            "n_sources": len(metrics), "n_rectified": int((metrics.qc_flag != "ok").sum()),
            "duration_s": round(session_dur, 1),
            "n_contexts": stim["context"].nunique(),
            "median_event_rate_hz": round(float(ok.event_rate_hz.median()), 3),
            "median_false_pos_frac": round(float(ok.false_pos_frac.median()), 4),
            "median_robust_snr": round(float(ok.robust_snr.median()), 3),
            "median_frac_gt4sd": round(float(ok.frac_events_gt4sd.median()), 3),
        }
        return metrics, ctx_df, summary
    finally:
        io.close()


def fit_cohort_classes(out_dir: Path) -> pd.DataFrame:
    """Fit quality classes once per acquisition cohort and write them back.

    Reads `slap2_metrics_all_sessions.csv`, runs `assign_classes` separately on
    the glutamate-only and the glutamate + calcium sessions, stores the result
    as `quality_class` (keeping `quality_class_session`), and copies the label
    into `slap2_context_rates_all_sessions.csv`. Safe to re-run; it only
    touches the class columns.
    """
    mpath = out_dir / "slap2_metrics_all_sessions.csv"
    cpath = out_dir / "slap2_context_rates_all_sessions.csv"
    m = pd.read_csv(mpath)
    if "quality_class_session" not in m.columns:      # tables from an older run
        m = m.rename(columns={"quality_class": "quality_class_session"})
    m = m.drop(columns=["quality_class"], errors="ignore")

    parts = []
    for _, grp in m.groupby("has_calcium", sort=True):
        parts.append(assign_classes(grp.reset_index(drop=True)))
    m = pd.concat(parts, ignore_index=True).sort_values(
        ["subject", "session", "dmd", "roi"]).reset_index(drop=True)
    m.to_csv(mpath, index=False)

    if cpath.exists():
        keys = ["subject", "session", "dmd", "roi"]
        ctx = pd.read_csv(cpath).drop(columns=["quality_class"], errors="ignore")
        ctx = ctx.merge(m[keys + ["quality_class"]], on=keys, how="left")
        ctx.sort_values(keys + ["context"]).to_csv(cpath, index=False)

    spath = out_dir / "slap2_session_summary.csv"
    if spath.exists():
        cols = {"Low SNR": "n_low_snr", "Intermediate": "n_intermediate",
                "High SNR": "n_high_snr"}
        counts = (pd.crosstab([m.subject, m.session], m.quality_class)
                    .reindex(columns=list(cols), fill_value=0).rename(columns=cols)
                    .reset_index())
        summ = pd.read_csv(spath).drop(columns=list(cols.values()), errors="ignore")
        summ.merge(counts, on=["subject", "session"], how="left").to_csv(spath, index=False)

    print("\nQuality classes per cohort (k-means within cohort):")
    tab = pd.crosstab(m.has_calcium.map({False: "glutamate only",
                                         True: "glutamate + calcium"}),
                      m.quality_class)
    print(tab.to_string())
    agree = (m.quality_class == m.quality_class_session).mean()
    print(f"{100 * agree:.0f}% of synapses keep their per-session label")
    return m


def write_outputs(args, all_metrics, all_ctx, summaries) -> None:
    """Persist the three aggregate tables, merging by session when asked.

    Merging replaces any rows for the sessions just processed and keeps the
    rest, so a single re-run never duplicates or drops other sessions' rows.
    """
    specs = [
        ("slap2_metrics_all_sessions.csv", all_metrics, ["subject", "session"]),
        ("slap2_context_rates_all_sessions.csv", all_ctx, ["subject", "session"]),
        ("slap2_session_summary.csv",
         [pd.DataFrame(summaries)] if summaries else [], ["subject", "session"]),
    ]
    for fname, frames, keys in specs:
        frames = [f for f in frames if f is not None and not f.empty]
        if not frames:
            continue
        new = pd.concat(frames, ignore_index=True)
        path = args.output / fname
        if args.merge and path.exists():
            old = pd.read_csv(path)
            done = set(map(tuple, new[keys].drop_duplicates().values.tolist()))
            keep = ~old[keys].apply(tuple, axis=1).isin(done)
            new = pd.concat([old[keep], new], ignore_index=True)
        new.sort_values(keys).to_csv(path, index=False)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--cache", type=Path, default=Path("/tmp/slap2_cache"))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--only", default=None,
                    help="process only assets whose path contains this substring")
    ap.add_argument("--merge", action="store_true",
                    help="merge into existing output CSVs instead of replacing "
                         "them (use with --only to re-run a single session)")
    ap.add_argument("--keep-downloads", action="store_true")
    ap.add_argument("--refit-only", action="store_true",
                    help="skip the per-session pass; only refit the cohort "
                         "classes on the existing metrics table")
    args = ap.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    if args.refit_only:
        fit_cohort_classes(args.output)
        return
    args.cache.mkdir(parents=True, exist_ok=True)

    assets = list_assets()
    if args.only:
        assets = [a for a in assets if args.only in a["path"]]
        if not assets:
            raise SystemExit(f"No asset path contains {args.only!r}")
    if args.limit:
        assets = assets[:args.limit]
    print(f"{len(assets)} sessions to process "
          f"({sum(a['size'] for a in assets)/1e9:.1f} GB)\n", flush=True)

    all_metrics, all_ctx, summaries, failures = [], [], [], []
    t_start = time.time()
    for i, a in enumerate(assets, 1):
        name = Path(a["path"]).name.replace("_image+ophys.nwb", "")
        subject = a["path"].split("/")[0].replace("sub-", "")
        print(f"[{i}/{len(assets)}] {name}", flush=True)
        try:
            p = fetch(a, args.cache)
            t0 = time.time()
            m, c, s = process(p, subject, name)
            all_metrics.append(m)
            if not c.empty:
                all_ctx.append(c)
            summaries.append(s)
            print(f"    {s['n_sources']} sources · {s['layout']} · "
                  f"rate {s['median_event_rate_hz']} Hz · "
                  f"FP {100*s['median_false_pos_frac']:.2f}% · "
                  f"{time.time()-t0:.0f}s", flush=True)
            if not args.keep_downloads:
                p.unlink(missing_ok=True)
        except Exception as e:
            print(f"    FAILED {type(e).__name__}: {e}", flush=True)
            failures.append({"session": name, "error": f"{type(e).__name__}: {e}"})

        # Write after every session so a crash never loses completed work.
        write_outputs(args, all_metrics, all_ctx, summaries)

    print(f"\n{'='*70}\nDone in {(time.time()-t_start)/60:.1f} min · "
          f"{len(summaries)} ok · {len(failures)} failed", flush=True)
    if summaries:
        df = pd.DataFrame(summaries)
        print(f"\n{df.n_sources.sum()} synapses across {len(df)} sessions, "
              f"{df.subject.nunique()} mice")
        print(df.to_string(index=False))
    for f in failures:
        print(f"  FAILED {f['session']}: {f['error']}")
    if summaries:
        fit_cohort_classes(args.output)


if __name__ == "__main__":
    main()
