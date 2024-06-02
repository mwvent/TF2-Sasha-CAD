wallSz = 0.6*4;
spc = 0.2;
pipeSz = 20;


module partOne() difference() {
    union() {
        d = pipeSz+wallSz;
        cylinder(h=wallSz, d=d, $fn=256);
        cylinder(h=40, d=d, $fn=256);
        cylinder(h=25, d=d*1.5, $fn=256);
        translate([0,0,25])
            cylinder(h=5, d1=d*1.5, d2=d, $fn=256);
    }
    translate([0,0,wallSz]) cylinder(h=50, d=pipeSz+spc, $fn=256);
}


module partTwo() difference() {
    h=40;
    d = pipeSz+wallSz;
    union() {
        cylinder(h=h, d=d, $fn=256);
        translate([0,0,h/2])
        rotate([0,90,0])
            cylinder(h=h/2, d=pipeSz+wallSz, $fn=256);
    translate([0,0,0]) cylinder(h=h+1, d=pipeSz+spc, $fn=256);
    }
    translate([0,0,h/2])
        rotate([0,90,0])
            cylinder(h=h+1, d=pipeSz+spc, $fn=256);
    translate([0,0,0]) cylinder(h=h+1, d=pipeSz+spc, $fn=256);
}


module partThree() difference() {
    totH = 120;
    bottomD = 110;
    bottomH = totH*0.15;
    hStages = [ totH*0.15, totH*0.40, totH*0.55, totH ];
    hSideCut = ((hStages[3] - hStages[2]) / 2) + hStages[2];
    $fn=256;
    union() {
        d = pipeSz+wallSz;
        difference() {
            cylinder(h=hStages[0], d=bottomD);
            translate([0,0,hStages[0]/2])
                cylinder(h=hStages[0], d=bottomD*0.8);
        }
        cylinder(h=wallSz, d=d);
        cylinder(h=hStages[3], d=d);
        d1 = bottomD*0.7;
        d2 = bottomD*0.5;
        cylinder(h=hStages[1], d=d1);
        translate([0,0,hStages[1]])
            cylinder(h=hStages[2]-hStages[1], d1=d1, d2=d2);
        translate([0,0,hStages[2]])
            cylinder(h=hStages[3]-hStages[2], d=d2);
    }
    translate([0,totH/2,hSideCut]) rotate([90,0,0])
        #cylinder(h=totH, d=pipeSz+spc);
    cylinder(h=totH-wallSz*2, d=pipeSz+spc);
}

//partOne();
//partTwo();
partThree();
