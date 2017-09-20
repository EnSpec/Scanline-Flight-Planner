from lxml import etree
from datetime import datetime,timedelta
from collections import OrderedDict

XHTML_NSMAP=OrderedDict({
        None:"http://www.topografix.com/GPX/1/1",
        "xsi":"http://www.w3.org/2001/XMLSchema-instance",
        "wptx1":"http://www.garmin.com/xmlschemas/WaypointExtension/v1",
        "gpxx":"http://www.garmin.com/xmlschemas/GpxExtensions/v3",
        #"gpxtrx":"http://www.garmin.com/xmlschemas/GpxExtensions/v3",
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
        ["gpxx","WaypointExtension","DisplayMode","SymbolAndName"],
        ["wptx1","WaypointExtension","DisplayMode","SymbolAndName"],
        ["ctx","CreationTimeExtension","CreationTime",None]
]



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
            "maxlat":str(bounds[0]['lat']),
            "maxlon":str(bounds[0]['lon'])
    }
    boundsElem = etree.SubElement(metaElem,"bounds",**bound_dict)
    return metaElem

def wayPointExtensions(time):
    extensions=etree.Element("extensions")
    for ext in WP_EXTENSIONS:
        parent=extensions
        for item in ext[1:-1]:
            tag="{"+XHTML_NSMAP[ext[0]]+"}"+item
            extElem=etree.SubElement(parent,tag)
            parent=extElem
        parent.text=ext[-1] or time
    return extensions



def makeWayPoint(coord,alt,time,seq_no):
    wayptElem = etree.Element("wpt",lat=str(coord['lat']),
            lon=str(coord['lon']))

    timeElem = etree.SubElement(wayptElem,"time")
    timeElem.text = time

    nameElem = etree.SubElement(wayptElem,"name")
    nameElem.text ="{}-{}-{}".format(alt,int(seq_no/4)+1,int(seq_no%4)+1)

    symElem = etree.SubElement(wayptElem,"sym")
    symElem.text="Flag, Blue"

    typeElem = etree.SubElement(wayptElem,"type")
    typeElem.text="user"

    wayptElem.append(wayPointExtensions(time))

    return wayptElem

def waypointsFromCoords(fname,coords,alt,bounds,times=None):
    """Take a list of coordinates and output a waypoint file that visits each
    point"""
    import sys
    root=etree.Element("gpx",nsmap=XHTML_NSMAP,attrib=ROOT_ATTRIBS,
            creator="Garmin Desktop App", version="1.1")
    #make up some fake timestamps
    times = times or [(datetime.now()+timedelta(seconds=5*i)).isoformat()
            for i in range(len(coords))]

    root.append(metadata(bounds,times[0]))

    for i,coord in enumerate(coords):
        root.append(makeWayPoint(coord,alt,times[i],i))

    with open(fname,"w") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n')
        f.write(etree.tostring(root,pretty_print=True).decode('ascii'))

