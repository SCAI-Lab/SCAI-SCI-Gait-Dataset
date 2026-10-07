# Author: Shreyasvi Natraj
# Project Leadership: Shreyasvi Natraj (Lead) and Diego Paez-Granados (Principal Investigator)
# Spinal Cord Artificial Intelligence (SCAI) Lab, ETH Zürich & Swiss Paraplegic Research

"""
SCAI-SCI Gait Dataset - SMPL 3D Sequence Visualizer
===================================================
Interactive 3D visualization of reconstructed SMPL human body model sequences:
24-joint kinematic skeleton and 6,890-vertex body surface mesh (or point cloud).

Author:
    Shreyasvi Natraj

Project Leadership:
    Shreyasvi Natraj (Lead)
    Diego Paez-Granados (Principal Investigator)

Affiliations:
    Spinal Cord Artificial Intelligence (SCAI) Lab, ETH Zürich, Switzerland
    Swiss Paraplegic Research, Nottwil, Switzerland

Usage:
    python visualize_smpl.py <release>/SMPL_Data/v<studyID>_sagittal_<li|re>_defaced_smpl_sequence.pkl
    python visualize_smpl.py <file.pkl> --save output.png

The SMPL faces are looked for in smpl_model/ (or smpl_models/) next to this script:
smpl_faces.npy, or SMPL_MALE.pkl / SMPL_FEMALE.pkl from https://smpl.is.tue.mpg.de/.

The sequences are root-relative and Y-up (SMPL camera convention). For display the
axes are mapped so that vertical is drawn vertical: plot X = data X (progression),
plot Y = data Z (depth), plot Z = data Y (up).
"""

__author__ = "Shreyasvi Natraj"
__credits__ = ["Shreyasvi Natraj (Lead)", "Diego Paez-Granados (Principal Investigator)"]

import argparse
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# ── SMPL 24-joint names ──
JOINT_NAMES = [
    'Pelvis', 'L_Hip', 'R_Hip', 'Spine1',
    'L_Knee', 'R_Knee', 'Spine2',
    'L_Ankle', 'R_Ankle', 'Spine3',
    'L_Foot', 'R_Foot', 'Neck',
    'L_Collar', 'R_Collar', 'Head',
    'L_Shoulder', 'R_Shoulder',
    'L_Elbow', 'R_Elbow',
    'L_Wrist', 'R_Wrist',
    'L_Hand', 'R_Hand',
]

# ── Skeleton connectivity (parent → child) ──
SKELETON_LINKS = [
    (0, 1), (0, 2), (0, 3),       # Pelvis → hips, spine
    (1, 4), (2, 5), (3, 6),       # Hips → knees, spine2
    (4, 7), (5, 8), (6, 9),       # Knees → ankles, spine3
    (7, 10), (8, 11), (9, 12),    # Ankles → feet, neck
    (12, 13), (12, 14), (12, 15), # Neck → collars, head
    (13, 16), (14, 17),           # Collars → shoulders
    (16, 18), (17, 19),           # Shoulders → elbows
    (18, 20), (19, 21),           # Elbows → wrists
    (20, 22), (21, 23),           # Wrists → hands
]

# Joint colors: left=blue, right=red, center=green
def joint_color(idx):
    name = JOINT_NAMES[idx]
    if name.startswith('L_'):
        return '#3498db'
    elif name.startswith('R_'):
        return '#e74c3c'
    return '#2ecc71'

def link_color(i, j):
    ni, nj = JOINT_NAMES[i], JOINT_NAMES[j]
    if ni.startswith('L_') or nj.startswith('L_'):
        return '#3498db'
    elif ni.startswith('R_') or nj.startswith('R_'):
        return '#e74c3c'
    return '#2ecc71'


def to_plot(pts):
    """Map Y-up data coordinates (..., 3) to Z-up plot coordinates."""
    return pts[..., [0, 2, 1]]


def load_smpl_faces():
    """Load SMPL face topology for mesh rendering."""
    # Prefer pre-extracted .npy file
    here = os.path.dirname(os.path.abspath(__file__))
    dirs = [os.path.join(here, d) for d in ('smpl_model', 'archive/smpl_model', 'smpl_models')]
    npy_candidates = [os.path.join(d, 'smpl_faces.npy') for d in dirs]
    for npy_path in npy_candidates:
        if os.path.exists(npy_path):
            return np.load(npy_path)

    # Fallback: try loading from SMPL pkl
    pkl_candidates = [os.path.join(d, n) for d in dirs for n in ('SMPL_MALE.pkl', 'SMPL_FEMALE.pkl')]
    for path in pkl_candidates:
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    model = pickle.load(f, encoding='latin1')
                if 'f' in model:
                    return np.array(model['f'], dtype=np.int32)
            except Exception as e:
                print(f"  Could not read faces from {path}: {e} (the official SMPL files need chumpy)")
    return None



def visualize(filepath, save_path=None):
    print("Loading SMPL sequence...")
    with open(filepath, 'rb') as f:
        data = pickle.load(f)

    joints = to_plot(data['joints'])       # (n_frames, 24, 3)
    vertices = to_plot(data['vertices'])   # (n_frames, 6890, 3)
    frame_ids = data['frame_ids'] # (n_frames,)
    n_frames = joints.shape[0]
    print(f"  Frames: {n_frames}, Joints: {joints.shape[1]}, Vertices: {vertices.shape[1]}")

    # Try loading SMPL faces for mesh rendering
    faces = load_smpl_faces()
    if faces is not None:
        print(f"  SMPL faces loaded: {faces.shape[0]} triangles")
    else:
        print("  No SMPL faces found, using point cloud for mesh")

    # ── Build figure ──
    fig = plt.figure(num="SCAI-SCI Gait Dataset - SMPL Viewer", figsize=(16, 8))
    fig.suptitle("SCAI-SCI Gait Dataset: 3D SMPL Sequence", fontsize=14, fontweight='bold')

    gs = fig.add_gridspec(3, 2, height_ratios=[2, 2, 0.15])
    ax_skel = fig.add_subplot(gs[0:2, 0], projection='3d')
    ax_mesh = fig.add_subplot(gs[0:2, 1], projection='3d')

    if save_path is None:
        slider_ax = fig.add_subplot(gs[2, :])

    # Subsample vertices for faster rendering (every 10th vertex)
    vert_step = 10

    # ── Drawing functions ──
    def compute_limits(pts):
        """Compute centered axis limits from point cloud."""
        cx = (pts[:, 0].min() + pts[:, 0].max()) / 2
        cy = (pts[:, 1].min() + pts[:, 1].max()) / 2
        cz = (pts[:, 2].min() + pts[:, 2].max()) / 2
        r = max(np.ptp(pts[:, 0]), np.ptp(pts[:, 1]), np.ptp(pts[:, 2])) / 2 + 0.05
        return cx, cy, cz, r

    def draw_skeleton(frame_idx):
        ax_skel.cla()
        j = joints[frame_idx]  # (24, 3)

        # Draw joints
        colors = [joint_color(i) for i in range(24)]
        ax_skel.scatter(j[:, 0], j[:, 1], j[:, 2], c=colors, s=50,
                       edgecolors='black', linewidth=0.5, zorder=5, depthshade=False)

        # Label joints
        for i, name in enumerate(JOINT_NAMES):
            ax_skel.text(j[i, 0], j[i, 1], j[i, 2] + 0.02, name,
                        fontsize=4, ha='center', va='bottom', color='#555')

        # Draw bones
        for (a, b) in SKELETON_LINKS:
            ax_skel.plot([j[a, 0], j[b, 0]], [j[a, 1], j[b, 1]], [j[a, 2], j[b, 2]],
                        color=link_color(a, b), linewidth=2, alpha=0.8)

        cx, cy, cz, r = compute_limits(j)
        ax_skel.set_xlim(cx - r, cx + r)
        ax_skel.set_ylim(cy - r, cy + r)
        ax_skel.set_zlim(cz - r, cz + r)

        fid = frame_ids[frame_idx]
        ax_skel.set_title(f"Skeleton — Frame {fid} ({frame_idx+1}/{n_frames})", fontsize=10)
        ax_skel.set_xlabel("X (progression) [m]", fontsize=8)
        ax_skel.set_ylabel("Z (depth) [m]", fontsize=8)
        ax_skel.set_zlabel("Y (up) [m]", fontsize=8)
        ax_skel.tick_params(labelsize=7)

    def draw_mesh(frame_idx):
        ax_mesh.cla()
        v = vertices[frame_idx]  # (6890, 3)

        if faces is not None:
            # Render mesh with subsampled faces for performance
            face_step = 4
            sub_faces = faces[::face_step]
            tri_verts = v[sub_faces]  # (n_sub_faces, 3, 3)
            mesh = Poly3DCollection(tri_verts, alpha=0.3, facecolor='#aed6f1',
                                    edgecolor='#5dade2', linewidth=0.15)
            ax_mesh.add_collection3d(mesh)
        else:
            # Fallback: denser point cloud
            v_sub = v[::3]
            ax_mesh.scatter(v_sub[:, 0], v_sub[:, 1], v_sub[:, 2],
                           c='#85c1e9', s=2, alpha=0.6)

        # Also draw skeleton on top for reference
        j = joints[frame_idx]
        for (a, b) in SKELETON_LINKS:
            ax_mesh.plot([j[a, 0], j[b, 0]], [j[a, 1], j[b, 1]], [j[a, 2], j[b, 2]],
                        color='#e74c3c', linewidth=1.5, alpha=0.6)

        cx, cy, cz, r = compute_limits(v)
        ax_mesh.set_xlim(cx - r, cx + r)
        ax_mesh.set_ylim(cy - r, cy + r)
        ax_mesh.set_zlim(cz - r, cz + r)

        fid = frame_ids[frame_idx]
        ax_mesh.set_title(f"Mesh — Frame {fid} ({frame_idx+1}/{n_frames})", fontsize=10)
        ax_mesh.set_xlabel("X (progression) [m]", fontsize=8)
        ax_mesh.set_ylabel("Z (depth) [m]", fontsize=8)
        ax_mesh.set_zlabel("Y (up) [m]", fontsize=8)
        ax_mesh.tick_params(labelsize=7)

    def draw_frame(idx):
        draw_skeleton(idx)
        draw_mesh(idx)

    # Draw initial frame (middle)
    init_frame = n_frames // 2
    draw_frame(init_frame)

    # ── Frame slider ──
    if save_path is None:
        slider = Slider(slider_ax, 'Frame', 0, n_frames - 1,
                       valinit=init_frame, valstep=1)

        def update(val):
            draw_frame(int(slider.val))
            fig.canvas.draw_idle()

        slider.on_changed(update)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")
    else:
        plt.show()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="SCAI-SCI Gait Dataset: Visualize an SMPL body model sequence (.pkl).")
    ap.add_argument("sequence", help="path to a *_smpl_sequence.pkl file")
    ap.add_argument("--save", metavar="PNG", help="write the middle frame to a file instead of opening a window")
    args = ap.parse_args()

    if not os.path.exists(args.sequence):
        ap.error(f"file not found: {args.sequence}")

    visualize(args.sequence, args.save)
