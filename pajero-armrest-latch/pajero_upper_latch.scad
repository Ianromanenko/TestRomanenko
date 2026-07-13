// ---------------------------------------------------------------------------
// Mitsubishi Pajero center-console armrest UPPER catch / latch  (OEM MR532555)
//
// NOTE ON SOURCE OF TRUTH
// The printable geometry (v3) is generated and VERIFIED by generate_latch.py
// (Python + trimesh): the domed "hood" uses a boolean intersection that is
// checked for watertightness and against OEM-anchored dimensions on every run.
// This environment has no OpenSCAD renderer, so rather than ship an unverified
// port, the authoritative model lives in the Python generator and the exported
// STL/3MF files. The block below documents the parameters so you can tweak and
// regenerate:  python3 generate_latch.py
//
// Real OEM part (from research): ~47 x 34 x 29 mm, hole-to-hole ~35 mm, ~15 g.
// ---------------------------------------------------------------------------

/* [Reference parameters — edit in generate_latch.py] */
MIRROR       = false;  // flip long/short screw ear if the part comes out reversed

// Mounting flange
FLANGE_D     = 16.0;   // depth (Y)
FLANGE_T     = 3.5;    // thickness
FLANGE_R     = 3.0;    // corner radius
EAR_LONG     = 6.0;    // overhang past hole (long side)
EAR_SHORT    = 6.0;    // overhang past hole (short side)

// Countersunk screw holes  (width = HOLE_SPACING + EAR_LONG + EAR_SHORT ~= 47)
HOLE_SPACING = 35.0;   // centre-to-centre (X)
HOLE_Y       = 8.0;    // from the flange back edge (Y)
HOLE_DIA     = 4.6;
CSK_DIA      = 8.0;
CSK_DEPTH    = 2.0;

// Central boss (with hole)
BOSS_W       = 12.0;
BOSS_D       = 9.0;
BOSS_H       = 5.0;
BOSS_HOLE_D  = 4.5;

// Domed hood
HOOD_W       = 34.0;   // width (X)
HOOD_H       = 30.0;   // height along its plane
HOOD_TH      = 12.0;   // thickness
HOOD_R       = 7.0;    // corner radius
HOOD_TILT    = 16.0;   // back-tilt, degrees
HOOD_DOME_R  = 58.0;   // front-face bulge radius
HOOD_TAPER   = 0.82;   // bottom/top width

// Hook / catch
HOOK_W       = 12.0;
HOOK_BAR_Y   = 4.0;
HOOK_BAR_T   = 3.0;
HOOK_LIP_LEN = 6.5;
HOOK_LIP_T   = 2.6;

// Rough placeholder so this file still previews *something* in OpenSCAD.
// (Not the real geometry — see generate_latch.py / the exported STL.)
color("gray") {
    translate([0, FLANGE_D/2, FLANGE_T/2])
        cube([HOLE_SPACING + EAR_LONG + EAR_SHORT, FLANGE_D, FLANGE_T], center=true);
    translate([0, 6, FLANGE_T])
        rotate([HOOD_TILT, 0, 0])
            resize([HOOD_W, HOOD_TH, HOOD_H])
                translate([0,0,0.5]) sphere(d=HOOD_H);
}
