from lxml import etree
from datetime import datetime,timedelta
from collections import OrderedDict

XHTML_NSMAP=OrderedDict({
        None:"http://www.topografix.com/GPX/1/1",
        "xsi":"http://www.w3.org/2001/XMLSchema-instance",
        "wptx1":"http://www.garmin.com/xmlschemas/WaypointExtension/v1",
        "gpxx":"http://www.garmin.com/xmlschemas/GpxExtensions/v3",
        "gpxtrx":"http://www.garmin.com/xmlschemas/GpxExtensions/v3",
        "gpxtpx":"http://www.garmin.com/xmlschemas/TrackPointExtension/v1",
        "trp":"http://www.garmin.com/xmlschemas/TripExtensions/v1",
        "adv":"http://www.garmin.com/xmlschemas/AdventuresExtensions/v1",
        "prs":"http://www.garmin.com/xmlschemas/PressureExtension/v1",
        "tmd":"http://www.garmin.com/xmlschemas/TripMetaDataExtensions/v1",
        "vptm":"http://www.garmin.com/xmlschemas/ViaPointTransportationModeExtensions/v1",
        "ctx":"http://www.garmin.com/xmlschemas/CreationTimeExtension/v1",
        "gpxacc":"http://www.garmin.com/xmlschemas/AccelerationExtension/v1",
        "gpxpx":"http://www.garmin.com/xmlschemas/PowerExtension/v1",
        "vidx1":"http://www.garmin.com/xmlschemas/VideoExtension/v1"
})
SCHEMA_LOCATION="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd http://www.garmin.com/xmlschemas/WaypointExtension/v1 http://www8.garmin.com/xmlschemas/WaypointExtensionv1.xsd http://www.garmin.com/xmlschemas/TrackPointExtension/v1 http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd http://www.garmin.com/xmlschemas/GpxExtensions/v3 http://www8.garmin.com/xmlschemas/GpxExtensionsv3.xsd http://www.garmin.com/xmlschemas/ActivityExtension/v1 http://www8.garmin.com/xmlschemas/ActivityExtensionv1.xsd http://www.garmin.com/xmlschemas/AdventuresExtensions/v1 http://www8.garmin.com/xmlschemas/AdventuresExtensionv1.xsd http://www.garmin.com/xmlschemas/PressureExtension/v1 http://www.garmin.com/xmlschemas/PressureExtensionv1.xsd http://www.garmin.com/xmlschemas/TripExtensions/v1 http://www.garmin.com/xmlschemas/TripExtensionsv1.xsd http://www.garmin.com/xmlschemas/TripMetaDataExtensions/v1 http://www.garmin.com/xmlschemas/TripMetaDataExtensionsv1.xsd http://www.garmin.com/xmlschemas/ViaPointTransportationModeExtensions/v1 http://www.garmin.com/xmlschemas/ViaPointTransportationModeExtensionsv1.xsd http://www.garmin.com/xmlschemas/CreationTimeExtension/v1 http://www.garmin.com/xmlschemas/CreationTimeExtensionsv1.xsd http://www.garmin.com/xmlschemas/AccelerationExtension/v1 http://www.garmin.com/xmlschemas/AccelerationExtensionv1.xsd http://www.garmin.com/xmlschemas/PowerExtension/v1 http://www.garmin.com/xmlschemas/PowerExtensionv1.xsd http://www.garmin.com/xmlschemas/VideoExtension/v1 http://www.garmin.com/xmlschemas/VideoExtensionv1.xsd"
ROOT_ATTRIBS={"{"+XHTML_NSMAP['xsi']+"}schemaLocation": SCHEMA_LOCATION}
WP_EXTENSIONS=[
    ["gpxx",["WaypointExtension",["DisplayMode","SymbolAndName"]]],
    ["wptx1",["WaypointExtension",["DisplayMode","SymbolAndName"]]],
    ["ctx",["CreationTimeExtension",["CreationTime",None]]]
]

RTE_EXTENSIONS=[
    ["gpxx",["RouteExtension",["IsAutoNamed","true"],
        ["DisplayColor","Magenta"]]],
    ["trp",["Trip",["TransportationMode","Hiking"]]],
]

RTEPT_EXTENSIONS=[
    ["trp",["ViaPoint",["CalculationMode","ShorterDistance"],
        ["ElevationMode","Standard"]]],
    ["gpxx",["RoutePointExtension",["Subclass","0"*12+"F"*24]]]
]

def _recursiveExtensionHelper(nsTag,exList,time):
    elem = etree.Element("{"+XHTML_NSMAP[nsTag]+"}"+exList[0])
    if all([not isinstance(e,list)for e in exList]):
        #base case: a tag + text combo
        elem.text=exList[1] or time
        return elem
    else:
        for nextList in exList[1:]:
            child = _recursiveExtensionHelper(nsTag,nextList,time)
            elem.append(child)
        return elem


def fixedExtensions(extension_tree,time):
    extensions=etree.Element("extensions")
    for ext in extension_tree:
        tree = _recursiveExtensionHelper(ext[0],ext[1],time)
        extensions.append(tree)
    return extensions

def metadata(bounds,time):
    metaElem = etree.Element("metadata")
    
    link = etree.SubElement(metaElem,"link",href="http://www.garmin.com")
    
    text = etree.SubElement(link,"text")
    text.text = "Garmin International"

    timeElem = etree.SubElement(metaElem,"time")
    timeElem.text = time

    bound_dict={
            "maxlat":str(bounds[1]['lat']),
            "maxlon":str(bounds[1]['lon']),
            "minlat":str(bounds[0]['lat']),
            "minlon":str(bounds[0]['lon'])
    }

    boundsElem = etree.SubElement(metaElem,"bounds",**bound_dict)
    return metaElem




def makeWayPoint(coord,alt,time,seq_no):
    wayptElem = etree.Element("wpt",lat=str(coord['lat']),
            lon=str(coord['lon']))

    timeElem = etree.SubElement(wayptElem,"time")
    timeElem.text = time

    nameElem = etree.SubElement(wayptElem,"name")
    nameElem.text ="{}-{}-{}".format(alt,int(seq_no/4)+1,int(seq_no%4)+1)

    symElem = etree.SubElement(wayptElem,"sym")
    if(seq_no in [1,2]):
        symElem.text="Flag, Green"
    else:
        symElem.text="Flag, Blue"

    typeElem = etree.SubElement(wayptElem,"type")
    typeElem.text="user"

    wayptElem.append(fixedExtensions(WP_EXTENSIONS,time))

    return wayptElem



def makeRoutePoint(coord,alt,time,seq_no):
    rteptElem = etree.Element("rtept",lat=str(coord['lat']),
            lon=str(coord['lon']))

    timeElem = etree.SubElement(rteptElem,"time")
    timeElem.text = time

    nameElem = etree.SubElement(rteptElem,"name")
    nameElem.text ="{}-{}-{}".format(alt,int(seq_no/4)+1,int(seq_no%4)+1)

    symElem = etree.SubElement(rteptElem,"sym")
    symElem.text="Navaid, "+["Blue","Green","Green","Blue"][seq_no%4]

    rteptElem.append(fixedExtensions(RTEPT_EXTENSIONS,time))

    return rteptElem


def makeRoute(alt,seq_nos):
    rteElem = etree.Element("rte")

    seq1 = "{}-{}-{}".format(alt,int(seq_nos[0]/4)+1,int(seq_nos[0]%4)+1)
    seq2 = "{}-{}-{}".format(alt,int(seq_nos[-1]/4)+1,int(seq_nos[-1]%4)+1)
    
    nameElem = etree.SubElement(rteElem,"name")
    nameElem.text="{} to {}".format(seq1,seq2)

    rteElem.append(fixedExtensions(RTE_EXTENSIONS,None))

    return rteElem

def gpxtrx2gpxx(xml_string):
    """gpxtrx and gpxx have the same namespace url, lxml likes to use
    gpxtrx but the "correct" file format should use gpxx. Manually
    replace all incorrect gpxtrx tags"""
    idx=xml_string.index('gpxtrx')+1
    return''.join((xml_string[:idx],xml_string[idx:].replace('gpxtrx','gpxx')))

def waypointsFromCoords(fname,areas,alt,bounds,times=None):
    """Take a list of coordinates and output a waypoint file that visits each
    point"""
    import sys
    root=etree.Element("gpx",nsmap=XHTML_NSMAP,attrib=ROOT_ATTRIBS,
            creator="Garmin Desktop App", version="1.1")
    #make up some fake timestamps
    times = times or [(datetime.now()+timedelta(seconds=5*i)).isoformat()
            .split('.')[0]+'Z' for i in range(sum([len(c)for c in areas]))]

    root.append(metadata(bounds,times[0]))

    for coords in areas:
        route = makeRoute(alt,[0,len(coords)])

        for i,coord in enumerate(coords):
            #root.append(makeWayPoint(coord,alt,times[i],i))
            route.append(makeRoutePoint(coord,alt,times[i],i))

        root.append(route)

    with open(fname,"w") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>')
        f.write(gpxtrx2gpxx(etree.tostring(root,pretty_print=True)
            .decode('ascii')))

