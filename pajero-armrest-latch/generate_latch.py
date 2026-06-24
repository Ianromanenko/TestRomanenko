#!/usr/bin/env python3
"""
Parametric generator for the Mitsubishi Pajero center-console armrest
UPPER catch / latch (OEM ref. MR532555, fits NM..NX / Montero 2000-2021).

The real OEM part dimensions are not published, so the model below is
dimensioned from the reference photos (photo proportions + standard trim
self-tapper sizes). Every fit-critical value is a named constant at the
top so it can be tuned after a test print and a caliper check of the
original part.

Output: pajero_upper_latch.stl  (+ preview.png)

Requires: trimesh, manifold3d, numpy, matplotlib
"""
import numpy as np
import trimesh
from trimesh.creation import box, cylinder, cone

# ----------------------------------------------------------------------
# PARAMETERS (mm)  -- measure the original and adjust these if needed
# ----------------------------------------------------------------------
# Mounting base plate (flange)
PLATE_L      = 70.0   # length, along the screw-hole axis (X)
PLATE_W      = 25.0   # width / depth (Y)
PLATE_T      = 4.5    # thickness (Z)
PLATE_FILLET = 4.0    # corner radius of the plate

# Screw holes (countersunk, for ~M5 self-tappers)
HOLE_SPACING = 56.0   # centre-to-centre distance between the two holes
HOLE_DIA     = 5.0    # through-hole diameter
CSK_DIA      = 9.6    # countersink top diameter
CSK_DEPTH    = 2.6    # countersink depth from the top face

# Central catch body (the block rising from the plate)
BODY_W       = 22.0   # X
BODY_D       = 15.0   # Y
BODY_H       = 13.0   # height above the plate (Z)
BODY_FILLET  = 2.5

# Top button / cap with the small hole seen in the photos
CAP_W        = 16.0
CAP_D        = 12.0
CAP_H        = 4.0
CAP_HOLE_DIA = 3.2

# Forward hook (the lever that engages the lid striker)
HOOK_W       = 14.0   # X width of the hook
HOOK_ARM_T   = 5.0    # thickness of the horizontal arm (Z)
HOOK_REACH   = 12.0   # how far it projects forward (+Y) past the body
HOOK_LIP_H   = 7.0    # downward catching lip height
HOOK_LIP_T   = 4.0    # lip thickness (Y)
HOOK_Z       = 6.0    # height of the underside of the arm above plate

SEG = 96  # cylinder facet count

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def rounded_plate(length, width, thick, r, segments=SEG):
    """A flat prism with rounded vertical corners (convex hull of 4 cyls)."""
    hx, hy = length / 2 - r, width / 2 - r
    parts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = cylinder(radius=r, height=thick, sections=segments)
            c.apply_translation((sx * hx, sy * hy, thick / 2))
            parts.append(c)
    return trimesh.util.concatenate(parts).convex_hull


def rounded_box(w, d, h, r, segments=48):
    """Box with rounded vertical edges, base at z=0, centred in X/Y."""
    return rounded_plate(w, d, h, r, segments)


def countersunk_hole(x, y):
    """Through hole + countersink cutter centred at (x, y), drilled in -Z..+Z."""
    drill = cylinder(radius=HOLE_DIA / 2, height=PLATE_T + 6, sections=SEG)
    drill.apply_translation((x, y, PLATE_T / 2))
    # countersink: cone wide at the top face, narrowing downward
    csk = cone(radius=CSK_DIA / 2, height=CSK_DEPTH, sections=SEG)
    # trimesh cone apex is at +height; flip so wide rim is at the top face
    csk.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    csk.apply_translation((x, y, PLATE_T))
    return trimesh.util.concatenate([drill, csk])


# ----------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------
def build():
    # --- base plate with countersunk holes ---
    plate = rounded_plate(PLATE_L, PLATE_W, PLATE_T, PLATE_FILLET)
    cutters = [countersunk_hole(+HOLE_SPACING / 2, 0),
               countersunk_hole(-HOLE_SPACING / 2, 0)]
    plate = plate.difference(trimesh.util.concatenate(cutters))

    # --- central catch body ---
    body = rounded_box(BODY_W, BODY_D, BODY_H, BODY_FILLET)
    body.apply_translation((0, 0, PLATE_T))

    # --- top cap / button with small hole ---
    cap = rounded_box(CAP_W, CAP_D, CAP_H, 2.0)
    cap.apply_translation((0, 0, PLATE_T + BODY_H))
    cap_hole = cylinder(radius=CAP_HOLE_DIA / 2, height=CAP_H + 4, sections=SEG)
    cap_hole.apply_translation((0, 0, PLATE_T + BODY_H + CAP_H / 2))
    cap = cap.difference(cap_hole)

    # --- forward hook (horizontal arm + downward catching lip) ---
    arm_len = BODY_D / 2 + HOOK_REACH
    arm = box((HOOK_W, arm_len, HOOK_ARM_T))
    arm.apply_translation((0, arm_len / 2, PLATE_T + HOOK_Z + HOOK_ARM_T / 2))

    lip = box((HOOK_W, HOOK_LIP_T, HOOK_LIP_H))
    lip_y = BODY_D / 2 + HOOK_REACH - HOOK_LIP_T / 2
    lip.apply_translation((0, lip_y,
                           PLATE_T + HOOK_Z + HOOK_ARM_T / 2 - HOOK_LIP_H / 2 + 0.5))

    # rounded thumb pad on the front-top of the body for a nicer look/feel
    pad = cylinder(radius=HOOK_W / 2, height=BODY_D * 0.7, sections=SEG)
    pad.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    pad.apply_translation((0, BODY_D / 2 * 0.4, PLATE_T + BODY_H))

    solids = [plate, body, cap, arm, lip, pad]
    mesh = trimesh.boolean.union(solids)

    # clean up
    mesh.merge_vertices()
    mesh.remove_duplicate_faces() if hasattr(mesh, "remove_duplicate_faces") else None
    mesh.fix_normals()
    return mesh


def preview(mesh, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(7, 6))
    ax = fig.add_subplot(111, projection="3d")
    tris = mesh.triangles
    coll = Poly3DCollection(tris, alpha=1.0, facecolor=(0.18, 0.18, 0.2),
                            edgecolor=(0.05, 0.05, 0.05), linewidths=0.15)
    ax.add_collection3d(coll)
    b = mesh.bounds
    ctr = mesh.centroid
    span = (b[1] - b[0]).max() / 2 * 1.1
    ax.set_xlim(ctr[0] - span, ctr[0] + span)
    ax.set_ylim(ctr[1] - span, ctr[1] + span)
    ax.set_zlim(ctr[2] - span, ctr[2] + span)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=22, azim=-58)
    ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
    ax.set_title("Pajero upper console latch (MR532555) — replica")
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    print(f"wrote {path}")


if __name__ == "__main__":
    m = build()
    print("watertight:", m.is_watertight)
    print("volume (mm^3): %.1f" % m.volume)
    bb = m.bounds
    print("bounding box (mm): %.1f x %.1f x %.1f" %
          tuple(bb[1] - bb[0]))
    m.export("pajero_upper_latch.stl")
    print("wrote pajero_upper_latch.stl")
    preview(m, "preview.png")
