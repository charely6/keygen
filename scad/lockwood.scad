use <keygen.scad>
include <gen/lockwood.gen.scad>

module lockwood(bitting="",
                outline_name="LW5",
                warding_name="LW5") {

    name = "Lockwood";

    /*
        Bitting is specified from bow to tip, 0-x, with 0 being the shallowest cut and x (10 or sometimes referenced as "A") being the deepest.
        Example: 0258x6
    */

    outlines_k = ["LW5"];
    outlines_v = [[outline_LW5_points, outline_LW5_paths,
                   [-outline_LW5_points[6][0], -outline_LW5_points[4][1]],
                   engrave_LW5_points,
                   engrave_LW5_paths]];
    wardings_k = ["LW5"];
    wardings_v = [warding_LW5_points];

    outline_param = key_lkup(outlines_k, outlines_v, outline_name);
    outline_points = outline_param[0];
    outline_paths = outline_param[1];
    offset = outline_param[2];
    engrave_points = outline_param[3];
    engrave_paths = outline_param[4];

    warding_points = key_lkup(wardings_k, wardings_v, warding_name);
    
    cut_locations = [for(i=[6.1, 10.07, 14.04, 18.01, 21.98, 25.95]) i];
    depth_table = [for(i=[8.56:-0.38:4.75]) i];

    heights = key_code_to_heights(bitting, depth_table);

    difference() {
        if($children == 0) {
            key_blank(outline_points,
                      warding_points,
                      outline_paths=outline_paths,
                      engrave_right_points=engrave_points,
                      engrave_right_paths=engrave_paths,
                      engrave_left_points=engrave_points,
                      engrave_left_paths=engrave_paths,
                      offset=offset,
                      plug_diameter=12.7);
        } else {
            children(0);
        }
        key_bitting(heights, cut_locations, 1.2);
    }
}

// Defaults
bitting="";
outline="LW5";
warding="LW5";
lockwood(bitting, outline, warding);
