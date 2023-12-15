use <keygen.scad>
include <falcon.gen.scad>

module falcon_025(bitting="",
                       outline_name="M",
                       warding_name="M") {

    name = "Falcon 025";

    /*
        Bitting is specified from bow to tip, 0-6, with 0 being the shallowest cut and 6 being the deepest.
        Example: 25363
    */

    outlines_k = ["M"];
    outlines_v = [[outline_m_points, outline_m_paths,
                   [-outline_m_points[92][0], -outline_m_points[98][1]],
                   engrave_m_points,
                   engrave_m_paths]];
    wardings_k = ["M"];
    wardings_v = [warding_m_points];

    outline_param = key_lkup(outlines_k, outlines_v, outline_name);
    outline_points = outline_param[0];
    outline_paths = outline_param[1];
    offset = outline_param[2];
    engrave_points = outline_param[3];
    engrave_paths = outline_param[4];

    warding_points = key_lkup(wardings_k, wardings_v, warding_name);
    
    cut_locations = [for(i=[.237, .393, .549, .705, .861, 1.017]) i*25.4];
    depth_table = [for(i=[0.340:-0.025:0.189]) i*25.4];

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
        key_bitting(heights, cut_locations, .7874);
    }
}

// Defaults
bitting="136240";
outline="M";
warding="M";
falcon_025(bitting, outline, warding);
