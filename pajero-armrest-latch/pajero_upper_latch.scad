// Mitsubishi Pajero center-console armrest UPPER catch / latch
// OEM ref. MR532555 (fits Pajero/Montero NM..NX, 2000-2021)
//
// Parametric replica dimensioned from reference photos. The OEM factory
// dimensions are not published, so verify the fit-critical values below
// (HOLE_SPACING, plate footprint, hook geometry) against the original
// part with calipers and adjust before a final print.
//
// Units: millimetres. Render: F6, then Export as STL.

$fn = 96;

/* [Base plate] */
PLATE_L      = 70.0;   // length along the screw-hole axis (X)
PLATE_W      = 25.0;   // width / depth (Y)
PLATE_T      = 4.5;    // thickness (Z)
PLATE_FILLET = 4.0;

/* [Screw holes - countersunk, ~M5 self-tappers] */
HOLE_SPACING = 56.0;   // centre-to-centre
HOLE_DIA     = 5.0;
CSK_DIA      = 9.6;
CSK_DEPTH    = 2.6;

/* [Central catch body] */
BODY_W      = 22.0;
BODY_D      = 15.0;
BODY_H      = 13.0;
BODY_FILLET = 2.5;

/* [Top button / cap] */
CAP_W        = 16.0;
CAP_D        = 12.0;
CAP_H        = 4.0;
CAP_HOLE_DIA = 3.2;

/* [Forward hook] */
HOOK_W     = 14.0;
HOOK_ARM_T = 5.0;
HOOK_REACH = 12.0;
HOOK_LIP_H = 7.0;
HOOK_LIP_T = 4.0;
HOOK_Z     = 6.0;

module rrect(l, w, h, r) {
    linear_extrude(height = h)
        offset(r = r) offset(r = -r)
            square([l, w], center = true);
}

module countersink(x) {
    translate([x, 0, -1])
        cylinder(d = HOLE_DIA, h = PLATE_T + 2);
    translate([x, 0, PLATE_T - CSK_DEPTH])
        cylinder(d1 = HOLE_DIA, d2 = CSK_DIA, h = CSK_DEPTH + 0.01);
}

module latch() {
    union() {
        // base plate with countersunk holes
        difference() {
            rrect(PLATE_L, PLATE_W, PLATE_T, PLATE_FILLET);
            countersink( HOLE_SPACING / 2);
            countersink(-HOLE_SPACING / 2);
        }
        // central catch body
        translate([0, 0, PLATE_T])
            rrect(BODY_W, BODY_D, BODY_H, BODY_FILLET);
        // top cap with small hole
        translate([0, 0, PLATE_T + BODY_H])
            difference() {
                rrect(CAP_W, CAP_D, CAP_H, 2.0);
                translate([0, 0, -1])
                    cylinder(d = CAP_HOLE_DIA, h = CAP_H + 2);
            }
        // rounded thumb pad
        translate([0, BODY_D * 0.2, PLATE_T + BODY_H])
            rotate([90, 0, 0])
                cylinder(d = HOOK_W, h = BODY_D * 0.7, center = true);
        // forward hook arm
        translate([-HOOK_W/2, 0, PLATE_T + HOOK_Z])
            cube([HOOK_W, BODY_D/2 + HOOK_REACH, HOOK_ARM_T]);
        // downward catching lip
        translate([-HOOK_W/2,
                   BODY_D/2 + HOOK_REACH - HOOK_LIP_T,
                   PLATE_T + HOOK_Z - HOOK_LIP_H + HOOK_ARM_T])
            cube([HOOK_W, HOOK_LIP_T, HOOK_LIP_H]);
    }
}

latch();
