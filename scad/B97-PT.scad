use <keygen.scad>
include <B97-PT.gen.scad>

module B97_PT(bitting="",
               outline_name="B97-PT",
               warding_name="B97-PT",
               series_name="GM04") {

    name = "B97-PT";

     
    /*
        Bitting is specified from bow to tip, 0-4, with 0 being the shallowest cut and 1 being the deepest.
                   The 4th (5th?) entry in the depth table that seems way higher is the key I was trying to replicate seemed to skip the first cut location so I added that as a "Skip" value to use. 
        Example: 412221
                   
        This model is for a Kawasaki Key sometimes called a X103 or a KA14 I think
        I pulled the outline and such from the motorcycle guide I have added and the main 2 depth and cut location tables from the Framon Key depth guide (v8) 
    */
    outlines_k = ["B97-PT"];
    wardings_k = ["B97-PT"];
                   
    wardingHeight_min = min([for(e=warding_points) e[1]]);
    wardingHeight_max = max([for(e=warding_points) e[1]]);
    wardingHeight = wardingHeight_max-wardingHeight_min;

    offset = [-outline_points[30][0], -outline_points[30][1]];
    depth_table= 
        series_name=="GM04"  ? [for(i=[.315, .290, .265, .240]) i*25.4] :
        series_name=="5001-6000"? [for(i=[.260, .240, .220, .200, 20]) i*25.4] :
        series_name=="custom"   ? [for(i=[.245, .215, .220, .200, 20]) i*25.4] :[];
    cut_locations=
        series_name=="GM04"  ? [for(i=[.205, .297, .389, .481, .573, .665, .757, .849, .941, 1.033]) i*25.4] :
        series_name=="5001-6000"? [for(i=[.1, .2, .3, .4, .5, .6]) i*25.4] :
        series_name=="custom"   ? [for(i=[.1, .2, .3, .4, .5, .6]) i*25.4] :[];

    // Kwikset starts with 1??

    heights = key_code_to_heights(bitting, depth_table);

    difference() 
    {
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
        key_bitting(heights, cut_locations, 1.4, 90);
        //This is my attempt at adding double sidded cutting Hopefully it works for others.
        translate([0,0,wardingHeight]){ 
        rotate([0,180,0]){
            key_bitting(heights, cut_locations, 1.4, 90);
        }
        }
    }
}

// Defaults
//bitting="412221";
bitting ="0012012120";
outline="B97-PT";
warding="B97-PT";
series_name="GM04";
B97_PT(bitting, outline, warding, series_name);
