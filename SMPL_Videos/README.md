# SMPL 3D Mesh Renders (SMPL_Videos/) — SCAI-SCI Gait Dataset

Each SMPL sequence in the **SCAI-SCI Gait Dataset** rendered as a video: a grey SMPL mesh on a black background. The
renders contain no camera image. SMPL is a template mesh without texture or facial
geometry, fitted to defaced video.

The files are in the [PhysioNet](https://physionet.org/content/scai-sci-gait-dataset) release, not in this repository.

## Files

- **Count:** 299 renders from 239 participants. One SMPL sequence has no render.
- **Name:** `v<studyID>_sagittal_<li|re>_defaced.mp4`, the same stem as the sequence
  `v<studyID>_sagittal_<li|re>_defaced_smpl_sequence.pkl` in `SMPL_Data/`.
- **Format:** H.264 MP4 at 15 fps (the rate of the SMPL sequences), in the frame size of the source video (1920 × 1088 in
  163 renders, 720 × 576 in 136). The container carries no creation time.
- **Length:** 44,694 frames, about 50 minutes in total.

## Linking

`trials.csv` has one row per render (`modality = smpl_video`) with `n_frames`,
`duration_s`, `video_fps`, `video_width`, `video_height` and `direction`. Its
`linked_file` points to the sequence, and the sequence's row points back. As for the
sequences, which MoCap trial a render matches is not recorded.
