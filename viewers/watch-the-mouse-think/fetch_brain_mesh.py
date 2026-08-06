"""
Download Allen CCF meshes and convert them to compact binary form
the viewer can load fast.

  assets/brain.bin                 — whole brain shell (structure 997, "root")
  assets/region_<acronym>.bin      — one per recorded region
  assets/regions.json              — index { acronym: { file, color, ccf_id } }

Each .bin layout:
  HEADER:  n_vertices uint32, n_indices uint32
  VERTS:   float32 * n_vertices * 3   (Allen CCF microns)
  INDICES: uint32 * n_indices         (flat triangle list)
"""
import json
import struct
import urllib.request
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
ASSETS = HERE / "assets"
ASSETS.mkdir(exist_ok=True)

MESH_URL_TMPL = ("https://download.alleninstitute.org/informatics-archive/"
                 "current-release/mouse_ccf/annotation/ccf_2017/"
                 "structure_meshes/{sid}.obj")

# Allen Mouse Brain CCF structure IDs. Verified against the Allen ontology.
# Acronym -> (structure_id, display_color_hex).
REGIONS = {
    # whole brain (translucent container; rendered separately)
    "root": (997, "#9bb0d0"),
    # visual cortex hierarchy
    "VISp":  (385, "#9bd8ff"),
    "VISl":  (409, "#7cc7ff"),
    "VISpm": (533, "#c0a8ff"),
    "VISam": (394, "#b9a6ff"),
    "VISrl": (417, "#85d0c5"),
    # thalamic visual relays
    "LGd":   (170, "#ffd166"),
    "LP":    (218, "#ffb466"),
    "PO":    (1020, "#8ed6ff"),
    # hippocampus subfields
    "CA1":   (382, "#ff8da3"),
    "CA3":   (463, "#ff7090"),
    "DG":    (726, "#ff5b80"),
    # midbrain / pretectum
    "APN":   (215, "#88f0c0"),
}


def fetch_obj(structure_id: int) -> Path:
    obj_path = ASSETS / f"struct_{structure_id}.obj"
    if obj_path.exists() and obj_path.stat().st_size > 0:
        return obj_path
    url = MESH_URL_TMPL.format(sid=structure_id)
    try:
        urllib.request.urlretrieve(url, obj_path)
    except Exception as e:
        if obj_path.exists():
            obj_path.unlink()
        raise RuntimeError(f"download {structure_id} ({url}): {e}")
    return obj_path


def parse_obj(path: Path):
    verts, faces = [], []
    with open(path, "rb") as f:
        for line in f:
            if not line:
                continue
            t = line[:2]
            if t == b"v ":
                _, x, y, z = line.split()[:4]
                verts.append((float(x), float(y), float(z)))
            elif t == b"f ":
                idxs = [int(p.split(b"/")[0]) - 1 for p in line.split()[1:]]
                for k in range(1, len(idxs) - 1):
                    faces.append((idxs[0], idxs[k], idxs[k + 1]))
    return np.asarray(verts, dtype=np.float32), np.asarray(faces, dtype=np.uint32).ravel()


def write_bin(verts: np.ndarray, indices: np.ndarray, path: Path):
    with open(path, "wb") as f:
        f.write(struct.pack("<II", verts.shape[0], indices.size))
        verts.tofile(f)
        indices.tofile(f)


def bake_one(acronym: str, sid: int) -> tuple[Path, int, int] | None:
    try:
        obj = fetch_obj(sid)
    except RuntimeError as e:
        print(f"[skip]  {acronym} (sid={sid}) — {e}")
        return None
    v, idx = parse_obj(obj)
    if v.size == 0:
        print(f"[skip]  {acronym} (sid={sid}) — empty mesh")
        return None
    out_name = "brain.bin" if acronym == "root" else f"region_{acronym}.bin"
    out_path = ASSETS / out_name
    write_bin(v, idx, out_path)
    print(f"[bake]  {acronym:<6} sid={sid:<5}  {v.shape[0]:>6} verts  {idx.size//3:>6} tris  "
          f"{out_path.stat().st_size/1e6:.2f} MB  -> {out_name}")
    return out_path, v.shape[0], idx.size


def main():
    print(f"[start] fetching {len(REGIONS)} meshes from Allen CCF …")
    index = {}
    for acronym, (sid, color) in REGIONS.items():
        result = bake_one(acronym, sid)
        if result is None:
            continue
        out_path, nV, nI = result
        index[acronym] = {
            "file": ("assets/" + out_path.name),
            "ccf_id": sid,
            "color": color,
            "n_verts": int(nV),
            "n_tris": int(nI // 3),
        }
    with open(ASSETS / "regions.json", "w") as f:
        json.dump(index, f, indent=2)
    print(f"[done]  wrote assets/regions.json with {len(index)} entries")


if __name__ == "__main__":
    main()
