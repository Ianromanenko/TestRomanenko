#!/usr/bin/env python3
"""
Parametric generator for the Mitsubishi Pajero center-console armrest
UPPER catch / latch (OEM ref. MR532555, fits NM..NX / Montero 2000-2021).

Geometry v2 — modelled to match the reference photos:
  * mounting plate with two rounded screw ears (countersunk holes)
  * wedge-shaped central block with a hole in its sloped face
  * wide tapered paddle (the grip lever) tilted up from the plate edge
  * J-hook under the paddle that engages the lid striker

Dimensions are derived from photo proportions; fit-critical values are
parameters below — verify HOLE_SPACING and the hook geometry against the
original part with calipers before a final print.

Output: pajero_upper_latch.stl / .3mf + preview renders.
"""
import numpy as np
import trimesh
from trimesh.creation import box, cylinder

# ----------------------------------------------------------------------
# PARAMETERS (mm)
# ----------------------------------------------------------------------
# Mounting plate (the part screwed to the console, Z-up, top face +Z)
PLATE_L      = 70.0    # overall width (X)
PLATE_D      = 20.0    # depth (Y), paddle hangs off the Y=0 edge
PLATE_T      = 3.5     # thickness
PLATE_R      = 6.0     # corner radius

# Screw holes in the ears
HOLE_SPACING = 56.0    # centre-to-centre (X)
HOLE_Y       = 12.0    # hole centre from the front (paddle) edge
HOLE_DIA     = 5.0
CSK_DIA      = 9.6
CSK_DEPTH    = 2.2

# Central wedge block (between the ears, protrudes past the back edge)
BLOCK_W      = 24.0    # X
BLOCK_D      = 13.0    # Y, sits from Y=BLOCK_Y0
BLOCK_Y0     = 8.0     # back end overhangs the plate rear edge slightly
BLOCK_H_BACK = 13.5    # top height at the back (Z, from plate bottom)
BLOCK_H_FRONT= 9.0     # top height at the front (sloped face)
BLOCK_R      = 2.0
BLOCK_HOLE_D = 5.0     # hole in the sloped face

# Paddle (grip lever)
PAD_W_ROOT   = 63.0    # width at the hinge edge
PAD_W_TIP    = 54.0    # width at the free end
PAD_LEN      = 32.0    # length along the paddle plane
PAD_T        = 3.6     # thickness
PAD_R        = 10.0    # corner radius (big, rounded tip like the photos)
PAD_ANGLE    = 45.0    # tilt above the plate plane, degrees
PAD_ROOT_Y   = 1.5     # embed of the root edge into the plate front
PAD_ROOT_Z   = 2.2     # height of the hinge line

# Catch hook: hangs from the paddle underside, curls back toward the plate
# (visible gap between the tilted paddle and the hook bar, like photo 1)
HOOK_W       = 14.0
HOOK_BAR_Y   = -7.0    # Y centre of the descending bar
HOOK_BAR_T   = 3.2     # bar thickness (Y)
HOOK_BOT_Z   = 1.2     # bottom of the hook
HOOK_LIP_LEN = 8.0     # lip length toward the plate (+Y)
HOOK_LIP_T   = 3.0     # lip thickness (Z)

SEG = 96


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def rounded_plate(length, width, thick, r, segments=SEG):
    """Flat prism with rounded vertical corners, base at z=0, centred XY."""
    hx, hy = length / 2 - r, width / 2 - r
    parts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = cylinder(radius=r, height=thick, sections=segments)
            c.apply_translation((sx * hx, sy * hy, thick / 2))
            parts.append(c)
    return trimesh.util.concatenate(parts).convex_hull


def rot_x(mesh, deg, point=(0, 0, 0)):
    mesh.apply_transform(trimesh.transformations.rotation_matrix(
        np.radians(deg), [1, 0, 0], point))
    return mesh


def countersunk_hole(x, y):
    from trimesh.creation import cone
    drill = cylinder(radius=HOLE_DIA / 2, height=PLATE_T + 8, sections=SEG)
    drill.apply_translation((x, y, PLATE_T / 2))
    csk = cone(radius=CSK_DIA / 2, height=CSK_DEPTH, sections=SEG)
    csk.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    csk.apply_translation((x, y, PLATE_T + 0.01))
    return trimesh.util.concatenate([drill, csk])


# ----------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------
def build():
    # --- mounting plate, front edge at Y=0, extends to Y=PLATE_D ---
    plate = rounded_plate(PLATE_L, PLATE_D, PLATE_T, PLATE_R)
    plate.apply_translation((0, PLATE_D / 2, 0))
    holes = trimesh.util.concatenate([
        countersunk_hole(+HOLE_SPACING / 2, HOLE_Y),
        countersunk_hole(-HOLE_SPACING / 2, HOLE_Y)])
    plate = plate.difference(holes)

    # --- central wedge block: high at the back, sloping down to the front ---
    from shapely.geometry import Polygon
    slope_deg = np.degrees(np.arctan2(BLOCK_H_BACK - BLOCK_H_FRONT, BLOCK_D))
    y0, y1 = BLOCK_Y0, BLOCK_Y0 + BLOCK_D
    prof = Polygon([(y0, 0), (y1, 0), (y1, BLOCK_H_BACK), (y0, BLOCK_H_FRONT)])
    blk = trimesh.creation.extrude_polygon(prof, BLOCK_W)
    # extruded along Z; remap so width goes along X: (p, q, e) -> (e, p, q)
    T = np.array([[0, 0, 1, -BLOCK_W / 2],
                  [1, 0, 0, 0],
                  [0, 1, 0, 0],
                  [0, 0, 0, 1.0]])
    blk.apply_transform(T)
    # hole perpendicular to the sloped face, centred on it
    face_c = np.array([0, BLOCK_Y0 + BLOCK_D / 2,
                       (BLOCK_H_BACK + BLOCK_H_FRONT) / 2])
    n = np.array([0, -np.sin(np.radians(slope_deg)), np.cos(np.radians(slope_deg))])
    drill = cylinder(radius=BLOCK_HOLE_D / 2, height=10, sections=SEG)
    drill.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], n))
    drill.apply_translation(face_c + n * 1.0)
    blk = blk.difference(drill)

    # --- paddle: tapered rounded plate, tilted up from the front edge ---
    pad = rounded_plate(PAD_W_ROOT, PAD_LEN, PAD_T, PAD_R)
    v = pad.vertices.copy()
    # taper: full width at root edge (y=+PAD_LEN/2), narrower at tip
    t = (PAD_LEN / 2 - v[:, 1]) / PAD_LEN          # 0 at root, 1 at tip
    v[:, 0] *= (1 - t * (1 - PAD_W_TIP / PAD_W_ROOT))
    pad.vertices = v
    pad.apply_translation((0, -PAD_LEN / 2, -PAD_T / 2))  # root edge at Y=0, centred Z
    rot_x(pad, -PAD_ANGLE)                                # tip goes -Y and +Z
    pad.apply_translation((0, PAD_ROOT_Y, PAD_ROOT_Z + PAD_T / 2))

    # --- catch hook: bar descends from the paddle underside, lip curls
    #     back toward the plate — leaves a visible gap like in photo 1 ---
    ang = np.radians(PAD_ANGLE)
    pad_under = PAD_ROOT_Z + (PAD_ROOT_Y - HOOK_BAR_Y) * np.tan(ang)
    bar = box((HOOK_W, HOOK_BAR_T, pad_under - HOOK_BOT_Z + 1.5))
    bar.apply_translation((0, HOOK_BAR_Y,
                           (pad_under + 1.5 + HOOK_BOT_Z) / 2))
    lip = box((HOOK_W, HOOK_LIP_LEN, HOOK_LIP_T))
    lip.apply_translation((0, HOOK_BAR_Y - HOOK_BAR_T / 2 + HOOK_LIP_LEN / 2,
                           HOOK_BOT_Z + HOOK_LIP_T / 2))

    mesh = trimesh.boolean.union([plate, blk, pad, bar, lip])
    mesh.merge_vertices()
    mesh.fix_normals()
    return mesh


def render(mesh, path, views):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(6 * len(views), 6))
    for i, (elev, azim, title) in enumerate(views, 1):
        ax = fig.add_subplot(1, len(views), i, projection="3d")
        coll = Poly3DCollection(mesh.triangles, facecolor=(0.2, 0.2, 0.22),
                                edgecolor=(0.05, 0.05, 0.05), linewidths=0.1)
        ax.add_collection3d(coll)
        b, c = mesh.bounds, mesh.centroid
        span = (b[1] - b[0]).max() / 2 * 1.05
        ax.set_xlim(c[0] - span, c[0] + span)
        ax.set_ylim(c[1] - span, c[1] + span)
        ax.set_zlim(c[2] - span, c[2] + span)
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(title)
        ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(path, dpi=110)
    print("wrote", path)


if __name__ == "__main__":
    m = build()
    print("watertight:", m.is_watertight)
    bb = m.bounds
    print("bbox (mm): %.1f x %.1f x %.1f" % tuple(bb[1] - bb[0]))
    m.export("pajero_upper_latch.stl")
    ex = m.copy()
    ex.apply_translation(-ex.centroid)
    ex.apply_translation((0, 0, ex.centroid[2] - ex.bounds[0][2]))
    ex.units = "mm"
    ex.export("pajero_upper_latch.3mf")
    print("wrote STL + 3MF")
    render(m, "preview.png",
           [(28, -55, "angled (like photo 1)"),
            (85, -90, "front/top (like photo 2)"),
            (5, -90, "side profile")])
