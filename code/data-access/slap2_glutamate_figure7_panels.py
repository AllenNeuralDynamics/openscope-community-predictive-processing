#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render the SLAP2-glutamate column of Figure 7 (panels C, G, K).

Figure 7 of the data-release paper is a 4-column x 3-row grid:

    columns : Neuropixels | Mesoscope | SLAP2 glutamate | SLAP2 voltage
    row 1   : A B C D  example 2D projection, single source, trace + events
    row 2   : E F G H  measure of signal and noise on traces, class definitions
    row 3   : I J K L  distribution of classes across context / neurons

This script renders the SLAP2 *glutamate* column:

  C  one example session — both imaging planes with every extracted synapse,
     one synapse's footprint, and 20 s of its ΔF/F with the detected events;
  G  how signal and noise are measured on a trace (same synapse), the class
     definition by example (one synapse per class), and every synapse of the
     archive in the event-amplitude feature space the classes are fitted on;
  K  event rate by stimulus context per class, and class composition across
     dendritic compartment and across neurons (one neuron per session).

Panel C and the trace in G read one NWB file. Everything else comes from the
archive-wide tables written by `slap2_glutamate_qc_batch.py` (20 sessions, 8 mice), so
G and K re-render in seconds without touching any NWB. Metrics and classes are
those of `slap2_glutamate_qc_events.py`, whose event-amplitude scheme mirrors the
mesoscope QC agreed in discussion #156.

Usage:
    python slap2_glutamate_figure7_panels.py --nwb <example session.nwb> \
        --metrics <dir with slap2_*_all_sessions.csv> --output <dir> \
        [--cache <local dir for the example session's arrays>]
"""

from __future__ import annotations

import argparse
import re
import warnings
from pathlib import Path

import matplotlib as mpl
import numpy as np
import pandas as pd

mpl.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.cm import ScalarMappable  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from slap2_glutamate_qc_events import (  # noqa: E402
    SD_DETECT, SD_LARGE, TAU_IGLUSNFR4F_S,
    baseline_noise, detect_events, event_amplitudes_raw, resolve_layout,
    sampling_interval,
)

warnings.filterwarnings("ignore")

# ───────────────────────── palette & style ─────────────────────────

# Ordinal one-hue ramp for the ordered quality classes (sequential-blue steps
# 250/450/650): monotone lightness, single hue, worst all-pairs CVD dE 19.
# The palest step is below 3:1 on white, so classes are also direct-labelled
# or given a legend with n wherever they appear.
CLASS_COLORS = {"Low SNR": "#86b6ef", "Intermediate": "#2a78d6", "High SNR": "#104281"}
CLASS_ORDER = ["Low SNR", "Intermediate", "High SNR"]

# Neutral greys for the three event-amplitude bins, so the bins never compete
# with the class ramp.
BIN_GREYS = {"lt2": "#c6c5c0", "mid": "#8b8a86", "gt4": "#2e2d2b"}
BIN_LABELS = {"lt2": "< 2 SD", "mid": "2–4 SD", "gt4": "> 4 SD"}

INK, INK_2, MUTED = "#0b0b0b", "#52514e", "#8a8985"
GRID, NOISE_GREY = "#e3e2de", "#b6b5b0"
ORANGE = "#eb6834"      # single accent: the example synapse, nothing else

COMPARTMENT = {1: "DMD1 · proximal dendrites", 2: "DMD2 · apical dendrites"}
COMP_SHORT = {1: "DMD1 · proximal", 2: "DMD2 · apical"}
COHORT = {False: "Glutamate only", True: "Glutamate + calcium"}

# Stimulus contexts of the 12 glutamate-only sessions (standard oddball
# paradigm; labels inferred from orientation statistics) …
CONTEXT_ORDER = ["Control (random ori)", "Oddball standard", "Oddball deviant",
                 "RF mapping", "Blank", "Inter-stimulus"]
CONTEXT_LABELS = {"Control (random ori)": "control\n(random)",
                  "Oddball standard": "oddball\nstandard",
                  "Oddball deviant": "oddball\ndeviant",
                  "RF mapping": "RF\nmapping", "Blank": "blank",
                  "Inter-stimulus": "inter-\nstimulus"}
# … and the named stimulus blocks of the 8 glutamate + calcium sessions,
# grouped by role so the four oddball paradigms sit next to their controls.
CONTEXT_GROUPS = [
    ("standard oddball", "standard\noddball"),
    ("motor oddball", "motor\noddball"),
    ("sequential oddball", "sequential\noddball"),
    ("jitter oddball", "jitter\noddball"),
    ("standard control", "standard\ncontrol"),
    ("sequential control block", "sequential\ncontrol"),
    ("jitter control", "jitter\ncontrol"),
    ("rf mapping", "RF\nmapping"),
    ("movie", "movie"),
    ("open loop prerecorded", "open-loop\nprerec."),
    ("Inter-stimulus", "inter-\nstimulus"),
]


def set_style() -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 7, "axes.labelsize": 7, "axes.titlesize": 7.5,
        "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5,
        "axes.edgecolor": INK_2, "axes.labelcolor": INK, "axes.linewidth": 0.6,
        "xtick.color": INK_2, "ytick.color": INK_2, "text.color": INK,
        "axes.spines.top": False, "axes.spines.right": False,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "grid.color": GRID, "grid.linewidth": 0.5,
        "legend.frameon": False,
        "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    })


def panel_tag(fig, letter: str) -> None:
    fig.text(0.005, 0.995, letter, fontsize=11, fontweight="bold", va="top",
             ha="left", color=INK)


def save_panel(fig, out: Path, name: str) -> None:
    for ext in ("svg", "png"):
        fig.savefig(out / f"{name}.{ext}", dpi=300)
    plt.close(fig)


def hide_frame(ax) -> None:
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)


def class_legend(ax, n: dict | None = None, **kw):
    handles = [Patch(facecolor=CLASS_COLORS[c],
                     label=f"{c} (n={n[c]:,})" if n is not None else c)
               for c in CLASS_ORDER]
    return ax.legend(handles=handles, labelcolor=INK_2, **kw)


# ───────────────────────── session loading ─────────────────────────

def session_id(nwb_path: Path) -> str:
    return nwb_path.name.replace("_image+ophys.nwb", "").replace(".nwb", "")


def session_date(session: str) -> pd.Timestamp:
    """Acquisition date from either session-id convention in DANDI 001424."""
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", session)
    if m:
        return pd.Timestamp(f"{m[1]}-{m[2]}-{m[3]}")
    m = re.search(r"(\d{4})(\d{2})(\d{2})T", session)
    return pd.Timestamp(f"{m[1]}-{m[2]}-{m[3]}") if m else pd.NaT


def mask_outlines(masks: np.ndarray) -> list[np.ndarray]:
    """Binary footprints with NaNs cleared, one per source."""
    return [np.nan_to_num(masks[i], nan=0.0) > 0 for i in range(masks.shape[0])]


def _plane_images(layout, dmd: int):
    """Activity image, mean image and per-source footprints for one plane."""
    activity = layout["image"](dmd, "activity")
    mean_img = layout["image"](dmd, "mean")
    seg = layout["segmentation"](dmd)
    if activity is None or seg is None:
        return None
    if mean_img is None:
        mean_img = activity
    # Older sessions store weighted `pixel_mask`; newer ones store `image_mask`.
    if "image_mask" in seg.colnames:
        outlines = mask_outlines(np.asarray(seg["image_mask"][:]))
    else:
        h, w = activity.shape[:2]
        outlines = []
        for pix in seg["pixel_mask"][:]:
            m = np.zeros((h, w), dtype=bool)
            for entry in pix:
                x, y = int(entry[0]), int(entry[1])
                if 0 <= y < h and 0 <= x < w:
                    m[y, x] = True
            outlines.append(m)
    return activity, mean_img, outlines


def load_session(nwb_path: Path) -> dict:
    """Traces and plane images of one session.

    Returns {"traces": {dmd: {"data", "ts", "dt"}}, "planes": {dmd: (activity,
    mean image, outlines)}}. The NWB layout is resolved, not assumed: DANDI
    001424 ships three of them.
    """
    from pynwb import NWBHDF5IO

    io = NWBHDF5IO(str(nwb_path), "r", load_namespaces=True)
    try:
        nwb = io.read()
        layout = resolve_layout(nwb)
        sess = {"traces": {}, "planes": {}}
        for dmd in layout["dmds"]:
            s = layout["dff_series"][dmd]
            ts = np.asarray(s.timestamps)
            sess["traces"][dmd] = {"data": np.asarray(s.data, dtype=np.float32),
                                   "ts": ts, "dt": sampling_interval(ts)}
            planes = _plane_images(layout, dmd)
            if planes is not None:
                sess["planes"][dmd] = planes
    finally:
        io.close()
    return sess


def load_session_cached(nwb_path: Path, cache: Path | None) -> dict:
    """`load_session`, with the arrays stashed as .npz under `cache`.

    The NWBs live on slow shared storage, and re-reading 2–4 GB for every
    figure iteration costs minutes; the arrays the panels need are a few
    hundred MB and load in a second from local disk.
    """
    f = None if cache is None else cache / (session_id(nwb_path) + ".npz")
    if f is not None and f.exists():
        z = np.load(f, allow_pickle=True)
        sess = {"traces": {}, "planes": {}}
        for d in [int(x) for x in z["dmds"]]:
            sess["traces"][d] = {"data": z[f"data{d}"], "ts": z[f"ts{d}"],
                                 "dt": float(z[f"dt{d}"])}
            if f"activity{d}" in z:
                sess["planes"][d] = (z[f"activity{d}"], z[f"mean{d}"],
                                     list(z[f"outlines{d}"]))
        print(f"loaded session arrays from {f}")
        return sess

    sess = load_session(nwb_path)
    if f is not None:
        f.parent.mkdir(parents=True, exist_ok=True)
        arrays = {"dmds": np.array(sorted(sess["traces"]))}
        for d, tr in sess["traces"].items():
            arrays[f"data{d}"], arrays[f"ts{d}"], arrays[f"dt{d}"] = tr["data"], tr["ts"], tr["dt"]
        for d, (act, mean_img, outs) in sess["planes"].items():
            arrays[f"activity{d}"], arrays[f"mean{d}"] = act, mean_img
            arrays[f"outlines{d}"] = np.stack(outs)
        np.savez(f, **arrays)
        print(f"cached session arrays under {cache}")
    return sess


# ───────────────────────── shared helpers ─────────────────────────

def usable(m: pd.DataFrame) -> pd.DataFrame:
    """Synapses that carry a class (measurable noise floor, ≥ 1 event)."""
    return m[m.quality_class.isin(CLASS_ORDER)]


def example_synapse(metrics: pd.DataFrame, dmd: int = 1) -> int:
    """The synapse with the largest > 4 SD event fraction on `dmd`."""
    md = usable(metrics[metrics.dmd == dmd])
    return int(md.sort_values("frac_events_gt4sd", ascending=False).iloc[0]["roi"])


def class_examples(metrics: pd.DataFrame) -> dict[str, tuple[int, int]]:
    """One representative (dmd, roi) per class: nearest to the class median."""
    m = usable(metrics).dropna(subset=["frac_events_lt2sd", "frac_events_gt4sd"])
    feats = m[["frac_events_lt2sd", "frac_events_gt4sd"]].to_numpy()
    sd = feats.std(0); sd[sd == 0] = 1
    out = {}
    for cls in CLASS_ORDER:
        sel = (m.quality_class == cls).to_numpy()
        if not sel.any():
            continue
        centre = np.median(feats[sel], axis=0)
        d = (((feats - centre) / sd) ** 2).sum(1)
        d[~sel] = np.inf
        row = m.iloc[int(np.argmin(d))]
        out[cls] = (int(row.dmd), int(row.roi))
    return out


def event_table(trace: np.ndarray, ts: np.ndarray, dt: float) -> dict:
    """Detection + raw-σ amplitudes for one trace, as the QC pipeline does it."""
    res = detect_events(trace, dt)
    finite = trace[np.isfinite(trace)]
    raw_sd, raw_med = baseline_noise(finite)
    amp_raw = event_amplitudes_raw(trace, res["idx"], dt, raw_sd)
    return {**res, "amp_raw": amp_raw, "raw_sd": raw_sd, "raw_med": raw_med,
            "t": ts[res["idx"]]}


def amplitude_bin(amp: np.ndarray) -> np.ndarray:
    return np.where(amp < 2.0, "lt2", np.where(amp < SD_LARGE, "mid", "gt4"))


def pick_window(ev: dict, ts: np.ndarray, width: float, t_from: float = 900.0,
                step: float = 1.0, n_min: int = 6) -> float:
    """Start time of a window that holds ≥ n_min events spanning all three bins.

    Scans forward from `t_from` so the example is a typical stretch mid-session
    rather than a cherry-picked burst.
    """
    t, amp = ev["t"], ev["amp_raw"]
    ok = np.isfinite(amp)
    t, b = t[ok], amplitude_bin(amp[ok])
    t0 = float(np.nanmin(ts)) + t_from
    for start in np.arange(t0, float(np.nanmax(ts)) - width, step):
        m = (t >= start) & (t < start + width)
        if m.sum() >= n_min and len(set(b[m])) == 3:
            return float(start)
    return t0


def stacked_composition(ax, table: pd.DataFrame, labels, fontsize=6, min_label=7.0,
                        thickness=0.55) -> None:
    """Horizontal 100 % stacked class composition, one bar per row of `table` (%)."""
    base = np.zeros(len(table))
    pos = np.arange(len(table))
    for cls in CLASS_ORDER:
        vals = table[cls].values
        ax.barh(pos, vals, left=base, height=thickness, color=CLASS_COLORS[cls],
                edgecolor="white", linewidth=1.0, label=cls)
        for p, (v, b) in enumerate(zip(vals, base)):
            if v > min_label:
                ax.text(b + v / 2, p, f"{v:.0f}", ha="center", va="center", fontsize=fontsize,
                        color="white" if cls != "Low SNR" else INK)
        base += vals
    ax.set_yticks(pos); ax.set_yticklabels(labels)
    ax.set_xlim(0, 100); ax.set_xlabel("% of synapses")
    ax.grid(axis="x", alpha=0.7)
    ax.set_axisbelow(True)


# ─────────────────── optional continuous colour ───────────────────

# `--color-by` swaps the three-class palette of panels C and G for a
# continuous scale on one per-synapse number. The default stays the classes:
# panel K stacks and groups by them, and the 3-class scheme is what keeps this
# column comparable to the mesoscope column (#156). `robust_snr` is offered
# because it is the obvious "SNR", but it is a poor gradient — its class
# medians (2.32 / 2.65 / 2.70 archive-wide) overlap almost completely, and
# every synapse above 10 is in the glutamate + calcium cohort, whose
# non-negative dF/F shrinks sigma. `median_event_raw_sd` is the default: same
# unit as the rest of panel G, and spearman 0.99 with the > 4 SD fraction the
# classes are ordered by.
GRADIENT_CMAP = plt.get_cmap("viridis")
GRADIENT_HALO = "#111111"
GRADIENT_LABELS = {
    "median_event_raw_sd": "median event amplitude (SD of noise)",
    "robust_snr": "95/50 SNR  (P95 − P50) / σ",
    "frac_events_gt4sd": "% of the synapse's events > 4 SD",
}


def gradient_values(m: pd.DataFrame, col: str) -> pd.Series:
    """Per-synapse values in the unit the colourbar is labelled with."""
    v = pd.to_numeric(m[col], errors="coerce")
    return 100 * v if col.startswith("frac_") else v


def gradient_norm(m: pd.DataFrame, col: str) -> Normalize:
    """2–98th percentile scale; the colourbar is drawn with both extends."""
    v = gradient_values(m, col).to_numpy(dtype=float)
    return Normalize(*np.percentile(v[np.isfinite(v)], [2, 98]))


def gradient_colorbar(fig, rect, norm, label: str, orientation: str = "horizontal"):
    """Colourbar at `rect` (figure coordinates), labelled in real units."""
    cax = fig.add_axes(rect)
    cb = fig.colorbar(ScalarMappable(norm=norm, cmap=GRADIENT_CMAP), cax=cax,
                      orientation=orientation, extend="both")
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=6, color=INK_2, labelcolor=INK_2, width=0.5, length=2.0)
    if orientation == "horizontal":
        cax.set_title(label, fontsize=6.3, color=INK, loc="right", pad=3)
    else:
        cb.set_label(label, fontsize=6.3, color=INK)
    return cb


def gradient_suffix(color_by: str | None) -> str:
    """Gradient variants are written next to the default panels, not over them."""
    return "" if color_by is None else "_gradient"


# ───────────────────────── panel C ─────────────────────────

def coverage_bbox(outlines: list[np.ndarray], pad: int = 12) -> tuple[int, int, int, int]:
    """Bounding box of imaged pixels. SLAP2 samples only selected pixels of
    the field, so the stored frame is mostly empty; panels crop to the data."""
    any_mask = np.zeros_like(outlines[0], dtype=bool)
    for ol in outlines:
        any_mask |= ol
    ys, xs = np.where(any_mask)
    h, w = any_mask.shape
    return (max(0, ys.min() - pad), min(h, ys.max() + pad + 1),
            max(0, xs.min() - pad), min(w, xs.max() + pad + 1))


def imaged_segments(activity: np.ndarray, outlines: list[np.ndarray]) -> list[dict]:
    """Connected islands of imaged pixels, each with its synapse count.

    SLAP2 images only user-selected regions, so a plane is a set of disjoint
    islands. Islands without a synapse (small targeting stubs) are dropped.
    """
    from scipy import ndimage

    imaged = np.isfinite(activity) & (activity != 0)
    labels, n = ndimage.label(imaged)
    segs = []
    for i in range(1, n + 1):
        region = labels == i
        n_syn = sum(bool(ol[region].any()) for ol in outlines)
        if n_syn < 1:
            continue
        ys, xs = np.where(region)
        segs.append({"n_synapses": n_syn, "bbox": (ys.min(), ys.max(), xs.min(), xs.max())})
    segs.sort(key=lambda s: s["bbox"][2])  # left to right
    return segs


def render_panel_c(sess: dict, metrics: pd.DataFrame, out: Path, dmd: int = 1,
                   color_by: str | None = None) -> int:
    """Both imaging planes, one example synapse footprint, and its trace + events.

    Both DMDs are drawn: recording proximal and apical dendrites of the same
    neuron simultaneously is the defining feature of the SLAP2 prep, and the
    compartments are what panel K compares.
    """
    planes = sess["planes"]
    if dmd not in planes:
        raise RuntimeError(f"DMD{dmd} is missing its activity image or segmentation.")
    _, mean_img, outlines = planes[dmd]
    ex = example_synapse(metrics, dmd)
    norm = None if color_by is None else gradient_norm(usable(metrics), color_by)

    tr = sess["traces"][dmd]
    trace, ts = tr["data"][:, ex], tr["ts"]
    ev = event_table(trace, ts, tr["dt"])

    # Geometry is explicit: microscopy axes keep equal aspect, so each plane's
    # box is sized from its own crop and the figure grows to fit both.
    fig_w = 7.2
    left, right = 0.065, 0.985
    TOP_IN, GAP_IN, ROW2_IN, BOT_IN, PLANE_GAP_IN = 0.42, 0.66, 1.30, 0.52, 0.46
    if color_by is not None:
        TOP_IN = 0.95            # headroom for the colourbar that replaces the legend
    avail_in = (right - left) * fig_w

    crops = {}
    for d, (act, _, outs) in planes.items():
        by0, by1, bx0, bx1 = coverage_bbox(outs)
        aspect = (bx1 - bx0) / (by1 - by0)
        w_in, h_in = avail_in, avail_in / aspect
        if h_in > 2.9:                      # keep one plane from dominating
            h_in, w_in = 2.9, 2.9 * aspect
        crops[d] = {"box": (by0, by1, bx0, bx1), "w": w_in, "h": h_in}

    order = sorted(crops)
    img_total = sum(crops[d]["h"] for d in order) + PLANE_GAP_IN * (len(order) - 1)
    fig_h = TOP_IN + img_total + GAP_IN + ROW2_IN + BOT_IN
    bottom = BOT_IN / fig_h
    fig = plt.figure(figsize=(fig_w, fig_h))

    # C-i: one activity image per plane, footprints coloured by quality class.
    y_cursor = 1 - TOP_IN / fig_h
    for k, d in enumerate(order):
        act, _, outs = planes[d]
        by0, by1, bx0, bx1 = crops[d]["box"]
        w_in, h_in = crops[d]["w"], crops[d]["h"]
        h_frac = h_in / fig_h
        x_left = left + (avail_in - w_in) / 2 / fig_w
        ax = fig.add_axes([x_left, y_cursor - h_frac, w_in / fig_w, h_frac])
        crop = act[by0:by1, bx0:bx1]
        ax.imshow(crop, cmap="gray", vmin=np.nanpercentile(crop, 2),
                  vmax=np.nanpercentile(crop, 99.5), interpolation="nearest",
                  aspect="equal")
        md = metrics[metrics.dmd == d].set_index("roi")
        vals = (None if color_by is None
                else gradient_values(md[md.quality_class.isin(CLASS_ORDER)], color_by))
        for i, ol in enumerate(outs):
            if not ol.any():
                continue
            crop_ol = ol[by0:by1, bx0:bx1]
            if color_by is None:
                colour = CLASS_COLORS.get(md.quality_class.get(i, ""), MUTED)
            else:
                v = vals.get(i, np.nan)
                colour = GRADIENT_CMAP(norm(v)) if np.isfinite(v) else MUTED
                # A dark stroke underneath keeps both ends of the ramp legible:
                # ROIs sit on bright puncta, the gaps between them are black.
                ax.contour(crop_ol, levels=[0.5], colors=[GRADIENT_HALO],
                           linewidths=1.2, alpha=0.55)
            ax.contour(crop_ol, levels=[0.5], colors=[colour], linewidths=0.55)
        if d == dmd:
            cy, cx = np.argwhere(outlines[ex]).mean(0)
            ax.plot(cx - bx0, cy - by0, marker="o", ms=9, mfc="none", mec=ORANGE, mew=1.0)
        # Outline each imaged island so a segment sitting alone at the edge
        # reads as part of this plane, and so SLAP2's sparse, non-contiguous
        # sampling is visible as a feature.
        segs = imaged_segments(act, outs)
        for sg in segs:
            sy0, sy1, sx0, sx1 = sg["bbox"]
            pad = 3
            ax.add_patch(mpl.patches.Rectangle(
                (sx0 - bx0 - pad, sy0 - by0 - pad), (sx1 - sx0) + 2 * pad, (sy1 - sy0) + 2 * pad,
                fill=False, edgecolor=MUTED, linewidth=0.5, linestyle=(0, (2, 2))))
            ax.text(sx0 - bx0 - pad, sy0 - by0 - pad - 2, f"{sg['n_synapses']}",
                    fontsize=5, color=MUTED, ha="left", va="bottom")
        n_cls = {c: int((md.quality_class == c).sum()) for c in CLASS_ORDER}
        ax.set_title(f"{COMPARTMENT[d]} — {len(outs)} synapses across {len(segs)} imaged "
                     f"segment{'s' if len(segs) != 1 else ''} (dashed)",
                     loc="left", color=INK, pad=6 if k else 14)
        hide_frame(ax)
        if k == 0 and color_by is None:
            handles = [Line2D([], [], color=CLASS_COLORS[c], lw=1.6, label=c) for c in CLASS_ORDER]
            ax.legend(handles=handles, loc="lower right", ncol=3, handlelength=1.2,
                      labelcolor=INK_2, bbox_to_anchor=(1.0, 1.005), columnspacing=1.2)
        y_cursor -= h_frac + PLANE_GAP_IN / fig_h

    if color_by is not None:
        cb_w_in = 1.35
        gradient_colorbar(fig, [right - cb_w_in / fig_w, 1 - 0.36 / fig_h,
                                cb_w_in / fig_w, 0.075 / fig_h], norm,
                          GRADIENT_LABELS[color_by])
        fig.text(right, 1 - 0.62 / fig_h, "colour scale: 2–98th percentile of this session",
                 ha="right", va="top", fontsize=5.4, color=MUTED)

    row2_h = ROW2_IN / fig_h
    trace_w = 0.655
    zoom_left = left + trace_w + 0.055

    # C-ii: zoom on the example synapse footprint over the mean image.
    ax = fig.add_axes([zoom_left, bottom, right - zoom_left, row2_h])
    ys, xs = np.argwhere(outlines[ex]).T
    pad = 14
    zy0, zy1 = max(0, ys.min() - pad), min(mean_img.shape[0], ys.max() + pad + 1)
    zx0, zx1 = max(0, xs.min() - pad), min(mean_img.shape[1], xs.max() + pad + 1)
    sub = mean_img[zy0:zy1, zx0:zx1]
    ax.imshow(sub, cmap="gray", vmin=np.nanpercentile(sub, 2),
              vmax=np.nanpercentile(sub, 99.5), interpolation="nearest")
    ax.contour(outlines[ex][zy0:zy1, zx0:zx1], levels=[0.5], colors=[ORANGE], linewidths=1.2)
    if color_by is None:
        ax.set_title(f"Synapse {ex} footprint\n(mean image)", loc="left", color=INK)
    else:
        v = gradient_values(metrics[(metrics.dmd == dmd) & (metrics.roi == ex)],
                            color_by).iloc[0]
        ax.set_title(f"Synapse {ex} footprint (mean image)\n"
                     f"{GRADIENT_LABELS[color_by].split(' (')[0]} {v:.1f}",
                     loc="left", color=INK)
    hide_frame(ax)

    # C-iii: 20 s of ΔF/F for that synapse with detected events.
    ax = fig.add_axes([left, bottom, trace_w, row2_h])
    t_start = float(np.nanmin(ts)) + 900.0
    win = (ts >= t_start) & (ts < t_start + 20.0)
    tt, yy = ts[win] - t_start, trace[win]
    ax.plot(tt, yy, lw=0.5, color=INK_2)
    in_win = (ev["t"] >= t_start) & (ev["t"] < t_start + 20.0)
    lo, hi = np.nanmin(yy), np.nanmax(yy)
    span = hi - lo
    ax.set_ylim(lo - 0.05 * span, hi + 0.28 * span)       # headroom for the ticks
    ax.scatter(ev["t"][in_win] - t_start, np.full(in_win.sum(), hi + 0.14 * span),
               marker="v", s=8, color=ORANGE, linewidths=0,
               label=f"detected event (> {SD_DETECT:.0f} SD)")
    ax.set_xlabel("time (s, from 900 s into the session)")
    ax.set_ylabel("ΔF/F")
    rate = ev["idx"].size / (np.nanmax(ts) - np.nanmin(ts))
    ax.set_title(f"Synapse {ex} — {in_win.sum()} events in 20 s "
                 f"({rate:.2f} Hz over the session)", loc="left", color=INK, pad=12)
    ax.legend(loc="lower right", labelcolor=INK_2, handletextpad=0.3,
              bbox_to_anchor=(1.0, 1.002))
    ax.grid(axis="y", alpha=0.7)
    ax.set_axisbelow(True)

    panel_tag(fig, "C")
    save_panel(fig, out, "figure7_panelC_slap2_glutamate" + gradient_suffix(color_by))
    print(f"panel C  → example synapse {ex} (DMD{dmd}), {ev['idx'].size} events, "
          f"class {metrics[(metrics.dmd == dmd) & (metrics.roi == ex)].quality_class.iloc[0]}")
    return ex


# ───────────────────────── panel G ─────────────────────────

def _draw_measurement(ax_z, ax_raw, sess, dmd: int, roi: int, width: float = 5.0) -> float:
    """G-i: detection on the matched-filtered trace, amplitude on the raw trace."""
    tr = sess["traces"][dmd]
    trace, ts, dt = tr["data"][:, roi], tr["ts"], tr["dt"]
    ev = event_table(trace, ts, dt)
    t0 = pick_window(ev, ts, width)
    win = (ts >= t0) & (ts < t0 + width)
    tt = ts[win] - t0
    in_win = (ev["t"] >= t0) & (ev["t"] < t0 + width)
    t_ev, i_ev = ev["t"][in_win] - t0, ev["idx"][in_win]
    amp_raw = ev["amp_raw"][in_win]
    bins = amplitude_bin(amp_raw)

    # (a) detection: matched-filtered trace in units of its own noise SD.
    z = ev["z"]
    ax_z.axhspan(-SD_DETECT, SD_DETECT, color=NOISE_GREY, alpha=0.25, lw=0)
    ax_z.axhline(SD_DETECT, color=INK_2, lw=0.6, ls="--")
    ax_z.plot(tt, z[win], lw=0.55, color=INK_2)
    ax_z.scatter(t_ev, z[i_ev], s=9, color=INK, zorder=5, linewidths=0)
    ax_z.text(1.004, SD_DETECT, f"{SD_DETECT:.0f} SD", transform=ax_z.get_yaxis_transform(),
              fontsize=5.8, color=INK_2, va="center", ha="left")
    ax_z.text(0.01, 0.96, "① detect — local maxima of the matched-filtered ΔF/F above "
              f"{SD_DETECT:.0f} SD of its noise (SD from the below-median half, "
              "which release cannot reach)", transform=ax_z.transAxes, fontsize=6,
              color=INK, va="top", ha="left")
    ax_z.set_ylabel("filtered ΔF/F\n(noise SD)")
    ax_z.set_ylim(min(-3.5, np.nanmin(z[win]) - 0.5), np.nanmax(z[win]) * 1.35)
    ax_z.tick_params(labelbottom=False)
    ax_z.grid(axis="y", alpha=0.7)
    ax_z.set_axisbelow(True)

    # (b) amplitude: peak − local baseline on the raw ΔF/F, in raw-noise SDs.
    raw = trace
    ax_raw.plot(tt, raw[win], lw=0.55, color=INK_2, zorder=2)
    sd, med = ev["raw_sd"], ev["raw_med"]
    for level, lab in ((2.0, "+2 SD"), (SD_LARGE, f"+{SD_LARGE:.0f} SD")):
        ax_raw.axhline(med + level * sd, color=MUTED, lw=0.5, ls=":")
        ax_raw.text(1.004, med + level * sd, lab, transform=ax_raw.get_yaxis_transform(),
                    fontsize=5.8, color=INK_2, va="center", ha="left")
    pre_a, pre_b = int(round(3 * TAU_IGLUSNFR4F_S / dt)), int(round(TAU_IGLUSNFR4F_S / dt))
    post = max(1, int(round(2 * TAU_IGLUSNFR4F_S / dt)))
    dx, tick = 0.028, 0.012       # bracket sits just right of the peak
    for i, b in zip(i_ev, bins):
        base = np.nanmedian(raw[max(0, i - pre_a):max(1, i - pre_b)])
        seg = raw[i:i + post + 1]
        k = int(np.nanargmax(seg))
        t_pk, pk = ts[i + k] - t0 + dx, seg[k]
        ax_raw.plot([t_pk, t_pk], [base, pk], color=BIN_GREYS[b], lw=1.3,
                    solid_capstyle="butt", zorder=3)
        for y in (base, pk):
            ax_raw.plot([t_pk - tick, t_pk + tick], [y, y], color=BIN_GREYS[b], lw=1.0,
                        solid_capstyle="butt", zorder=3)
    ax_raw.text(0.01, 0.96, "② measure — amplitude = peak − local baseline on the raw "
                "ΔF/F (brackets), in SD of the raw-trace noise", transform=ax_raw.transAxes,
                fontsize=6, color=INK, va="top", ha="left")
    handles = [Line2D([], [], color=BIN_GREYS[b], lw=2.2, label=BIN_LABELS[b])
               for b in ("lt2", "mid", "gt4")]
    ax_raw.legend(handles=handles, loc="upper right", ncol=3, labelcolor=INK_2,
                  handlelength=1.0, columnspacing=1.0, handletextpad=0.4,
                  borderaxespad=0.2, bbox_to_anchor=(1.0, 0.88), fontsize=6)
    lo, hi = np.nanmin(raw[win]), np.nanmax(raw[win])
    ax_raw.set_ylim(lo - 0.08 * (hi - lo), hi + 0.45 * (hi - lo))
    ax_raw.set_ylabel("ΔF/F")
    ax_raw.set_xlabel(f"time (s, from {t0 - np.nanmin(ts):.0f} s into the session)")
    ax_raw.grid(axis="y", alpha=0.7)
    ax_raw.set_axisbelow(True)
    return t0


def _draw_class_examples(axes, sess, metrics: pd.DataFrame, examples: dict,
                         color_by: str | None = None, norm=None) -> None:
    """G-ii: the event-amplitude histogram of one synapse per class."""
    lo_edge, hi_edge = -2.0, 14.0
    bins = np.arange(lo_edge, hi_edge + 0.01, 0.25)
    for k, cls in enumerate(reversed(CLASS_ORDER)):          # High on top
        ax = axes[k]
        if cls not in examples:
            ax.set_axis_off(); continue
        d, r = examples[cls]
        tr = sess["traces"][d]
        ev = event_table(tr["data"][:, r], tr["ts"], tr["dt"])
        amps = ev["amp_raw"][np.isfinite(ev["amp_raw"])]
        if color_by is None:
            colour, title = CLASS_COLORS[cls], f"{cls} — synapse {r}, DMD{d}"
        else:
            v = gradient_values(metrics[(metrics.dmd == d) & (metrics.roi == r)],
                                color_by).iloc[0]
            colour, title = GRADIENT_CMAP(norm(v)), f"synapse {r}, DMD{d} — {v:.1f}"
        ax.axvspan(lo_edge, 2, color=BIN_GREYS["lt2"], alpha=0.45, lw=0)
        ax.axvspan(2, SD_LARGE, color=BIN_GREYS["mid"], alpha=0.30, lw=0)
        ax.axvspan(SD_LARGE, hi_edge, color=BIN_GREYS["gt4"], alpha=0.18, lw=0)
        counts, _, _ = ax.hist(np.clip(amps, lo_edge, hi_edge - 1e-6), bins=bins,
                               color=colour, edgecolor="white", linewidth=0.3)
        ax.set_ylim(0, 1.55 * counts.max())
        f = [(amps < 2).mean(), ((amps >= 2) & (amps < SD_LARGE)).mean(), (amps >= SD_LARGE).mean()]
        for x, frac, b in zip((0.0, 3.0, 9.0), f, ("lt2", "mid", "gt4")):
            txt = f"{BIN_LABELS[b]}\n{100 * frac:.0f} %" if k == 0 else f"{100 * frac:.0f} %"
            ax.text(x, 0.95, txt, transform=ax.get_xaxis_transform(), ha="center",
                    va="top", fontsize=6, color=INK, linespacing=1.3)
        ax.set_xlim(lo_edge, hi_edge)
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.set_title(title, loc="left", color=INK, fontsize=6.2, pad=3)
        ax.text(0.985, 0.5, f"{amps.size:,}\nevents", transform=ax.transAxes, ha="right",
                va="center", fontsize=5.6, color=INK_2, linespacing=1.3)
        ax.set_xticks([0, 2, 4, 8, 12])
        if k == 2:
            ax.set_xlabel("event amplitude (SD of raw ΔF/F noise)")
        else:
            ax.tick_params(labelbottom=False)


def _draw_feature_space(ax, m: pd.DataFrame, title: str, rings: pd.DataFrame | None,
                        xlim, ylim, legend_loc="upper right",
                        color_by: str | None = None, norm=None) -> None:
    """G-iii: every synapse of one cohort in the (<2 SD %, >4 SD %) plane."""
    n = {c: int((m.quality_class == c).sum()) for c in CLASS_ORDER}
    if color_by is None:
        for cls in CLASS_ORDER:
            sel = m[m.quality_class == cls]
            ax.scatter(100 * sel.frac_events_lt2sd, 100 * sel.frac_events_gt4sd, s=4,
                       alpha=0.6, color=CLASS_COLORS[cls], linewidths=0, rasterized=True)
    else:
        ax.scatter(100 * m.frac_events_lt2sd, 100 * m.frac_events_gt4sd, s=4, alpha=0.75,
                   c=gradient_values(m, color_by), cmap=GRADIENT_CMAP, norm=norm,
                   linewidths=0, rasterized=True)
    if rings is not None:
        ax.scatter(100 * rings.frac_events_lt2sd, 100 * rings.frac_events_gt4sd, s=48,
                   facecolors="none", edgecolors=ORANGE, linewidths=1.1, zorder=6)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_xlabel("% of the synapse's events < 2 SD")
    ax.set_title(title, loc="left", color=INK, fontsize=6.8)
    if color_by is None:
        class_legend(ax, n, loc=legend_loc, handlelength=0.9, handleheight=0.9,
                     handletextpad=0.4, borderpad=0.25, labelspacing=0.3, fontsize=6)
    ax.grid(alpha=0.7)
    ax.set_axisbelow(True)


def render_panel_g(sess: dict, m_ex: pd.DataFrame, m_all: pd.DataFrame,
                   summary: pd.DataFrame, out: Path, dmd: int = 1,
                   color_by: str | None = None) -> None:
    """Signal/noise measurement on a trace, and the class definition."""
    roi = example_synapse(m_ex, dmd)
    examples = class_examples(m_ex)
    norm = None if color_by is None else gradient_norm(usable(m_all), color_by)

    fig = plt.figure(figsize=(7.2, 5.3))
    outer = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.3], hspace=0.42, left=0.075,
                             right=0.965 if color_by is None else 0.915,
                             top=0.93, bottom=0.09)
    top = outer[0].subgridspec(2, 1, hspace=0.12, height_ratios=[1.0, 1.15])
    ax_z = fig.add_subplot(top[0])
    ax_raw = fig.add_subplot(top[1], sharex=ax_z)
    t0 = _draw_measurement(ax_z, ax_raw, sess, dmd, roi)
    ax_z.set_title(f"Measuring signal and noise on a trace — synapse {roi}, "
                   f"{COMPARTMENT[dmd]}", loc="left", color=INK, pad=5)

    bot = outer[1].subgridspec(1, 3, width_ratios=[1.18, 1.0, 1.0], wspace=0.26)
    hist_gs = bot[0].subgridspec(3, 1, hspace=0.55)
    hist_axes = [fig.add_subplot(hist_gs[i]) for i in range(3)]
    _draw_class_examples(hist_axes, sess, m_ex, examples, color_by, norm)

    # Feature space, one axis per acquisition cohort (the cohorts were
    # packaged by different extraction pipelines and classes are fitted within
    # each; see slap2_glutamate_qc_batch.fit_cohort_classes).
    m = usable(m_all)
    xlim = (0, np.ceil(100 * m.frac_events_lt2sd.max() / 5) * 5)
    ylim = (np.floor(100 * m.frac_events_gt4sd.min() / 10) * 10, 100)
    axes_fs = [fig.add_subplot(bot[1]), fig.add_subplot(bot[2])]
    for ax, coh in zip(axes_fs, (False, True)):
        mc = m[m.has_calcium.astype(bool) == coh]
        sc = summary[summary.has_calcium.astype(bool) == coh]
        rings = None
        if coh == bool(m_ex.has_calcium.iloc[0]):
            keys = set(examples.values())
            rings = m_ex[[(d, r) in keys for d, r in zip(m_ex.dmd, m_ex.roi)]]
        _draw_feature_space(
            ax, mc, f"{COHORT[coh]}\n{len(sc)} sessions, {sc.subject.nunique()} mice, "
                    f"{len(mc):,} synapses", rings, xlim, ylim,
            legend_loc="lower right" if coh else "upper right",
            color_by=color_by, norm=norm)
    axes_fs[0].set_ylabel("% of the synapse's events > 4 SD")
    axes_fs[1].tick_params(labelleft=False)
    if color_by is None:
        caption = ("k-means (k = 3) on each synapse's (< 2, 2–4, > 4 SD) fractions, fitted "
                   "per acquisition cohort; classes ordered by the > 4 SD fraction.")
    else:
        fig.canvas.draw()
        pos = axes_fs[1].get_position()
        gradient_colorbar(fig, [pos.x1 + 0.016, pos.y0, 0.013, pos.height], norm,
                          GRADIENT_LABELS[color_by], orientation="vertical")
        caption = ("Colour: each synapse's own value on the scale at right — one continuum, "
                   "not three classes.\nThe glutamate + calcium cohort reads warmer because "
                   "its ΔF/F is non-negative (NMF-denoised), which shrinks σ.")
    axes_fs[0].text(0, -0.2, caption + "\nRings: the three example synapses at left.",
                    transform=axes_fs[0].transAxes, fontsize=5.8, color=MUTED, va="top",
                    linespacing=1.4)

    panel_tag(fig, "G")
    save_panel(fig, out, "figure7_panelG_slap2_glutamate" + gradient_suffix(color_by))
    print(f"panel G  → trace window from {t0 - np.nanmin(sess['traces'][dmd]['ts']):.0f} s; "
          f"class examples {examples}")


# ───────────────────────── panel K ─────────────────────────

def _rate_bars(ax, d: pd.DataFrame, contexts: list[tuple[str, str]],
               n_cls: dict) -> None:
    """Grouped bars: mean ± SEM event rate per synapse, by context and class."""
    width = 0.26
    xs = np.arange(len(contexts))
    for k, cls in enumerate(CLASS_ORDER):
        means, errs = [], []
        for c, _ in contexts:
            v = d[(d.context == c) & (d.quality_class == cls)]["rate_hz"].dropna()
            means.append(v.mean() if len(v) else np.nan)
            errs.append(v.std(ddof=1) / np.sqrt(len(v)) if len(v) > 1 else np.nan)
        ax.bar(xs + (k - 1) * width, means, width * 0.92, yerr=errs, capsize=1.3,
               color=CLASS_COLORS[cls], label=f"{cls} (n={n_cls[cls]:,})",
               error_kw={"lw": 0.5, "ecolor": INK_2})
    ax.set_xticks(xs)
    ax.set_xticklabels([lbl for _, lbl in contexts], fontsize=5.6)
    ax.set_xlim(-0.6, len(contexts) - 0.4)
    ax.grid(axis="y", alpha=0.7)
    ax.set_axisbelow(True)


def render_panel_k(m_all: pd.DataFrame, ctx: pd.DataFrame, out: Path) -> None:
    """Classes across stimulus context, dendritic compartment, and neurons."""
    m = usable(m_all)
    # A rate needs a few seconds of recording behind it; a synapse that caught
    # only a sliver of a block is not a rate estimate for that block.
    ctx = ctx[ctx.quality_class.isin(CLASS_ORDER) & (ctx.seconds >= 5.0)]
    dual = set(m.loc[m.has_calcium.astype(bool), "session"])
    glut = set(m.session) - dual

    fig = plt.figure(figsize=(7.2, 5.4))
    outer = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.2], hspace=0.7,
                             left=0.075, right=0.985, top=0.88, bottom=0.15)

    # K-i: event rate by stimulus context, one axis per cohort (their stimulus
    # vocabularies differ: inferred contexts vs. named block tables).
    d_g = ctx[ctx.session.isin(glut)]
    d_d = ctx[ctx.session.isin(dual)]
    ctx_g = [(c, CONTEXT_LABELS[c]) for c in CONTEXT_ORDER if c in set(d_g.context)]
    ctx_d = [(c, lbl) for c, lbl in CONTEXT_GROUPS
             if c in set(d_d.context) and (d_d.context == c).sum() >= 100]
    top = outer[0].subgridspec(1, 2, width_ratios=[len(ctx_g), len(ctx_d)], wspace=0.06)
    ax_g = fig.add_subplot(top[0])
    ax_d = fig.add_subplot(top[1], sharey=ax_g)
    for ax, d, cs, sessions, coh in ((ax_g, d_g, ctx_g, glut, False),
                                     (ax_d, d_d, ctx_d, dual, True)):
        mc = m[m.session.isin(sessions)]
        n_cls = {c: int((mc.quality_class == c).sum()) for c in CLASS_ORDER}
        _rate_bars(ax, d, cs, n_cls)
        ax.set_title(f"{COHORT[coh]} — {len(sessions)} sessions, {mc.subject.nunique()} mice\n"
                     f"Low {n_cls['Low SNR']:,} · Intermediate {n_cls['Intermediate']:,} · "
                     f"High {n_cls['High SNR']:,} synapses",
                     loc="left", color=INK, fontsize=5.9, pad=4)
        if coh:
            ax.tick_params(axis="x", labelsize=5.1)
    ax_g.set_ylabel("event rate per synapse (Hz)\nmean ± SEM over synapses")
    ax_d.tick_params(labelleft=False)
    ax_g.set_ylim(0, ax_g.get_ylim()[1] * 1.08)
    fig.text(0.075, 0.985, "Distribution of classes across stimulus context",
             fontsize=7.5, color=INK, va="top")
    fig.legend(handles=[Patch(facecolor=CLASS_COLORS[c], label=c) for c in CLASS_ORDER],
               loc="upper right", bbox_to_anchor=(0.985, 0.995), ncol=3, labelcolor=INK_2,
               handlelength=0.9, columnspacing=1.2, handletextpad=0.4, borderaxespad=0.0)

    # K-ii: class composition by dendritic compartment, one axis per cohort.
    bot = outer[1].subgridspec(1, 2, width_ratios=[1.0, 2.1], wspace=0.5)
    comp_gs = bot[0].subgridspec(2, 1, hspace=0.9)
    for k, coh in enumerate((False, True)):
        ax = fig.add_subplot(comp_gs[k])
        mc = m[m.has_calcium.astype(bool) == coh]
        rows, labels = [], []
        for d in (2, 1):                        # DMD1 ends up on top
            sel = mc[mc.dmd == d]
            rows.append(sel.quality_class.value_counts(normalize=True)
                        .reindex(CLASS_ORDER, fill_value=0.0) * 100)
            labels.append(f"{COMP_SHORT[d]}\nn={len(sel):,}")
        stacked_composition(ax, pd.DataFrame(rows).reset_index(drop=True), labels,
                            fontsize=5.8, thickness=0.6)
        ax.tick_params(axis="y", labelsize=5.8)
        ax.set_title(("Classes across dendritic compartment\n" if k == 0 else "")
                     + COHORT[coh], loc="left", color=INK, fontsize=6.8 if k == 0 else 6.2,
                     pad=4)
        if k == 0:
            ax.set_xlabel("")

    # K-iii: class composition per neuron (one per session), in acquisition
    # order and grouped by mouse, the two cohorts apart.
    ax = fig.add_subplot(bot[1])
    s = (m.groupby(["subject", "session"])
           .agg(has_calcium=("has_calcium", "first"), n=("roi", "size")).reset_index())
    s["date"] = s.session.map(session_date)
    s["first_date"] = s.groupby("subject").date.transform("min")
    s = s.sort_values(["has_calcium", "first_date", "subject", "date"]).reset_index(drop=True)
    # Leave one empty slot between the cohorts.
    s["x"] = np.arange(len(s)) + s.has_calcium.astype(int)
    rows = []
    for _, row in s.iterrows():
        sel = m[m.session == row.session]
        rows.append(sel.quality_class.value_counts(normalize=True)
                    .reindex(CLASS_ORDER, fill_value=0.0) * 100)
    tab = pd.DataFrame(rows).reset_index(drop=True)
    base = np.zeros(len(tab))
    for cls in CLASS_ORDER:
        vals = tab[cls].values
        ax.bar(s.x, vals, bottom=base, width=0.72, color=CLASS_COLORS[cls],
               edgecolor="white", linewidth=0.8)
        for x, v, b in zip(s.x, vals, base):
            if v > 12:
                ax.text(x, b + v / 2, f"{v:.0f}", ha="center", va="center", fontsize=5,
                        color="white" if cls != "Low SNR" else INK)
        base += vals
    # Mouse bands and labels (single-session mice sit side by side, so their
    # labels are staggered), cohort labels above.
    for k, (subj, grp) in enumerate(s.groupby("subject", sort=False)):
        a, b = grp.x.min(), grp.x.max()
        if k % 2 == 0:
            ax.axvspan(a - 0.5, b + 0.5, color=GRID, alpha=0.55, lw=0, zorder=0)
        ax.text((a + b) / 2, 101.5 + (6.5 if (k % 2 and b == a) else 0.0), str(subj),
                ha="center", va="bottom", fontsize=5.2, color=MUTED)
    for coh in (False, True):
        grp = s[s.has_calcium.astype(bool) == coh]
        ax.text((grp.x.min() + grp.x.max()) / 2, 114, COHORT[coh], ha="center",
                va="bottom", fontsize=6.2, color=INK_2)
    ax.set_xticks(s.x)
    ax.set_xticklabels([d.strftime("%Y-%m-%d") for d in s.date], rotation=60, ha="right",
                       fontsize=5.2)
    ax.set_xlim(-0.6, s.x.max() + 0.6)
    ax.set_ylim(0, 100)
    ax.set_ylabel("% of synapses")
    ax.set_title("Classes across neurons — one neuron per session, by mouse and date",
                 loc="left", color=INK, fontsize=6.8, pad=27)
    ax.grid(axis="y", alpha=0.7)
    ax.set_axisbelow(True)
    fig.text(0.075, 0.012, "Classes are fitted per acquisition cohort: the two cohorts were "
             "packaged by different extraction pipelines (glutamate + calcium ΔF/F is "
             "non-negative and denoised),\nso the class split is not a prep-quality "
             "comparison between them.", fontsize=5.8, color=MUTED, va="bottom",
             linespacing=1.4)

    panel_tag(fig, "K")
    save_panel(fig, out, "figure7_panelK_slap2_glutamate")

    print("panel K  → event rate (Hz/synapse) by context and class:")
    piv = (ctx.assign(cohort=ctx.session.isin(dual).map({False: "glut", True: "glut+ca"}))
              .pivot_table(index=["cohort", "context"], columns="quality_class",
                           values="rate_hz", aggfunc="mean")
              .reindex(columns=CLASS_ORDER).round(3))
    print(piv.to_string())


# ───────────────────────── main ─────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nwb", required=True, type=Path, help="example session (panel C, G-i/ii)")
    ap.add_argument("--metrics", required=True, type=Path,
                    help="directory holding slap2_metrics_all_sessions.csv, "
                         "slap2_context_rates_all_sessions.csv, slap2_session_summary.csv")
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--cache", type=Path, default=None,
                    help="local directory to cache the example session's arrays (.npz)")
    ap.add_argument("--only", default="CGK", help="subset of panels to render, e.g. GK")
    ap.add_argument("--color-by", default=None, choices=list(GRADIENT_LABELS),
                    help="colour panels C and G by this per-synapse value on a continuous "
                         "scale instead of the three quality classes; writes *_gradient "
                         "files next to the defaults (panel K always uses the classes)")
    args = ap.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    set_style()

    m_all = pd.read_csv(args.metrics / "slap2_metrics_all_sessions.csv")
    ctx_all = pd.read_csv(args.metrics / "slap2_context_rates_all_sessions.csv")
    summary = pd.read_csv(args.metrics / "slap2_session_summary.csv")
    if "quality_class" not in m_all.columns or not m_all.quality_class.isin(CLASS_ORDER).any():
        raise SystemExit("metrics table has no cohort classes — run "
                         "`slap2_glutamate_qc_batch.py --refit-only` first")

    sid = session_id(args.nwb)
    m_ex = m_all[m_all.session == sid].reset_index(drop=True)
    if m_ex.empty:
        raise SystemExit(f"{sid} is not in {args.metrics}/slap2_metrics_all_sessions.csv")
    print(f"example session {sid}: {len(m_ex)} synapses, classes "
          f"{m_ex.quality_class.value_counts().to_dict()}")

    sess = load_session_cached(args.nwb, args.cache) if set("CG") & set(args.only) else None
    if "C" in args.only:
        render_panel_c(sess, m_ex, args.output, color_by=args.color_by)
    if "G" in args.only:
        render_panel_g(sess, m_ex, m_all, summary, args.output, color_by=args.color_by)
    if "K" in args.only:
        render_panel_k(m_all, ctx_all, args.output)
    print(f"\nWrote panels to {args.output}")


if __name__ == "__main__":
    main()
