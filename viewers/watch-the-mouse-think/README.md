# watch the mouse think

A small 3D viewer for Allen Neuropixels recordings. Streams a session from
DANDI, places each recorded unit at its true CCF coordinate inside the Allen
mouse brain atlas, glows region-by-region as activity flows through.

Inspired by [Jérôme Lecoq's tweet](https://twitter.com/LecoqJerome) about the
[OpenScope Community Predictive Processing](https://github.com/AllenNeuralDynamics/openscope-community-predictive-processing)
project.

## Run

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python fetch_brain_mesh.py       # ~7MB of Allen CCF region meshes
.venv/bin/python prep_session.py           # streams a slice from DANDI

python3 -m http.server 8788
open http://localhost:8788/viewer.html
```

## Honest framing

- **Data:** Allen Visual Coding Neuropixels, DANDI [000021](https://dandiarchive.org/dandiset/000021), session `715093703`.
- **Stim:** drifting gratings (randomized by design — so the on-screen "sequence surprise" panel reacts to trial *transitions*, not to predictive-coding deviants).
- **3D anatomy:** AP and DV are real CCF microns. ML is reconstructed per-unit by sampling each unit's anatomical region's actual mesh extent — DANDI 000021's NWB packaging mirrors the ML coord (z) from DV (y); see `prep_session.py:load_region_ml_bounds`.

Built to drop onto the OpenScope PP data once those NWBs ship CCF registration.
