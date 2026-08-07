#!/usr/bin/env python3
"""
Parametric generator (v3) for the Mitsubishi Pajero center-console armrest
UPPER catch / latch (OEM ref. MR532555, fits NM..NX / Montero 2000-2021).

v3 is re-derived from scratch against the user's reference photos, matching:
  C1 thin mounting flange (flat strip)
  C2 two countersunk screw holes near the flange ends
  C3 central raised square boss with a hole on top
  C4 large rounded/domed textured "hood" body rising from the flange edge
  C5 hood reads trapezoidal/rounded from the front
  C6 hook / catch on the underside near the boss
  C7 watertight, mm-scale, flange-on-bed printable

Fit-critical values are parameters. MIRROR flips the (optionally) asymmetric
ears. Outputs STL + 3MF (A and mirror B) and photo-angle previews.
"""
import numpy as np
import trimesh
from trimesh.creation import box, cylinder, cone
from shapely.geometry import Polygon

# ----------------------------------------------------------------------
# PARAMETERS (mm)
# ----------------------------------------------------------------------
MIRROR       = False

# --- Scale anchored to the real OEM part (research): MR532555 upper catch
#     is ~47 x 34 x 29 mm, hole-to-hole ~35 mm, ~15 g (black plastic). ---

# Mounting flange (flat strip, Z-up, top face +Z)
FLANGE_D     = 16.0    # depth (Y); hood cantilevers off the +Y edge
FLANGE_T     = 3.5     # thickness
FLANGE_R     = 3.0     # corner radius
EAR_LONG     = 6.0     # plate overhang past hole on the long side
EAR_SHORT    = 6.0     # ... short side (equal by default -> symmetric)

# Countersunk screw holes
HOLE_SPACING = 35.0    # centre-to-centre (X)  -> width ~47 mm with ears
HOLE_Y       = 8.0     # from the flange back edge (Y)
HOLE_DIA     = 4.6
CSK_DIA      = 8.0
CSK_DEPTH    = 2.0

# Central square boss with a hole on top
BOSS_W       = 12.0
BOSS_D       = 9.0
BOSS_H       = 5.0     # above the flange top
BOSS_R       = 1.6
BOSS_HOLE_D  = 4.5

# Domed "hood" body (the big rounded grip that rises off the flange)
HOOD_W       = 34.0    # width (X) — leaves the screw ears exposed
HOOD_H       = 30.0    # height along its own plane
HOOD_TH      = 12.0    # thickness (through the shield)
HOOD_R       = 7.0     # outline corner radius
HOOD_TILT    = 16.0    # tilt back from vertical, degrees
HOOD_DOME_R  = 58.0    # front-face bulge radius (bigger = flatter)
HOOD_TAPER   = 0.82    # bottom width / top width (trapezoid)

# Hook / catch under the hood, curling back toward the flange
HOOK_W       = 12.0
HOOK_BAR_Y   = 4.0     # bar centre (Y), in front of the boss
HOOK_BAR_T   = 3.0
HOOK_BOT_Z   = 0.9
HOOK_LIP_LEN = 6.5
HOOK_LIP_T   = 2.6

SEG = 96


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def rounded_plate_x(x_min, x_max, y_min, y_max, thick, r, segments=SEG):
    """Rounded prism spanning [x_min,x_max] x [y_min,y_max], base at z=0."""
    parts = []
    for cx in (x_min + r, x_max - r):
        for cy in (y_min + r, y_max - r):
            c = cylinder(radius=r, height=thick, sections=segments)
            c.apply_translation((cx, cy, thick / 2))
            parts.append(c)
    return trimesh.util.concatenate(parts).convex_hull


def rounded_box(w, d, h, r, segments=48):
    return rounded_plate_x(-w / 2, w / 2, -d / 2, d / 2, h, r, segments)


def countersunk_hole(x, y):
    drill = cylinder(radius=HOLE_DIA / 2, height=FLANGE_T + 8, sections=SEG)
    drill.apply_translation((x, y, FLANGE_T / 2))
    csk = cone(radius=CSK_DIA / 2, height=CSK_DEPTH, sections=SEG)
    csk.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    csk.apply_translation((x, y, FLANGE_T + 0.01))
    return trimesh.util.concatenate([drill, csk])


def rot_x(mesh, deg, point=(0, 0, 0)):
    mesh.apply_transform(trimesh.transformations.rotation_matrix(
        np.radians(deg), [1, 0, 0], point))
    return mesh


def build_hood():
    """A rounded trapezoidal shield, front face domed, built lying then tilted.
    Local frame: X width, Y through-thickness, Z height; base at Z=0."""
    # trapezoid outline in X-Z, extruded through Y
    wt, wb = HOOD_W / 2, HOOD_W / 2 * HOOD_TAPER
    r = HOOD_R
    # rounded trapezoid via hull of 4 corner circles (in X-Z plane)
    circ = []
    for (cx, cz) in [(-wb + r, r), (wb - r, r),
                     (-wt + r, HOOD_H - r), (wt - r, HOOD_H - r)]:
        c = cylinder(radius=r, height=HOOD_TH, sections=64)
        c.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [1, 0, 0]))
        c.apply_translation((cx, 0, cz))
        circ.append(c)
    shield = trimesh.util.concatenate(circ).convex_hull
    # dome the front (+Y) face: subtract everything outside a big cylinder
    dome = cylinder(radius=HOOD_DOME_R, height=HOOD_W + 20, sections=192)
    dome.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    dome.apply_translation((0, HOOD_TH / 2 - HOOD_DOME_R, HOOD_H / 2))
    shield = shield.intersection(dome)
    return shield


# ----------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------
def build():
    # --- flange (asymmetric-capable) with countersunk holes ---
    x_left = -(HOLE_SPACING / 2 + EAR_LONG)
    x_right = (HOLE_SPACING / 2 + EAR_SHORT)
    flange = rounded_plate_x(x_left, x_right, 0, FLANGE_D, FLANGE_T, FLANGE_R)
    holes = trimesh.util.concatenate([
        countersunk_hole(+HOLE_SPACING / 2, HOLE_Y),
        countersunk_hole(-HOLE_SPACING / 2, HOLE_Y)])
    flange = flange.difference(holes)

    # --- central boss with a hole, seated behind the hood (visible) ---
    boss_y = FLANGE_D - BOSS_D / 2 - 1.0
    boss = rounded_box(BOSS_W, BOSS_D, BOSS_H, BOSS_R)
    boss.apply_translation((0, boss_y, FLANGE_T))
    bhole = cylinder(radius=BOSS_HOLE_D / 2, height=BOSS_H + 4, sections=SEG)
    bhole.apply_translation((0, boss_y, FLANGE_T + BOSS_H - 2))
    boss = boss.difference(bhole)

    # --- domed hood: already built vertical (height along Z); tilt back a
    #     little and seat its base on the front part of the flange ---
    hood = build_hood()
    rot_x(hood, HOOD_TILT)                 # lean back over the flange
    hood.apply_translation((0, 3.0, FLANGE_T - 0.5))

    # --- hook / catch under the hood ---
    bar_top = FLANGE_T + 9.0
    bar = box((HOOK_W, HOOK_BAR_T, bar_top - HOOK_BOT_Z))
    bar.apply_translation((0, HOOK_BAR_Y, (bar_top + HOOK_BOT_Z) / 2))
    lip = box((HOOK_W, HOOK_LIP_LEN, HOOK_LIP_T))
    lip.apply_translation((0, HOOK_BAR_Y - HOOK_BAR_T / 2 + HOOK_LIP_LEN / 2,
                           HOOK_BOT_Z + HOOK_LIP_T / 2))

    mesh = trimesh.boolean.union([flange, boss, hood, bar, lip])
    if MIRROR:
        mesh.apply_scale((-1, 1, 1))
    mesh.merge_vertices()
    mesh.fix_normals()
    return mesh


# ----------------------------------------------------------------------
# Render harness (mimics the three reference photo angles)
# ----------------------------------------------------------------------
def render(mesh, path, views, ncols=3):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(5.2 * ncols, 5))
    for i, (elev, azim, title) in enumerate(views, 1):
        ax = fig.add_subplot(1, ncols, i, projection="3d")
        ax.add_collection3d(Poly3DCollection(
            mesh.triangles, facecolor=(0.17, 0.17, 0.19),
            edgecolor=(0.05, 0.05, 0.05), linewidths=0.08))
        b, c = mesh.bounds, mesh.centroid
        s = (b[1] - b[0]).max() / 2 * 1.05
        ax.set_xlim(c[0] - s, c[0] + s)
        ax.set_ylim(c[1] - s, c[1] + s)
        ax.set_zlim(c[2] - s, c[2] + s)
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(title, fontsize=12)
        ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(path, dpi=115)
    print("wrote", path)


def export_on_bed(mesh, stem):
    mesh.export(stem + ".stl")
    ex = mesh.copy()
    ex.apply_translation((-(ex.bounds[0][0] + ex.bounds[1][0]) / 2,
                          -(ex.bounds[0][1] + ex.bounds[1][1]) / 2,
                          -ex.bounds[0][2]))
    ex.units = "mm"
    ex.export(stem + ".3mf")


def self_check(mesh):
    """Quantitative acceptance checks -> printed report."""
    bb = mesh.bounds
    dims = bb[1] - bb[0]
    vol = mesh.volume / 1000.0
    # targets from OEM research: ~47 x 34 x 29 mm, ~15 g
    checks = {
        "watertight": mesh.is_watertight,
        "winding_consistent": mesh.is_winding_consistent,
        "width 42-52mm (OEM ~47)": 42 <= dims[0] <= 52,
        "depth 24-34mm (OEM ~29)": 24 <= dims[1] <= 34,
        "height 28-38mm (OEM ~34)": 28 <= dims[2] <= 38,
        "mass 8-24g PETG (OEM ~15)": 8 <= vol * 1.27 <= 24,
    }
    print("=== SELF-CHECK ===")
    print("bbox mm: %.1f x %.1f x %.1f | vol %.1f cm3 | ~%.1f g PETG"
          % (*dims, vol, vol * 1.27))
    for k, v in checks.items():
        print(("  [PASS] " if v else "  [FAIL] ") + k)
    return all(checks.values())


if __name__ == "__main__":
    import generate_latch as G
    G.MIRROR = False
    m = build()
    ok = self_check(m)
    export_on_bed(m, "pajero_upper_latch_A")
    export_on_bed(m, "pajero_upper_latch")
    G.MIRROR = True
    mb = build()
    export_on_bed(mb, "pajero_upper_latch_B_mirror")
    render(m, "preview.png",
           [(22, -60, "3/4 view (cf IMG_3295)"),
            (12, -90, "front (cf IMG_3294)"),
            (6, 0, "side profile")])
    print("ALL CHECKS PASS" if ok else "*** CHECKS FAILED ***")
