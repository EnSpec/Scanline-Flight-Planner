"""Formulae taken from http://www.movable-type.co.uk/scripts/latlong.html"""
import numpy as np
from numpy import sin,cos,radians,degrees,arcsin,arccos,arctan2,sqrt,pi

EARTH_RADIUS = 6.3710088e6 #meters


def prettifyCoords(coords):
    out = {}
    for key,coord in coords.items():
        formatstr = "{:d}\xB0 {:02d}' {:08.5f}\""
        if coord < 0:
            coord *= -1 
            formatstr = "-" + formatstr
        deg,minute = divmod(coord*60,60)
        minute,sec = divmod(minute*60,60)
        out[key] = formatstr.format(int(deg),int(minute),sec)
    return out

def atDistAndBearing(start,dist,bearing):
    """Find the destination from coordinates start travelling 
    `dist` meters at bearing `bearing`
    """
    lat0 = start['lat']
    lon0 = start['lon']
    latr0 = radians(lat0)
    lonr0 = radians(lon0)
    bearingr = radians(bearing)
    d_div_R = dist/EARTH_RADIUS
    latrf = arcsin(sin(latr0)*cos(d_div_R)+
                cos(latr0)*sin(d_div_R)*cos(bearingr))

    lonrf = arctan2(sin(bearingr)*sin(d_div_R)*cos(latr0),
                cos(d_div_R)-sin(latr0)*sin(latrf)) + lonr0

    latf = degrees(latrf)
    lonf = ((degrees(lonrf)+540)%360) - 180
    return {'lat':latf,'lon':lonf}

def bearingTo(start,end):
    latr0 = radians(start['lat'])
    lonr0 = radians(start['lon'])
    latrf = radians(end['lat'])
    lonrf = radians(end['lon'])
    dlonr = radians(end['lon']-start['lon'])
    
    y = sin(dlonr)*cos(latrf)
    x = cos(latr0)*sin(latrf)-sin(latr0)*cos(latrf)*cos(dlonr)

    return (degrees(arctan2(y,x))+360)%360

def distanceTo(start,end):
    latr0 = radians(start['lat'])
    lonr0 = radians(start['lon'])
    latrf = radians(end['lat'])
    lonrf = radians(end['lon'])
    dlatr = radians(end['lat']-start['lat'])
    dlonr = radians(end['lon']-start['lon'])

    a = (sin(dlatr/2)**2 + cos(latr0)*cos(latrf) * 
            sin(dlonr/2)**2)
    c = 2*arctan2(sqrt(a),sqrt(1-a))
    d = EARTH_RADIUS*c

    return d

def intersectionOf(start,bearing1,end,bearing2):
    latr0 = radians(start['lat'])
    lonr0 = radians(start['lon'])
    latrf = radians(end['lat'])
    lonrf = radians(end['lon'])
    dlatr = radians(end['lat']-start['lat'])
    dlonr = radians(end['lon']-start['lon'])
    theta13 = radians(bearing1)
    theta23 = radians(bearing2)

    angld12 = 2*arcsin(sqrt((sin(dlatr/2)**2 + cos(latr0) * 
            cos(latrf)*sin(dlonr/2)**2)))
    theta1 = arccos((sin(latrf) - sin(latr0)*cos(angld12)) /
                (sin(angld12)*cos(latr0)))
    theta2 = arccos((sin(latr0) - sin(latrf)*cos(angld12)) /
                (sin(angld12)*cos(latrf)))

    if sin(dlonr) > 0:
        theta12 = theta1
        theta21 = 2*pi - theta2
    else:
        theta12 = 2*pi - theta1
        theta21 = theta2

    angl1 = (theta13 - theta12 + pi)%(2*pi) - pi
    angl2 = (theta21 - theta23 + pi)%(2*pi) - pi

    if sin(angl1) == 0 and sin(angl2) == 0:
        return None
    if sin(angl1)*sin(angl2) < 0:
        return None
    
    angl3 = arccos(-cos(angl1)*cos(angl2)+sin(angl1)*sin(angl2)*cos(angld12))
    angld13 = arctan2(sin(angld12)*sin(angl1)*sin(angl2),
                            cos(angl2)+cos(angl1)*cos(angl3))

    latr3 = arcsin(sin(latr0)*cos(angld13)+cos(latr0) *
                       sin(angld13)*cos(theta13))

    dlonr13 = arctan2(sin(theta13)*sin(angld13)*cos(latr0),
                       cos(angld13)-sin(latr0)*sin(latr3))
    lonr3 = lonr0 + dlonr13

    lat3 = degrees(latr3)
    lon3 = (degrees(lonr3)+540)%360 - 180
    return {'lat':lat3,'lon':lon3}

if __name__ == '__main__':
    START = {'lat':43.305487,'lon':-89.332522}
    END   =  {'lat':43.305303,'lon':-89.332033}

    bearingTest = atDistAndBearing(END,1000,90)
    print("1000m from END @ 90 degrees:",end=' ')
    print(prettifyCoords(bearingTest))

    print("Bearing between START and END",end=' ')
    print(bearingTo(START,END))

    print("Distance between START and END",end=' ')
    print(distanceTo(START,END))
    
    intersectionTest = intersectionOf({'lat':51.8853,'lon':0.2545},108.547,
                {'lat':49.0034,'lon':2.5735},32.435)
    print("Intersection Test",end=' ')
    print(intersectionTest)
   
    
