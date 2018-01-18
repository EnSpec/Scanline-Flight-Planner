import shapefile
import os

SHAPE_TYPES={'Polygon':5,'Point':1}
KEYS = 'lon','lat'
def findPointCoords(shpfile):
    shpf = shapefile.Reader(shpfile)
    coords = []
    for shape in shpf.shapes():
        if shape.shapeType == SHAPE_TYPES['Point']:
            coords.append(dict(zip(KEYS,shape.points[0])))
    return coords

def findPolyCoords(shpfile):
    shpf = shapefile.Reader(shpfile)
    coords = []
    for shape in shpf.shapes():
        if shape.shapeType == SHAPE_TYPES['Polygon']:
            coords+=[[dict(zip(KEYS,p))for p in shape.points]]
    return coords

def findRegionType(shpfile,types_to_check=("Polygon","Point")):
    shpf = shapefile.Reader(shpfile)
    for shape in shpf.shapes():
        for t in types_to_check:
            if shape.shapeType == SHAPE_TYPES[t]:
                return t
    return None

def findMeta(shpfile):
    shpf = shapefile.Reader(shpfile)
    fields = shpf.fields
    records = shpf.records()
    out = {key:[]for key in fields}
    print(records)

def coordDictListToCoord2DList(coord_dict_list,alt=0):
    coords = list(map(lambda c:[c['lon'],c['lat'],alt],coord_dict_list))
    nested_coords = [[p1,p2]for p1,p2 in zip(coords[::2],coords[1::2])]
    return [coords]


def planOutlineFromCoords(fname,regions,alt,approach,bearing,sidelap,
        inst,names,vehic='fullscale',units='US'):
    polyw = shapefile.Writer(shapefile.POLYGON)
    polyw.field('name','C',40)
    polyw.field('alt','F',12)
    polyw.field('approach','F',12)
    polyw.field('bearing','F',12)
    polyw.field('sidelap','F',12)
    polyw.field('inst','C',40)
    polyw.field('frame','F',12)
    polyw.field('fov','F',10)
    polyw.field('vehicle','C',20)
    polyw.field('units','C',10)
    for area,name in zip(regions,names):
        bounds = coordDictListToCoord2DList(area,0)
        polyw.poly(parts=bounds)
        polyw.record(
            name,
            alt,
            approach,
            bearing,
            sidelap,
            inst.name,
            inst.frame,
            inst.fieldOfView,
            vehic,
            units
        )
    polyw.save(fname)

def flightPlanFromCoords(outpath,coords,scanlinebounds,alt,speed):
    if not os.path.isdir(outpath):
        os.makedirs(outpath)
    linew = shapefile.Writer(shapefile.POLYLINE)
    linew.field('idx','N',10)
    footw = shapefile.Writer(shapefile.POLYGON)
    footw.field('idx','N',10)
    pointw = shapefile.Writer(shapefile.POINT)
    pointw.field('idx','N',10)
    pointw.field('type','C',40)
    for i in range(int(len(coords)/4)):
        #write the scan area first
        bounds = coordDictListToCoord2DList(scanlinebounds[i],0)
        footw.poly(parts=bounds)
        footw.record(str(i),'Scanline Bounds')
        #then the flight line
        line=coordDictListToCoord2DList(coords[4*i:4*i+4])
        linew.poly(parts=line,shapeType=shapefile.POLYLINE)
        linew.record(i)
        #then the start/end/entry/exit points of the flight line
        pointw.point(*line[0][0])
        pointw.point(*line[0][1])
        pointw.point(*line[0][2])
        pointw.point(*line[0][3])
        [pointw.record(i,p)for p in["START","ENTER","EXIT","END"]]

    linew.save(os.path.join(outpath,'scanlines'))
    footw.save(os.path.join(outpath,'footprints'))
    pointw.save(os.path.join(outpath,'points'))

