import shapefile

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
