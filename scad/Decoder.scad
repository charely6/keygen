module decoder(name, depth_table, wardingHeight=8, doubleSided=false){
    numOfDepths = len(depth_table);
    maxDepth = max(depth_table);
    thickness=1;
    spacePerDepth=4;
    union(){
    difference()
    {
        cube([(numOfDepths+2)*spacePerDepth,maxDepth+2*spacePerDepth,thickness]);
        translate([(1)*spacePerDepth,spacePerDepth,-1]){
            cube([spacePerDepth,depth_table[0],thickness+2]);
        }
        for(i=[1:numOfDepths-1]){
            translate([(1+i)*spacePerDepth-0.1,spacePerDepth,-1]){
                if(doubleSided){
                  cube([spacePerDepth+0.1,2*depth_table[i]-wardingHeight,thickness+2]);  
                 }else{
                 cube([spacePerDepth+0.1,depth_table[i],thickness+2]);
                }
            }
        }
    }
       for(i=[0:numOfDepths-1]){
            translate([(1.5+i)*spacePerDepth,depth_table[i]+(spacePerDepth*1.25),thickness]){
                text(str(i), font="Liberation Sans", size=spacePerDepth/2, halign="center");
            }
        }
       translate([((numOfDepths+2)*spacePerDepth)/2,spacePerDepth*0.25,thickness]){
           text(name,font="Liberation Sans", size=spacePerDepth/2,halign="center");
           } 

    }
    
}
name = "Schlage Classic";
depth_table = [for(i=[0.335:-0.015:0.199]) i*25.4];
decoder(name, depth_table);
   
    