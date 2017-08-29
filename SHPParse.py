import shapefile

POINT_TYPE = 1
POLY_TYPE = 5
KEYS = 'lon','lat'
def findPointCoords(shpfile):
    shpf = shapefile.Reader(shpfile)
    coords = []
    for shape in shpf.shapes():
        if shape.shapeType == POINT_TYPE:
            coords.append(dict(zip(KEYS,shape.points[0])))
    return coords

def findPolyCoords(shpfile):
    shpf = shapefile.Reader(shpfile)
    coords = []
    for shape in shpf.shapes():
        if shape.shapeType == POLY_TYPE:
            coords+=[[dict(zip(KEYS,p))for p in shape.points]]
    return coords
