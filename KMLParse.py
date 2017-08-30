#there are python libraries for parsing kml, but the file's we're dealing with
#are simple enough that lxml does the trick
from lxml import etree
from contextlib import contextmanager

def findchildren(elem,tag):
    return [c for c in elem.getchildren()if c.tag.endswith(tag)]

def latlonfromcoords(coord_element):
    key = ['lon','lat']
    coord = coord_element.text
    return[dict(zip(key,[float(f)for f in c.split(',')]))for c in coord.split()]


def digIntoTree(elem,tree,i=-1):
    if i == -1:
        root = elem.getroot().getchildren()[0]
        return digIntoTree(root,tree,0)
    elif i == len(tree) - 1:
        return findchildren(elem,tree[i])
    else:
        elem_list = []
        for e in findchildren(elem,tree[i]):
            elem_list+=digIntoTree(e,tree,i+1)
        return elem_list

def findPointCoords(kmlfile):
    TREE=["Folder","Placemark","Point","coordinates"]
    with open(kmlfile) as f:
        return[latlonfromcoords(c)[0] for c in digIntoTree(etree.parse(f),TREE)]

def findPolyCoords(kmlfile,ptype="LinearRing"):
    TREE=["Folder","Placemark","Polygon","outerBoundaryIs",ptype,"coordinates"]
    with open(kmlfile) as f:
        return[latlonfromcoords(c) for c in digIntoTree(etree.parse(f),TREE)]

def findRegionType(kmlfile,types_to_check=("Polygon","Point")):
    """Test the various coord finding methods on this file and see if they
    produce valid results"""
    with open(kmlfile) as f:
        dataset = etree.parse(f)
        for elem in dataset.iter():
            for t in types_to_check:
                if elem.tag.endswith(t):
                    return t
    return None



if __name__ == '__main__':
    import sys
    print(findRegionType(sys.argv[1]))
    #print(findPointCoords(sys.argv[1]))

