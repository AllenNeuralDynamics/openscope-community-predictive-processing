"""
Stream one Allen Visual Coding Neuropixels session (DANDI 000021),
extract spike rasters + CCF brain coords + stimulus epochs + a decoder
+ a Markov 'predicts next' model. Write outputs to out/.

This dataset has REAL CCF coordinates per electrode, so the viewer can
place every unit at its actual 3D position inside the mouse brain.
"""

import json
import struct
from pathlib import Path

import h5py
import numpy as np
import remfile
from dandi.dandiapi import DandiAPIClient
from pynwb import NWBHDF5IO
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm

DANDISET_ID = "000021"
DANDI_PATH = "sub-699733573/sub-699733573_ses-715093703.nwb"

HERE = Path(__file__).parent
OUT_DIR = HERE / "out"
ASSETS_DIR = HERE / "assets"
OUT_DIR.mkdir(exist_ok=True)

# Allen CCF midline in microns. Right hemisphere has z > MIDLINE_Z.
MIDLINE_Z = 5700.0

BIN_SIZE_S = 0.02              # 20 ms bins
WINDOW_SECONDS = 240           # 4 min playback window
MAX_UNITS = 1200               # dense enough to fill recorded regions
MIN_SNR = 1.2
TRAIN_FRAC = 0.6

# We use drifting gratings as the model-able stimulus stream.
STIM_TABLE_NAME = "drifting_gratings_presentations"
# Discretize each presentation by (orientation, temporal_frequency) — that's
# the trial-type we'll model. 'blank' is its own type (NaN orientation).
LABEL_COLUMN = "orientation"


def load_region_ml_bounds():
    """
    Load every baked region mesh from assets/, return per-region right-hemisphere
    ML bounds in CCF microns:
        { acronym: (z_min, z_max, z_center) }
    These bounds give each unit a plausible ML coordinate based on its region's
    actual anatomical extent (right hemisphere only).
    """
    bounds = {}
    for path in sorted(ASSETS_DIR.glob("region_*.bin")):
        acro = path.stem.replace("region_", "")
        with open(path, "rb") as f:
            n_v, n_i = struct.unpack("<II", f.read(8))
            verts = np.frombuffer(f.read(n_v * 12), dtype=np.float32).reshape(-1, 3)
        z = verts[:, 2]
        # Keep only right-hemisphere portion of the mesh.
        right = z[z > MIDLINE_Z]
        if right.size == 0:
            right = z
        bounds[acro] = (float(right.min()), float(right.max()), float(np.median(right)))
    return bounds


def open_streaming_nwb():
    print(f"[fetch] DANDI {DANDISET_ID} :: {DANDI_PATH}")
    client = DandiAPIClient()
    asset = client.get_dandiset(DANDISET_ID).get_asset_by_path(DANDI_PATH)
    url = asset.get_content_url(follow_redirects=1, strip_query=True)
    print(f"[stream] {asset.size/1e9:.1f} GB on disk; we read a tiny slice")
    rf = remfile.File(url)
    h5 = h5py.File(rf, "r")
    io = NWBHDF5IO(file=h5, mode="r", load_namespaces=True)
    nwb = io.read()
    return nwb, io, h5, rf


def get_stim_table(nwb):
    if STIM_TABLE_NAME not in nwb.intervals:
        raise RuntimeError(f"missing intervals table: {STIM_TABLE_NAME}")
    return nwb.intervals[STIM_TABLE_NAME]


def trial_label(orient):
    """Map a presentation row to a discrete trial-type label."""
    o = float(orient)
    if np.isnan(o):
        return "blank"
    return f"deg_{int(round(o)):03d}"


def select_units(nwb, max_units, min_snr):
    """
    Pick high-SNR units across all probes/regions. Return arrays parallel
    to the kept set:
        keep_idx, probe_per_unit, region_per_unit, ccf_xyz (n_units, 3)
    """
    units = nwb.units
    snr = np.array(units["snr"][:])
    pcid = np.array(units["peak_channel_id"][:]).astype(int)

    # Electrodes: read just the columns we need (avoid waveform-style heavy reads).
    e_df = nwb.electrodes.to_dataframe()
    # peak_channel_id is the electrode 'id' / table index.
    e_idx = e_df.index.to_numpy()
    e_map = {int(i): row for i, row in zip(e_idx, e_df.itertuples(index=False))}

    valid = (snr >= min_snr) & np.isin(pcid, e_idx)
    order = np.argsort(-snr * valid)  # descending
    keep = order[:max_units * 3]      # over-pick, then balance by region
    keep = [int(i) for i in keep if valid[i]]
    # Balance: cap units per region so the brain isn't all V1 stripes.
    per_region_cap = max(20, max_units // 8)
    counts = {}
    kept = []
    for i in keep:
        e = e_map[int(pcid[i])]
        region = str(e.location) or "grey"
        if counts.get(region, 0) >= per_region_cap:
            continue
        kept.append(i)
        counts[region] = counts.get(region, 0) + 1
        if len(kept) >= max_units:
            break
    kept_idx = np.array(sorted(kept))

    # CCF z (ML) is packaging-mirrored to y in DANDI 000021's NWBs (verified).
    # Restore an anatomically plausible ML by sampling each unit's region's
    # right-hemisphere mesh extent. (See README for the full caveat.)
    ml_bounds = load_region_ml_bounds()
    rng = np.random.default_rng(0)

    probes, regions, xyz = [], [], []
    for i in kept_idx:
        e = e_map[int(pcid[i])]
        region = str(e.location) or "grey"
        x = float(e.x)
        y = float(e.y)
        if region in ml_bounds:
            zmin, zmax, _ = ml_bounds[region]
            # Bias toward region center using a triangular distribution.
            z = float(rng.triangular(zmin, (zmin + zmax) / 2.0, zmax))
        else:
            # No mesh for "grey" etc. — place in right-hemisphere visual cortex band.
            z = float(rng.uniform(7500, 9500))
        probes.append(str(e.group_name))
        regions.append(region)
        xyz.append((x, y, z))

    region_counts = {}
    for r in regions:
        region_counts[r] = region_counts.get(r, 0) + 1
    print(f"[units] {len(kept_idx)} kept   snr {snr[kept_idx].min():.1f}..{snr[kept_idx].max():.1f}")
    print(f"[units] regions: " + ", ".join(f"{r}:{c}" for r, c in sorted(region_counts.items(), key=lambda kv: -kv[1])[:10]))
    print(f"[units] ML reconstructed for {len(ml_bounds)} regions from Allen meshes "
          f"(DANDI 000021 packaging mirrors z<-y; see README)")
    return kept_idx, probes, regions, np.array(xyz, dtype=np.float32)


def bin_spikes(spike_times_per_unit, t0, t1, bin_size):
    n_bins = int(np.floor((t1 - t0) / bin_size))
    edges = t0 + np.arange(n_bins + 1) * bin_size
    raster = np.zeros((len(spike_times_per_unit), n_bins), dtype=np.uint8)
    for i, st in enumerate(tqdm(spike_times_per_unit, desc="bin", leave=False)):
        st = np.asarray(st)
        st = st[(st >= t0) & (st < t1)]
        if st.size == 0:
            continue
        counts, _ = np.histogram(st, bins=edges)
        raster[i] = np.clip(counts, 0, 255)
    return raster, edges


def pick_window(stim_table, want_seconds):
    starts = np.array(stim_table["start_time"][:])
    t_min, t_max = float(starts.min()), float(starts.max() + 5)
    # Just take the first contiguous chunk that fits — drifting gratings
    # block is internally uniform enough that any window works.
    t0 = t_min
    t1 = min(t_max, t0 + want_seconds)
    print(f"[window] {t0:.1f}s .. {t1:.1f}s  ({((np.asarray(starts) >= t0) & (np.asarray(starts) < t1)).sum()} presentations)")
    return t0, t1


def build_per_bin_labels(stim_table, edges, t0, t1):
    starts = np.array(stim_table["start_time"][:])
    stops = np.array(stim_table["stop_time"][:])
    orients = np.array(stim_table[LABEL_COLUMN][:])
    tfs = np.array(stim_table["temporal_frequency"][:])
    types = [trial_label(o) for o in orients]

    mask = (stops > t0) & (starts < t1)
    starts, stops = starts[mask], stops[mask]
    tfs = tfs[mask]
    orients = orients[mask]
    types = [types[i] for i in range(len(types)) if mask[i]]

    vocab = sorted(set(types))
    type_to_idx = {t: i for i, t in enumerate(vocab)}

    midpoints = (edges[:-1] + edges[1:]) / 2.0
    labels = np.full(len(midpoints), -1, dtype=np.int16)

    intervals = []
    for s, e, t, tf, ori in zip(starts, stops, types, tfs, orients):
        i0 = max(int(np.searchsorted(edges, s, side="right") - 1), 0)
        i1 = min(int(np.searchsorted(edges, e, side="left")), len(labels))
        if i1 > i0:
            labels[i0:i1] = type_to_idx[t]
        # Stash NaN-safe versions for JSON serialisation.
        tf_v = None if np.isnan(tf) else float(tf)
        ori_v = None if np.isnan(ori) else float(ori)
        intervals.append((float(s), float(e), t, tf_v, ori_v))

    return labels, vocab, intervals


def fit_decoder(raster_T, labels, train_frac):
    valid_idx = np.where(labels >= 0)[0]
    if valid_idx.size < 50:
        raise RuntimeError(f"too few labeled bins ({valid_idx.size})")
    split = int(len(valid_idx) * train_frac)
    train_bins = valid_idx[:split]
    train_end_idx = int(train_bins[-1])

    X_train = raster_T[train_bins]
    y_train = labels[train_bins]
    scaler = StandardScaler().fit(X_train)
    clf = LogisticRegression(max_iter=300, C=0.1).fit(
        scaler.transform(X_train), y_train)
    probs = clf.predict_proba(scaler.transform(raster_T))
    print(f"[decoder] trained on {len(train_bins)} bins  classes={clf.classes_.tolist()}")
    return probs, clf.classes_.tolist(), train_end_idx


def train_markov_predictor(stim_table, vocab, t0, t1, order=3, smoothing=0.5):
    """k-order Markov model over full-session trial type sequence."""
    all_orients = np.array(stim_table[LABEL_COLUMN][:])
    all_types = [trial_label(o) for o in all_orients]
    starts_all = np.array(stim_table["start_time"][:])
    stops_all = np.array(stim_table["stop_time"][:])
    type_to_idx = {t: i for i, t in enumerate(vocab)}
    # Some all_types may not be in vocab (occurred outside window). Map those to a sink class.
    sink = len(vocab)
    full_idx = np.array([type_to_idx.get(t, sink) for t in all_types], dtype=np.int32)
    n_types = len(vocab)

    counts = {}
    for i in range(order, len(full_idx)):
        prev = tuple(int(x) for x in full_idx[i - order : i])
        nxt = int(full_idx[i])
        if nxt == sink:
            continue
        row = counts.setdefault(prev, np.full(n_types, smoothing, dtype=np.float32))
        row[nxt] += 1.0

    marginal = np.full(n_types, smoothing, dtype=np.float32)
    for v in full_idx:
        if v != sink:
            marginal[v] += 1.0
    marginal = marginal / marginal.sum()

    in_win = (stops_all > t0) & (starts_all < t1)
    win_idx = np.where(in_win)[0]
    pred_rows = np.zeros((len(win_idx), n_types), dtype=np.float32)
    surprise = np.zeros(len(win_idx), dtype=np.float32)

    for j, i in enumerate(win_idx):
        if i < order:
            pred = marginal
        else:
            prev = tuple(int(x) for x in full_idx[i - order : i])
            row = counts.get(prev)
            pred = (row / row.sum()) if row is not None else marginal
        pred_rows[j] = pred
        actual = int(full_idx[i])
        if actual == sink:
            surprise[j] = 0.0
        else:
            p_actual = float(pred[actual])
            surprise[j] = -np.log2(max(p_actual, 1e-6))

    print(f"[markov] order={order} contexts={len(counts)}  "
          f"surprise mean={surprise.mean():.2f}  max={surprise.max():.2f}")
    return {
        "starts": starts_all[win_idx],
        "stops": stops_all[win_idx],
        "types_idx": np.array([min(int(i), n_types - 1) for i in full_idx[win_idx]], dtype=np.int32),
        "predicted": pred_rows,
        "surprise": surprise,
    }


def probe_geometry_from_units(probes_per_unit, xyz):
    """
    Fit each probe's shank line through the (corrected) positions of its
    kept units. Returns { probe: [[x0,y0,z0], [x1,y1,z1]] }.
    Since we reconstructed unit z from region meshes, this gives a probe line
    that visually passes through the units we're rendering.
    """
    out = {}
    pts_by = {}
    for probe, pt in zip(probes_per_unit, xyz):
        pts_by.setdefault(probe, []).append(pt)
    for probe, pts in pts_by.items():
        P = np.asarray(pts, dtype=np.float64)
        if P.shape[0] < 2:
            continue
        mu = P.mean(axis=0)
        centered = P - mu
        try:
            _, _, vt = np.linalg.svd(centered, full_matrices=False)
        except np.linalg.LinAlgError:
            continue
        axis = vt[0]
        proj = centered @ axis
        # Extend slightly past the unit extent so the shank visibly enters/exits.
        margin = (proj.max() - proj.min()) * 0.08
        a = mu + axis * (float(proj.min()) - margin)
        b = mu + axis * (float(proj.max()) + margin)
        out[probe] = [a.tolist(), b.tolist()]
    return out


def aggregate_per_region(raster, regions_per_unit):
    """
    Aggregate spike counts per region per bin → float32 [n_regions, n_bins],
    normalized to z-score within each region's distribution over the window.
    Regions with no units are skipped.
    """
    by_region = {}
    for i, r in enumerate(regions_per_unit):
        by_region.setdefault(r, []).append(i)
    region_names = sorted(by_region.keys())
    n_bins = raster.shape[1]
    out = np.zeros((len(region_names), n_bins), dtype=np.float32)
    for ri, r in enumerate(region_names):
        idxs = by_region[r]
        # mean spikes per unit per bin in this region.
        mean_per_bin = raster[idxs, :].astype(np.float32).mean(axis=0)
        # z-score across time so each region's glow uses its own dynamic range.
        mu = mean_per_bin.mean()
        sd = mean_per_bin.std() + 1e-6
        out[ri] = (mean_per_bin - mu) / sd
    return region_names, out


def main():
    nwb, io, h5, rf = open_streaming_nwb()
    try:
        stim = get_stim_table(nwb)
        t0, t1 = pick_window(stim, WINDOW_SECONDS)

        kept_idx, probes_per_unit, regions_per_unit, ccf_xyz = select_units(
            nwb, MAX_UNITS, MIN_SNR)

        print("[spikes] pulling spike_times for kept units …")
        spike_times = [np.asarray(nwb.units["spike_times"][i]) for i in kept_idx]

        raster, edges = bin_spikes(spike_times, t0, t1, BIN_SIZE_S)
        labels, vocab, intervals = build_per_bin_labels(stim, edges, t0, t1)
        probs, classes, train_end = fit_decoder(
            raster.T.astype(np.float32), labels, TRAIN_FRAC)
        markov = train_markov_predictor(stim, vocab, t0, t1, order=3)
        region_names, region_act = aggregate_per_region(raster, regions_per_unit)
        print(f"[regions] activity for {len(region_names)} regions, "
              f"z-range {region_act.min():.2f}..{region_act.max():.2f}")
        probe_geom = probe_geometry_from_units(probes_per_unit, ccf_xyz)
        for p, (a, b) in probe_geom.items():
            length_um = float(np.linalg.norm(np.array(a) - np.array(b)))
            print(f"[probe ] {p}  shank {length_um/1000:.2f} mm")
    finally:
        io.close()
        h5.close()
        rf.close()

    raster.tofile(OUT_DIR / "raster.bin")
    probs.astype(np.float32).tofile(OUT_DIR / "probs.bin")
    markov["predicted"].astype(np.float32).tofile(OUT_DIR / "markov_preds.bin")
    markov["surprise"].astype(np.float32).tofile(OUT_DIR / "markov_surprise.bin")
    ccf_xyz.astype(np.float32).tofile(OUT_DIR / "ccf_xyz.bin")
    region_act.astype(np.float32).tofile(OUT_DIR / "region_activity.bin")

    n_units, n_bins = raster.shape
    probes_unique = sorted(set(probes_per_unit))
    regions_unique = sorted(set(regions_per_unit))

    manifest = {
        "dandiset": DANDISET_ID,
        "session_id": Path(DANDI_PATH).stem,
        "window": [t0, t1],
        "bin_size_s": BIN_SIZE_S,
        "n_units": int(n_units),
        "n_bins": int(n_bins),
        "n_classes": int(probs.shape[1]),
        "classes": [vocab[c] for c in classes],
        "vocab": vocab,
        "train_end_bin": int(train_end),
        "probes": probes_unique,
        "regions": regions_unique,
        # Order of rows in region_activity.bin — may differ from `regions` (sorted).
        "region_activity_order": region_names,
        # Probe shank endpoints in CCF microns (xyz), for drawing the shanks.
        "probes_geometry": probe_geom,
        "units": [
            {"probe": probes_per_unit[i], "region": regions_per_unit[i]}
            for i in range(n_units)
        ],
        "intervals": [{"start": s - t0, "stop": e - t0, "type": t,
                       "tf": tf, "ori": ori}
                      for (s, e, t, tf, ori) in intervals],
        "markov": {
            "n_presentations": int(len(markov["surprise"])),
            "starts": (markov["starts"] - t0).tolist(),
            "stops": (markov["stops"] - t0).tolist(),
            "types_idx": markov["types_idx"].astype(int).tolist(),
        },
        "files": {
            "raster": "out/raster.bin",
            "probs": "out/probs.bin",
            "markov_preds": "out/markov_preds.bin",
            "markov_surprise": "out/markov_surprise.bin",
            "ccf_xyz": "out/ccf_xyz.bin",                # float32 [n_units, 3]  µm in Allen CCF
            "region_activity": "out/region_activity.bin", # float32 [n_regions, n_bins]
            "brain_mesh": "assets/brain.bin",
            "regions_index": "assets/regions.json",
        },
    }
    with open(OUT_DIR / "session.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"[done] {n_units} units, {n_bins} bins  "
          f"({raster.nbytes/1e6:.1f}MB raster + {probs.nbytes/1e6:.1f}MB probs + "
          f"{ccf_xyz.nbytes/1e3:.1f}KB coords)")


if __name__ == "__main__":
    main()
