"""Functions to read/write APM Planner waypoint files
"""

CMDS = {
    "Waypoint": 16,
    "Ret":20,
    "Condition Yaw":115,
    "Change Speed":178
}
KEYS = {v:k for k,v in CMDS.items()}
HEAD = "QGC WPL 110\n" 
TAIL = "{}\t0\t0\t20\t0\t0\t0\t0\t0\t0\t0\t1\n"
FMT = "{}\t"*8+"{lat}\t{lon}\t{alt}\t1\n"

def waypointsFromCoords(fname,coords,alt,angle=None,speed=None):
    """Take a list of coordinates and output a waypoint file that visits each
    point then returns to the first"""
    with open(fname,'w') as f:
        f.write(HEAD)
        f.write(FMT.format(0,1,3,CMDS["Waypoint"],*[0]*4,alt=alt,**coords[0]))
        idx = 1
        if angle is not None:
            f.write(FMT.format(1,0,0,CMDS["Condition Yaw"],angle,
                0,1,0,alt=0,lat=0,lon=1))
            idx+=1
        if speed is not None:
            f.write(FMT.format(2,0,3,CMDS["Change Speed"],0,speed,
                1,0,lat=0,lon=0,alt=alt))
            idx+=1
        for coord in coords[1:]:
            f.write(FMT.format(idx,0,3,CMDS["Waypoint"],*[0]*4,alt=alt,**coord))
            idx+=1
        f.write(TAIL.format(idx))


