# SMPL Sequences (SMPL_Data/) — SCAI-SCI Gait Dataset

3D body pose and shape for each sagittal walking video in the **SCAI-SCI Gait Dataset**. The sequences were reconstructed
frame by frame with **CameraHMR** (Patel & Black, 3DV 2025), which fits the SMPL body model
(Loper et al., 2015). [`scripts/camerahmr_pipeline.py`](../scripts/camerahmr_pipeline.py)
assembled them into one sequence per video. Of five mesh-recovery methods benchmarked on
this cohort, CameraHMR reconstructed the most frames with near-lowest joint error; see
[Why CameraHMR](../README.md#why-camerahmr).

The files are in the [PhysioNet](https://physionet.org/content/scai-sci-gait-dataset) release, not in this repository. The source videos are not
released.

## Files

- **Count:** 300 sequences from 239 participants (178 with one, 61 with two). One
  participant has motion capture but no sequence.
- **Name:** `v<studyID>_sagittal_<li|re>_defaced_smpl_sequence.pkl`, in one flat folder.
  `li` (links) and `re` (rechts) are the walking direction in the image, as the laboratory
  named the video.
- **Length:** 46–553 frames per sequence, 44,980 frames in total.
- **Format:** a Python pickle holding a dict of NumPy arrays. It loads with `pickle`
  alone; no torch or chumpy is needed. Unpickling can run code, so load only files from
  the official release.

## Contents

| Key | Shape | dtype | Meaning |
|:---|:---|:---|:---|
| `frame_ids` | `(F,)` | int64 | Frame number at the 15 fps of the SMPL sequences and renders. **Not always contiguous**; see below. |
| `global_orient` | `(F, 3)` | float64 | Root orientation, axis-angle (rad). |
| `body_pose` | `(F, 69)` | float32 | Rotations of the 23 non-root joints, axis-angle (rad). |
| `betas` | `(F, 10)` | float32 | SMPL shape coefficients, **estimated per frame**. |
| `trans` | `(F, 3)` | float32 | **All zeros**: the sequences carry no global translation. |
| `joints` | `(F, 24, 3)` | float32 | SMPL joint positions, m. |
| `vertices` | `(F, 6890, 3)` | float32 | SMPL mesh vertices, m. |

The files store no frame rate, sex or model name.

## Conventions and caveats

- **Y is up.** X is horizontal in the image plane (the walking direction), and Z is depth.
  This is not the Z-up laboratory frame of the MoCap data; rotate one of them before
  comparing.
- **Root-relative.** `trans` is zero, so the body walks in place. Walking speed and step
  length cannot be read from these files; use `gait_parameters.csv`. Coordinates are in
  the SMPL model frame, so the pelvis sits about 0.2–0.3 m from the origin rather than
  at it.
- **Time.** The SMPL sequences and their renders run at 15 fps; this is not the frame
  rate of the original recordings. Use `frame_ids / 15` for time in seconds. Sequences are trimmed from the video
  (`frame_first` and `frame_last` in `trials.csv`), and 68 sequences skip frames (gaps of
  2–13 frames, 240 in total) where the detector dropped a frame. `trials.csv` lists
  `frame_gaps` and `frames_skipped` per file. Resample onto a regular grid before
  differentiating.
- **Body shape.** `betas` varies from frame to frame because each frame is estimated on
  its own. Average over the sequence (or take the median) for one shape.
- **Walking direction** is in `trials.csv` (`direction`). For 2 sequences whose video had
  no direction tag, it was inferred from the body orientation (`direction_source =
  inferred`). For 2 sequences the orientation disagrees with the tag in the file name
  (`direction_check`).
- **Stored joints and pose parameters.** `joints` and `vertices` are the pipeline's
  output after its axis change. If you recompute them from `global_orient`, `body_pose`
  and `betas` with an SMPL implementation, check the orientation against the stored
  `joints` before mixing the two.
- **Link to MoCap.** A sequence belongs to the same participant and session as the MoCap
  trials, but which trial it matches is not recorded.

<!-- TODO(verify): 180° about Y between stored joints and FK of global_orient in 299/300 files (array check, not yet confirmed with smplx) -->

## Joint indices

| Index | Joint | Index | Joint | Index | Joint |
|---:|:---|---:|:---|---:|:---|
| 0 | Pelvis | 8 | R_Ankle | 16 | L_Shoulder |
| 1 | L_Hip | 9 | Spine3 | 17 | R_Shoulder |
| 2 | R_Hip | 10 | L_Foot | 18 | L_Elbow |
| 3 | Spine1 | 11 | R_Foot | 19 | R_Elbow |
| 4 | L_Knee | 12 | Neck | 20 | L_Wrist |
| 5 | R_Knee | 13 | L_Collar | 21 | R_Wrist |
| 6 | Spine2 | 14 | R_Collar | 22 | L_Hand |
| 7 | L_Ankle | 15 | Head | 23 | R_Hand |

Parents: 0→1,2,3 · 1→4→7→10 · 2→5→8→11 · 3→6→9→12→15 · 12→13→16→18→20→22 ·
12→14→17→19→21→23.

## Loading

```python
from pathlib import Path
import pickle
import numpy as np

DATA = Path("/path/to/RELEASE_v1.5_SCAI-SCI-Gait")
path = sorted((DATA / "SMPL_Data").glob("*.pkl"))[0]
with open(path, "rb") as f:
    seq = pickle.load(f)

t = seq["frame_ids"] / 15.0                  # seconds, may have gaps
joints = seq["joints"]                       # (F, 24, 3), m, Y up
betas = np.median(seq["betas"], axis=0)      # one shape per sequence

# knee height above the ankle, left side (Y is vertical)
knee_above_ankle = joints[:, 4, 1] - joints[:, 7, 1]
print(f"{len(t)} frames over {t[-1] - t[0]:.1f} s; "
      f"median knee-ankle height {np.median(knee_above_ankle):.2f} m")
```

## Viewer

```bash
python visualize_smpl.py $DATA/SMPL_Data/v<studyID>_sagittal_<li|re>_defaced_smpl_sequence.pkl
python visualize_smpl.py $DATA/SMPL_Data/v<studyID>_sagittal_<li|re>_defaced_smpl_sequence.pkl --save frame.png
```

The viewer draws the skeleton (left blue, right red, midline green) and the mesh. For a
mesh surface it needs the SMPL faces: `smpl_faces.npy`, or the model files from the
[Max Planck Institute](https://smpl.is.tue.mpg.de/), in `smpl_model/` next to the
viewer. The official SMPL model pickle files require `chumpy`. Without the faces the mesh is drawn as a
point cloud.

## Renders

Each sequence is also released as a video of the mesh; see
[`../SMPL_Videos/`](../SMPL_Videos/README.md).
