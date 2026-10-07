# Optical Motion Capture & Force Plates (MoCap_Data/) — SCAI-SCI Gait Dataset

Optoelectronic lower-body motion capture with two force plates and, in most trials,
surface EMG, as part of the **SCAI-SCI Gait Dataset**. The data files are distributed through [PhysioNet](https://physionet.org/content/scai-sci-gait-dataset), not in this repository.

## Files

- **Count:** 300 trials from 240 participants (180 with one trial, 60 with two).
- **Name:** `mocap<studyID>-<trial>.c3d`. `<studyID>` is the release participant number
  (3 digits). `<trial>` is the laboratory's trial number within the session, not a running
  index.
- **Length:** 2.5–12.3 s per trial, 262–2,461 marker frames; 222,400 frames in total.
- **Format:** C3D, readable with [`ezc3d`](https://github.com/pyomeca/ezc3d), `btk` or any
  C3D reader.

## Acquisition

| | |
|:---|:---|
| Cameras | Qualisys Miqus optoelectronic system (Qualisys AB, Sweden); 6–8 gait cycles per assessment |
| Markers | 20 lower-body markers, Istituti Ortopedici Rizzoli (IOR) protocol |
| Force plates | 2 × Bertec 4060-06 (Bertec Corporation, USA) |
| EMG | Noraxon Ultium (Noraxon Inc., USA), 194 trials of 171 participants |
| Processing | Labelled in Qualisys Track Manager; gaps of up to 10 frames filled by polynomial interpolation; exported as C3D |

## What each file contains

| Group | Content |
|:---|:---|
| `POINT` | The 20 protocol markers, in one fixed order in every file. Units: mm. |
| `ANALOG` | Force-plate channels (2 × 6), EMG where recorded, a `Sync` channel in most files, and in some files unidentified channels (listed per trial in `trials.csv`). Units: V. |
| `FORCE_PLATFORM` | 2 plates, type 4: `USED`, `TYPE`, `CHANNEL`, `CORNERS`, `ORIGIN`, `CAL_MATRIX` (6 × 6, stored by column), `ZERO`. |
| `EVENT` | Acquisition triggers only (`Trigger event`, 0–2 per trial). **No gait events are annotated.** |
| `ROTATION`, `EZC3D` | Added by the C3D writer; carry no data. |

**Sampling rates differ between trials.** Nothing was resampled. The rates are stored in
each file (`POINT:RATE`, `ANALOG:RATE`) and listed in `trials.csv`.

| Markers | Trials | | Analog | Trials |
|---:|---:|---|---:|---:|
| 200 Hz | 163 | | 1500 Hz | 108 |
| 100 Hz | 129 | | 1000 Hz | 85 |
| 246 Hz | 8 | | 2000 Hz | 77 |
| | | | 500 Hz | 21 |
| | | | 1722 Hz | 8 |
| | | | 1600 Hz | 1 |

**Axes.** Z is vertical and Y is medio-lateral. Participants walk along X in both
directions (+X and −X). The direction is not normalised between trials.

**De-identification.** Only the `POINT`, `ANALOG`, `FORCE_PLATFORM` and `EVENT` groups
are kept, with free-text descriptions blanked. The writer library adds `ROTATION` and
`EZC3D`. Every other group of the acquisition software was removed, including patient
fields, operator and timestamps. Trajectories and analog signals are unchanged.

## Marker set (20)

Order in the files: `L_IAS, L_IPS, R_IPS, R_IAS, L_FTC, L_FLE, L_FAX, L_TTC, L_FAL,
L_FCC, L_FM1, L_FM5, R_FTC, R_FLE, R_FAX, R_TTC, R_FAL, R_FCC, R_FM1, R_FM5`.

| Label | Landmark |
|:---|:---|
| `IAS` | Anterior superior iliac spine |
| `IPS` | Posterior superior iliac spine |
| `FTC` | Greater trochanter |
| `FLE` | Lateral femoral epicondyle |
| `FAX` | Auxiliary knee marker (knee axis orientation) |
| `TTC` | Tibial tuberosity |
| `FAL` | Lateral malleolus |
| `FCC` | Calcaneus (heel) |
| `FM1` | First metatarsal head |
| `FM5` | Fifth metatarsal head |

Each label has an `L_` (left) and an `R_` (right) version. Trials recorded with an
extended full-body set were reduced to these 20. A marker absent from a whole recording
keeps its label and is NaN throughout (`missing_markers` in `trials.csv`).

**Missing samples** are NaN. 37 trials have all 20 markers in fewer than 90% of frames.
`trials.csv` gives `markers_complete_pct`, `markers_with_gaps` and
`worst_marker_missing_pct` per trial.

## Force plates

Forces (N) and moments (N·mm) are computed as the plate's `CAL_MATRIX` times its six analog channels.
The channels come from `FORCE_PLATFORM:CHANNEL`; do not rely on the analog labels.

- **Channel names.** 163 trials label the plate channels `Fx_FP1` … `Mz_FP2` (analog 1–6
  and 9–14). 137 use generic `Channel_NN` labels; there, plate 1 is on `Channel_02–07`.
  `trials.csv` gives the map per trial (`force_plate_channels`).
- **Channel map error.** In 1 trial, `FORCE_PLATFORM:CHANNEL` assigns `Channel_12` twice,
  so plate 2 is short of one component (`force_plate_map`).
- **Units.** The analog signals are in V. A few files declare N on some channels; they
  still need `CAL_MATRIX` (`analog_units`).
- **Sign.** As stored, forces are those exerted **on** the plate, so the vertical load
  (Fz) is negative during stance. Negate for the ground reaction force on the body.
- **Analog tail.** Some trials end with a short run of NaN analog samples, at most 0.7%
  (`analog_nan_max_pct`).

## EMG

Surface EMG is **raw**, as recorded: not filtered, rectified, or normalized. It is in V at
the analog rate. Apply your own processing (for example, a band-pass filter and an RMS envelope).
Channels are labelled by side and muscle (for example `L Tibialis Anterior`). The most
frequent are tibialis anterior and gastrocnemius lateralis, recorded in almost every EMG
trial; some trials add biceps femoris, vastus medialis, gluteus medius and rectus
femoris. `trials.csv` lists the muscles per trial (`emg_muscles`, `n_emg_channels`).

## trials.csv (MoCap rows)

`trials.csv` has one row per released file (899 rows). Its MoCap rows (`modality =
mocap`) give per trial:

`studyID`, `file`, `trial`, `n_frames`, `duration_s`, `point_rate_hz`, `analog_rate_hz`,
`markers_complete_pct`, `markers_with_gaps`, `worst_marker_missing_pct`,
`missing_markers`, `n_analog_channels`, `emg_muscles`, `n_emg_channels`,
`n_force_plates`, `force_plate_channels`, `force_plate_map`, `other_analog_channels`,
`analog_units`, `analog_nan_max_pct`, `n_trigger_events`, `has_metadata`.

Each column is defined in [`../metadata/data_dictionary.csv`](../metadata/data_dictionary.csv).

## Gait parameters

`gait_parameters.csv` has one row per MoCap trial (300 rows). It joins on `file`, or on
`studyID` and `trial`.

| Column | Unit | Definition |
|:---|:---|:---|
| `status` | | `ok`, or why values are empty: `no travel (stationary trial)`, `markers missing`, `no stride detected` |
| `n_strides_left`, `n_strides_right` | count | consecutive heel strikes 0.5–3.0 s apart |
| `walking_speed_m_s` | m/s | pelvis travel along the direction of progression between the first and last heel strike |
| `cadence_steps_min` | steps/min | 120 / mean stride time |
| `stride_time_s` | s | mean over both sides |
| `stride_time_cv` | | standard deviation / mean; empty below three strides |
| `stride_length_m` | m | heel travel along the direction of progression over one stride, mean over both sides |
| `step_length_left_m`, `step_length_right_m` | m | heel-to-heel distance along the direction of progression at heel strike |
| `step_length_asymmetry` | | \|left − right\| / mean; 0 is symmetric |
| `step_width_m` | m | distance between the heels across the direction of progression at heel strike |
| `stance_pct_left`, `stance_pct_right` | % of stride | heel strike to the next toe-off |
| `swing_pct_left`, `swing_pct_right` | % of stride | 100 − stance |
| `double_support_pct` | % of stride | left stance + right stance − 100 |

Strides are detected from the marker trajectories, following Zeni et al. (*Gait &
Posture*, 2008), because the C3D files contain no pre-annotated gait events. Of the 300 trials, 292 are
`ok`, 6 are stationary, 1 lacks the required markers, and 1 has no detectable stride. The
definitions follow the NINDS SCI Common Data Elements (supplemental, stride analysis).

## Loading

```python
from pathlib import Path
import numpy as np
from ezc3d import c3d

DATA = Path("/path/to/RELEASE_v1.5_SCAI-SCI-Gait")
trial = sorted((DATA / "MoCap_Data").glob("*.c3d"))[0]

c = c3d(str(trial))
P = c["parameters"]

labels = P["POINT"]["LABELS"]["value"]              # the 20 protocol markers
xyz = c["data"]["points"][:3]                       # (3, 20, n_frames), mm, NaN = missing
rate = float(P["POINT"]["RATE"]["value"][0])
t = np.arange(xyz.shape[2]) / rate

heel_l = xyz[:, labels.index("L_FCC"), :]           # Z (index 2) is vertical
print(f"{len(labels)} markers, {xyz.shape[2]} frames at {rate:g} Hz")

# forces and moments of plate 1, calibrated
fp = P["FORCE_PLATFORM"]
ch = fp["CHANNEL"]["value"][:, 0] - 1               # 0-based analog channels of plate 1
raw = c["data"]["analogs"][0, ch, :]                # V
fm = fp["CAL_MATRIX"]["value"][:, :, 0] @ raw       # Fx Fy Fz (N), Mx My Mz (N·mm)
fz = fm[2]                                          # negative under load
```

## Viewer

```bash
python visualize_mocap.py $DATA/MoCap_Data/mocap<studyID>-<trial>.c3d
python visualize_mocap.py $DATA/MoCap_Data/mocap<studyID>-<trial>.c3d --save frame.png
```

The viewer shows the markers in 3D (pelvis green, left blue, right red), with Fx, Fy and
Fz of both plates below. A dashed line marks the frame shown in the 3D view.
