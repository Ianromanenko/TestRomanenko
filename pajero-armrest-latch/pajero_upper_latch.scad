// Mitsubishi Pajero center-console armrest UPPER catch / latch
// OEM ref. MR532555 (fits Pajero/Montero NM..NX, 2000-2021)
//
// Geometry v2, matched to the reference photos:
//   * mounting plate with two countersunk screw holes
//   * wedge-shaped central block with a hole in its sloped face
//   * wide tapered paddle (grip lever) tilted up from the plate edge
//   * catch hook hanging from the paddle underside
//
// OEM dimensions are unpublished; verify HOLE_SPACING and the hook
// against the original with calipers, then re-export.
// Units: mm. Render: F6, then Export as STL.

$fn = 96;

/* [Mounting plate] */
PLATE_L      = 70.0;
PLATE_D      = 20.0;
PLATE_T      = 3.5;
PLATE_R      = 6.0;

/* [Screw holes] */
HOLE_SPACING = 56.0;
HOLE_Y       = 12.0;
HOLE_DIA     = 5.0;
CSK_DIA      = 9.6;
CSK_DEPTH    = 2.2;

/* [Central wedge block] */
BLOCK_W       = 24.0;
BLOCK_D       = 13.0;
BLOCK_Y0      = 8.0;
BLOCK_H_BACK  = 13.5;
BLOCK_H_FRONT = 9.0;
BLOCK_R       = 2.0;
BLOCK_HOLE_D  = 5.0;

/* [Paddle] */
PAD_W_ROOT = 63.0;
PAD_W_TIP  = 54.0;
PAD_LEN    = 32.0;
PAD_T      = 3.6;
PAD_R      = 10.0;
PAD_ANGLE  = 45.0;
PAD_ROOT_Y = 1.5;
PAD_ROOT_Z = 2.2;

/* [Catch hook] */
HOOK_W       = 14.0;
HOOK_BAR_Y   = -7.0;
HOOK_BAR_T   = 3.2;
HOOK_BOT_Z   = 1.2;
HOOK_LIP_LEN = 8.0;
HOOK_LIP_T   = 3.0;

module rrect(l, w, h, r) {
    linear_extrude(height = h)
        offset(r = r) offset(r = -r)
            square([l, w], center = true);
}

module countersink(x) {
    translate([x, HOLE_Y, -1])
        cylinder(d = HOLE_DIA, h = PLATE_T + 2);
    translate([x, HOLE_Y, PLATE_T - CSK_DEPTH])
        cylinder(d1 = HOLE_DIA, d2 = CSK_DIA, h = CSK_DEPTH + 0.01);
}

slope = atan2(BLOCK_H_BACK - BLOCK_H_FRONT, BLOCK_D);

module latch() {
    union() {
        // mounting plate, front edge at Y=0
        difference() {
            translate([0, PLATE_D/2, 0])
                rrect(PLATE_L, PLATE_D, PLATE_T, PLATE_R);
            countersink( HOLE_SPACING/2);
            countersink(-HOLE_SPACING/2);
        }
        // wedge block: high at the back, sloping down toward the paddle,
        // with a hole perpendicular to the sloped face
        difference() {
            rotate([90, 0, 90])
                linear_extrude(height = BLOCK_W, center = true)
                    polygon([[BLOCK_Y0, 0], [BLOCK_Y0 + BLOCK_D, 0],
                             [BLOCK_Y0 + BLOCK_D, BLOCK_H_BACK],
                             [BLOCK_Y0, BLOCK_H_FRONT]]);
            translate([0, BLOCK_Y0 + BLOCK_D/2, (BLOCK_H_BACK + BLOCK_H_FRONT)/2])
                rotate([slope, 0, 0])
                    cylinder(d = BLOCK_HOLE_D, h = 14, center = true);
        }
        // paddle: tapered, tilted up from the front edge
        translate([0, PAD_ROOT_Y, PAD_ROOT_Z])
            rotate([-PAD_ANGLE, 0, 0])         // tip goes -Y and +Z
                translate([0, -PAD_LEN, 0])
                    linear_extrude(height = PAD_T)
                        polygon_paddle();
        // hook: bar descending from the paddle underside + lip toward plate
        translate([-HOOK_W/2, HOOK_BAR_Y - HOOK_BAR_T/2, HOOK_BOT_Z])
            cube([HOOK_W, HOOK_BAR_T,
                  PAD_ROOT_Z + (PAD_ROOT_Y - HOOK_BAR_Y)*tan(PAD_ANGLE) + 1.5 - HOOK_BOT_Z]);
        translate([-HOOK_W/2, HOOK_BAR_Y - HOOK_BAR_T/2, HOOK_BOT_Z])
            cube([HOOK_W, HOOK_LIP_LEN, HOOK_LIP_T]);
    }
}

// 2D outline of the paddle: rounded trapezoid, root edge at y=PAD_LEN
module polygon_paddle() {
    hull() {
        for (sx = [-1, 1]) {
            translate([sx*(PAD_W_ROOT/2 - PAD_R), PAD_LEN - PAD_R]) circle(PAD_R);
            translate([sx*(PAD_W_TIP/2  - PAD_R), PAD_R])           circle(PAD_R);
        }
    }
}

latch();
