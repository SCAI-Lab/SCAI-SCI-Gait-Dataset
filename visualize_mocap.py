# Author: Shreyasvi Natraj
# Project Leadership: Shreyasvi Natraj (Lead) and Diego Paez-Granados (Principal Investigator)
# Spinal Cord Artificial Intelligence (SCAI) Lab, ETH Zürich & Swiss Paraplegic Research

"""
SCAI-SCI Gait Dataset - MoCap and Force Plate 3D Visualizer
===========================================================
Interactive 3D visualization of 20-marker lower-body optical motion capture
(IOR protocol) alongside synchronized 6-axis ground reaction forces (Fx, Fy, Fz).

Author:
    Shreyasvi Natraj

Project Leadership:
    Shreyasvi Natraj (Lead)
    Diego Paez-Granados (Principal Investigator)

Affiliations:
    Spinal Cord Artificial Intelligence (SCAI) Lab, ETH Zürich, Switzerland
    Swiss Paraplegic Research, Nottwil, Switzerland

Usage:
    python visualize_mocap.py <release>/MoCap_Data/mocap<studyID>-<trial>.c3d
    python visualize_mocap.py <file.c3d> --save output.png

Forces are plotted as stored in the file after calibration: the force exerted on the
plate, so vertical load (Fz) is negative. The dashed line on the force plots marks
the frame shown in the 3D view.
"""

__author__ = "Shreyasvi Natraj"
__credits__ = ["Shreyasvi Natraj (Lead)", "Diego Paez-Granados (Principal Investigator)"]

import argparse
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from ezc3d import c3d

# Skeleton connections for lower body markers
SKELETON_LINKS = [
    # Pelvis
    ('L_IAS', 'R_IAS'), ('L_IAS', 'L_IPS'), ('R_IAS', 'R_IPS'), ('L_IPS', 'R_IPS'),
    # Left leg
    ('L_IAS', 'L_FTC'), ('L_IAS', 'L_FLE'), ('L_FTC', 'L_FLE'),
    ('L_FLE', 'L_TTC'), ('L_FLE', 'L_FAX'),
    ('L_TTC', 'L_FAL'), ('L_FAX', 'L_FAL'),
    ('L_FAL', 'L_FCC'), ('L_FAL', 'L_FM1'), ('L_FAL', 'L_FM5'),
    ('L_FCC', 'L_FM1'), ('L_FCC', 'L_FM5'), ('L_FM1', 'L_FM5'),
    # Right leg
    ('R_IAS', 'R_FTC'), ('R_IAS', 'R_FLE'), ('R_FTC', 'R_FLE'),
    ('R_FLE', 'R_TTC'), ('R_FLE', 'R_FAX'),
    ('R_TTC', 'R_FAL'), ('R_FAX', 'R_FAL'),
    ('R_FAL', 'R_FCC'), ('R_FAL', 'R_FM1'), ('R_FAL', 'R_FM5'),
    ('R_FCC', 'R_FM1'), ('R_FCC', 'R_FM5'), ('R_FM1', 'R_FM5'),
]

PELVIS = {'L_IAS', 'R_IAS', 'L_IPS', 'R_IPS'}

MARKER_COLORS = {
    'L_IAS': '#2ecc71', 'L_IPS': '#2ecc71', 'R_IPS': '#2ecc71', 'R_IAS': '#2ecc71',
    'L_FTC': '#3498db', 'L_FLE': '#3498db', 'L_FAX': '#3498db', 'L_TTC': '#3498db',
    'L_FAL': '#3498db', 'L_FCC': '#3498db', 'L_FM1': '#3498db', 'L_FM5': '#3498db',
    'R_FTC': '#e74c3c', 'R_FLE': '#e74c3c', 'R_FAX': '#e74c3c', 'R_TTC': '#e74c3c',
    'R_FAL': '#e74c3c', 'R_FCC': '#e74c3c', 'R_FM1': '#e74c3c', 'R_FM5': '#e74c3c',
}


def extract_grf_ezc3d(c_data):
    """Extract GRF from c3d using ezc3d. Returns list of dicts per force plate."""
    params = c_data['parameters']
    if 'FORCE_PLATFORM' not in params:
        return []

    fp_params = params['FORCE_PLATFORM']
    num_fp = int(fp_params['USED']['value'][0])
    if num_fp == 0:
        return []

    analog_data = c_data['data']['analogs']  # (1, n_channels, n_samples)
    analog_rate = float(params['ANALOG']['RATE']['value'][0])
    channels_per_fp = fp_params['CHANNEL']['value']  # (n_ch, n_fp)
    fp_types = fp_params['TYPE']['value']
    cal_matrix = fp_params.get('CAL_MATRIX', {}).get('value', None)

    force_plates = []
    for fp_idx in range(num_fp):
        fp_type = int(fp_types[fp_idx])
        ch_indices = channels_per_fp[:, fp_idx] - 1  # 0-based
        raw = analog_data[0, ch_indices, :]  # (6, n_samples)

        if fp_type == 4 and cal_matrix is not None:
            cal = cal_matrix[:, :, fp_idx]
            calibrated = cal @ raw
            fx, fy, fz = calibrated[0], calibrated[1], calibrated[2]
        else:
            fx, fy, fz = raw[0], raw[1], raw[2]

        force_plates.append({'fx': fx, 'fy': fy, 'fz': fz})

    return force_plates


def visualize(filepath, save_path=None):
    print("Reading C3D trial (ezc3d)...")
    c_data = c3d(filepath)
    params = c_data['parameters']

    # ── Markers ──
    labels = params['POINT']['LABELS']['value']
    points = c_data['data']['points']  # (4, n_markers, n_frames)
    video_rate = float(params['POINT']['RATE']['value'][0])
    n_frames = points.shape[2]
    label_to_idx = {name: i for i, name in enumerate(labels)}
    print(f"  Markers: {len(labels)}")
    print(f"  Frames: {n_frames}, Marker rate: {video_rate} Hz")

    # ── GRF ──
    analog_rate = float(params['ANALOG']['RATE']['value'][0]) if 'ANALOG' in params else 0
    force_plates = extract_grf_ezc3d(c_data)
    num_fp = len(force_plates)
    print(f"  Force Plates: {num_fp}, Analog Rate: {analog_rate} Hz")

    # ── Build figure ──
    # We use a dedicated row for the slider between the 3D plot and GRF plots
    if num_fp > 0:
        fig = plt.figure(num="SCAI-SCI Gait Dataset - MoCap & Force Plates", figsize=(15, 10))
        fig.suptitle("SCAI-SCI Gait Dataset: MoCap and Force Plates", fontsize=14, fontweight='bold')

        gs = fig.add_gridspec(2 + num_fp, 3, height_ratios=[3.2, 0.12] + [1] * num_fp)
        ax3d = fig.add_subplot(gs[0, :], projection='3d')

        if save_path is None:
            slider_ax = fig.add_subplot(gs[1, :])

        grf_axes = []
        for i in range(num_fp):
            for j in range(3):
                ax = fig.add_subplot(gs[2 + i, j])
                grf_axes.append(ax)
    else:
        fig = plt.figure(num="SCAI-SCI Gait Dataset - MoCap", figsize=(12, 10))
        fig.suptitle("SCAI-SCI Gait Dataset: MoCap", fontsize=14, fontweight='bold')
        
        gs = fig.add_gridspec(2, 1, height_ratios=[3.2, 0.12])
        ax3d = fig.add_subplot(gs[0, :], projection='3d')

        if save_path is None:
            slider_ax = fig.add_subplot(gs[1, :])
        
        grf_axes = []

    # ── Plot GRF ──
    force_labels = [('Fx', '#e74c3c'), ('Fy', '#27ae60'), ('Fz', '#2980b9')]
    force_names = ['fx', 'fy', 'fz']
    cursors = []
    for fp_idx in range(num_fp):
        fp = force_plates[fp_idx]
        for j in range(3):
            ax = grf_axes[fp_idx * 3 + j]
            data = fp[force_names[j]]
            t_analog = np.arange(len(data)) / analog_rate
            ax.plot(t_analog, data, color=force_labels[j][1], linewidth=0.8)
            ax.set_title(f"FP{fp_idx+1} {force_labels[j][0]}", fontsize=9)
            ax.set_ylabel("Force [N]", fontsize=8)
            ax.set_xlabel("Time [s]", fontsize=8)
            ax.tick_params(labelsize=7)
            ax.grid(True, alpha=0.3)
            cursors.append(ax.axvline(0, color='#555', linestyle='--', linewidth=0.8))

    # ── 3D skeleton ──
    def draw_skeleton(frame_idx):
        ax3d.cla()
        all_x, all_y, all_z = [], [], []

        for name in labels:
            idx = label_to_idx[name]
            x, y, z = points[0, idx, frame_idx], points[1, idx, frame_idx], points[2, idx, frame_idx]
            if np.isnan(x) or np.isnan(y) or np.isnan(z):
                continue
            color = MARKER_COLORS.get(name, '#95a5a6')
            ax3d.scatter(x, y, z, c=color, s=40, edgecolors='black', linewidth=0.5, zorder=5)
            ax3d.text(x, y, z + 15, name, fontsize=5, ha='center', va='bottom', color='#555')
            all_x.append(x); all_y.append(y); all_z.append(z)

        for (a, b) in SKELETON_LINKS:
            if a not in label_to_idx or b not in label_to_idx:
                continue
            ia, ib = label_to_idx[a], label_to_idx[b]
            xa, ya, za = points[0, ia, frame_idx], points[1, ia, frame_idx], points[2, ia, frame_idx]
            xb, yb, zb = points[0, ib, frame_idx], points[1, ib, frame_idx], points[2, ib, frame_idx]
            if any(np.isnan(v) for v in [xa, ya, za, xb, yb, zb]):
                continue
            if a in PELVIS and b in PELVIS:
                link_color = '#2ecc71'
            elif a.startswith('L_') and b.startswith('L_'):
                link_color = '#3498db'
            elif a.startswith('R_') and b.startswith('R_'):
                link_color = '#e74c3c'
            else:
                link_color = '#2ecc71'
            ax3d.plot([xa, xb], [ya, yb], [za, zb], color=link_color, linewidth=1.5, alpha=0.7)

        if all_x:
            cx, cy, cz = (min(all_x)+max(all_x))/2, (min(all_y)+max(all_y))/2, (min(all_z)+max(all_z))/2
            max_range = max(max(all_x)-min(all_x), max(all_y)-min(all_y), max(all_z)-min(all_z))/2 + 50
            ax3d.set_xlim(cx-max_range, cx+max_range)
            ax3d.set_ylim(cy-max_range, cy+max_range)
            ax3d.set_zlim(cz-max_range, cz+max_range)

        time_s = frame_idx / video_rate
        for line in cursors:
            line.set_xdata([time_s, time_s])
        ax3d.set_title(f"Frame {frame_idx}/{n_frames-1}  (t={time_s:.2f}s)", fontsize=10)
        ax3d.set_xlabel("X [mm]", fontsize=8)
        ax3d.set_ylabel("Y [mm]", fontsize=8)
        ax3d.set_zlabel("Z [mm]", fontsize=8)
        ax3d.tick_params(labelsize=7)

    init_frame = n_frames // 2
    draw_skeleton(init_frame)

    # ── Frame slider ──
    if save_path is None:
        slider = Slider(slider_ax, 'Frame', 0, n_frames - 1, valinit=init_frame, valstep=1)
        
        def update(val):
            draw_skeleton(int(slider.val))
            fig.canvas.draw_idle()

        slider.on_changed(update)
    
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")
    else:
        plt.show()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="SCAI-SCI Gait Dataset: Visualize a MoCap trial (.c3d) with its force plates.")
    ap.add_argument("trial", help="path to a .c3d file")
    ap.add_argument("--save", metavar="PNG", help="write the middle frame to a file instead of opening a window")
    args = ap.parse_args()

    if not os.path.exists(args.trial):
        ap.error(f"file not found: {args.trial}")

    visualize(args.trial, args.save)
