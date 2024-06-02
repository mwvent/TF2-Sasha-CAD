barrelsSpc=33;
barrelD=25.4;
barrelJoinH=30;
capH=5;
$fn=256;

module flame() {
    difference() {
        union() {
            translate([0,0,barrelsSpc])
                scale([1,1,0.7])
                import("OrangeCap-flame.stl");
             translate([0,0,barrelJoinH])
            cylinder(h=capH+2, d=barrelsSpc*3+6);
        }
        translate([0,0,barrelJoinH-2]) {
        cylinder(h=capH+2, d=barrelsSpc*3+0.4);
        cylinder(h=capH+5, d=barrelsSpc*2.35);
        }
    }
}

module part() {
    for(r=[0:1:5]) rotate([0,0,r*(360/6)]) {
        difference() {
            translate([barrelsSpc,0,0])
                cylinder(h=barrelJoinH, d=barrelsSpc);
            translate([barrelsSpc,0,0])
                cylinder(h=barrelJoinH, d=barrelD);
        }
    }
    translate([0,0,barrelJoinH])
        cylinder(h=capH, d=barrelsSpc*3);
       translate([0,0,barrelJoinH+capH]) 
    difference() {
        cylinder(h=capH*1.5, d=barrelsSpc*2.9);
        linear_extrude(height=capH*1.5)
            translate([-44,-10,0])
                text(text="Prop",size=30);
    }
}

flame();