# Scripts & Viewers — SCAI-SCI Gait Dataset

| Script | Purpose | Dependencies |
|:---|:---|:---|
| [`camerahmr_pipeline.py`](camerahmr_pipeline.py) | Assembles CameraHMR's per-frame outputs into one SMPL sequence per video (`.pkl`). | `torch`, `smplx`, `pytorch3d`, `scipy`, `numpy` |
| [`../visualize_mocap.py`](../visualize_mocap.py) | Viewer for a MoCap trial: markers in 3D and the force plates. | `ezc3d`, `matplotlib`, `numpy` |
| [`../visualize_smpl.py`](../visualize_smpl.py) | Viewer for an SMPL sequence: skeleton and mesh. | `matplotlib`, `numpy` |

The code that de-identified and assembled the release is not part of this repository. It
covers the C3D header allowlist, the marker protocol, the clinical coding, renumbering,
`trials.csv`, `gait_parameters.csv` and the release checks, and it lives in the SCAI Lab
release toolkit. What it did to the data is described in the data READMEs.

---

## CameraHMR sequence pipeline (`camerahmr_pipeline.py`)

CameraHMR (Patel & Black, 3DV 2025) estimates SMPL pose and shape for each video frame.
This script assembles those per-frame estimates into one sequence per video:

1. *(optional, `--organize`)* sorts CameraHMR's loose outputs into `images/`,
   `obj_output/` and `pkl_output/`;
2. loads each frame's pose, root orientation, shape and translation;
3. computes the 24 joint positions and the 6,890 mesh vertices with `smplx`;
4. changes the axes to Y-up and composes the root orientation to match;
5. writes one `.pkl` per video with `frame_ids`, `global_orient`, `body_pose`, `betas`,
   `trans`, `joints` and `vertices`.

It writes `<video stem>_smpl_sequence.pkl`. The release toolkit then renamed the files with
release participant numbers, flattened them into one folder and removed byte-identical
duplicates, so the script does not reproduce the released file names. In every released
file `trans` is zero; the script writes zeros when CameraHMR provides no translation.

### Arguments

- `--input_dir`: folder with CameraHMR's per-frame `.pkl` files (or loose files with
  `--organize`).
- `--output_dir`: where the sequence files are written.
- `--gender`: SMPL model, `male` or `female` (default `male`).
- `--smpl_model_dir`: folder with `SMPL_MALE.pkl` and `SMPL_FEMALE.pkl` (default
  `smpl_models`).
- `--organize`: sort loose outputs into subfolders first.

### Example

```bash
# sort raw CameraHMR outputs
python scripts/camerahmr_pipeline.py --organize --input_dir /path/to/camerahmr_raw/

# build the sequences
python scripts/camerahmr_pipeline.py \
    --input_dir /path/to/camerahmr_raw/pkl_output \
    --output_dir /path/to/smpl_sequences \
    --gender male \
    --smpl_model_dir smpl_models/
```

The SMPL model files need a license from the [SMPL project page](https://smpl.is.tue.mpg.de/).
The released files do not record which of the two models built each sequence.

---

## Viewers

```bash
python visualize_mocap.py <release>/MoCap_Data/mocap<studyID>-<trial>.c3d [--save frame.png]
python visualize_smpl.py  <release>/SMPL_Data/v<studyID>_sagittal_<li|re>_defaced_smpl_sequence.pkl [--save frame.png]
```

Both open an interactive window with a frame slider. `--save` writes the middle frame to a
PNG instead. Figure titles do not show the participant number. Saved figures still show
participant data, so share them only within the data use agreement.
