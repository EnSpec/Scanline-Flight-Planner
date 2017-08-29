import LonLatMath as llmath
import numpy as np
import time
import Spectrometer
import KMLParse
import SHPParse


class Edge(object):
    """The representation of a single edge of a ScanArea"""
    #the maximum difference in bearing for a point to be counted as on-line
    BEARING_ERROR = 1e-2 #degrees
    def __init__(self,p1,p2):
        self._start = p1
        self._end = p2
        self._bearing = None
        self._length = None

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @property
    def endpoints(self):
        return self._start,self._end

    @property
    def bearing(self):
        if self._bearing is None:
            self._bearing = llmath.bearingTo(self.start,self.end)
        return self._bearing

    @property
    def length(self):
        if self._length is None:
            self._length = llmath.distanceTo(self.start,self.end)
        return self._length

    def intersection(self,point,bearing = None):
        int_info = {}
        #first, see if the point being tested lies along the edge
        bearing_to_point = llmath.bearingTo(self._start,point)
        dist_to_point = self.distanceTo(point)
        if (abs(bearing_to_point-self.bearing)<self.BEARING_ERROR and 
                dist_to_point[0] < self.length):
            int_info['point']=point
            int_info['dist'] = dist_to_point[0]
            return int_info

        if bearing is None:
            return None
        #else, see where the line at angle bearing passing through point
        #intersects with the edge
        intersect=llmath.intersectionOf(self.start,self.bearing,point,bearing)
        if intersect is not None:
            #sometimes intersectionOf returns NaN, this is not good
            if np.isnan(intersect['lat']):
                return None

            #check that intersect actually lies between start and end
            dists_from_me = self.distanceTo(intersect)
            if dists_from_me[0]<self.length and dists_from_me[1]<self.length:
                dist_from_point = llmath.distanceTo(point,intersect)
                int_info['point'] = intersect
                int_info['dist'] = dist_from_point
            else:
                int_info = None
        else:
            int_info = None
        return int_info

    def distanceTo(self,point):
        """Get the distance from both ends of the Edge to the point"""
        start_d = llmath.distanceTo(self.start,point)
        end_d  = llmath.distanceTo(self.end,point)
        return start_d,end_d


    def reverse(self):
        return Edge(self.end,self.start)

    def __repr__(self):
        prettyS = "{lat},{lon}".format(**llmath.prettifyCoords(self.start))
        prettyE = "{lat},{lon}".format(**llmath.prettifyCoords(self.end))
        return "{} -> {} (bearing: {}, length: {})".format(
            prettyS, prettyE, self.bearing, self.length)

class ScanArea(object):
    """Represents a single, continuous area of land to be scanned.
    Stored internally as a list of coordinates
    """
    def __init__(self,home,perimeter,spectrometer=None,alt = None,bearing=None):
        self._home = home
        self._perimeter = perimeter
        self.setBearing(bearing)
        self._buildEdges()
        self._coords = []
        self._alt = alt
        self._spectrometer = spectrometer
    
    def setHome(self,home):
        self._home = home

    def setAltitude(self,altitude):
        self._alt = altitude

    def setSpectrometer(self,spectrometer):
        self._spectrometer = spectrometer

    def setBearing(self,bearing):
        if bearing == 90:
            #trig stuff in LatLonMath doesn't like 90
            bearing = 89.99
        self._bearing = bearing
        self._arrangePerimeter(self._perimeter)

    def _computeCenter(self,perimeter):
        """Find the center of the set of points. This is the cartesian center
        rather than geographic, hopefully it doesn't make that much of a
        difference on the scale we're working at.
        """
        center = np.mean([[p['lat'],p['lon']]for p in perimeter],axis=0)
        center = {'lat':center[0],'lon':center[1]}
        return center

    def _arrangePerimeter(self,perimeter):
        """Arrange the perimiter clockwise,then select the point nearest home
        as the starting point.
        """
        self._center = self._computeCenter(perimeter)
        if self._bearing is None:
            home_bearing = llmath.bearingTo(self._center,self._home)
        else:
            home_bearing = (self._bearing-90)%360
        perimeter.sort(key=lambda x:(llmath.bearingTo(self._center,x)+360-home_bearing)%360)
        self._perimeter = perimeter

    def _buildEdges(self):
        self._edges = []
        for start,end in zip(self._perimeter[:-1],self._perimeter[1:]):
            self._edges.append(Edge(start,end))
        self._edges.append(Edge(self._perimeter[-1],self._perimeter[0]))

    
    def _findIntersectionsInDirection(self,direction,start,curr_point=None):
        """Travel self._width meters in direction, then scan for an intersect
        with an edge both parallel and antiparallel to self._leading_edge.
        If no intersect is found in either direction, we've exited the ScanArea
        and can return
        """
        curr_point = curr_point or llmath.atDistAndBearing(
                self._perimeter[0],self._width,direction)
        found_intersect = True
        
        dir_coords = [start]
        while found_intersect:
            #don't check the leading edge
            new_points = []
            for t_dir in self._travel_dir,self._opp_dir:
                for edge in self._edges:
                    intersect = edge.intersection(curr_point,t_dir)
                    if intersect and len(new_points) < 2:
                        new_points.append(intersect['point'])
                        found_intersect = True
            
            curr_point = llmath.atDistAndBearing(
                     curr_point,self._width,direction)
            #append new_points to dir_coords such that the new_point closer 
            #to the last coord is added first
            if len(new_points) > 1:
                #if we cross multiple times (eg in a concave area), just take
                #the two most extreme
                if len(new_points) > 2:
                    n = len(new_points)
                    combos = [(i,j) for i in range(n)for j in range(i,n)]
                    new_edge = sorted([Edge(*c)for c in combos],
                            key=lambda x:x.length)[-1]
                else:
                    new_edge = Edge(*new_points)

                dists_from_coords = new_edge.distanceTo(dir_coords[-1])
                if dists_from_coords[0] > dists_from_coords[1]:
                    dir_coords += new_edge.endpoints[::-1]
                else:
                    dir_coords += new_edge.endpoints
            else:
                found_intersect = False
        return dir_coords[1:]

    def findScanLines(self):
        self._coords = [self._home]
        self._width = self._spectrometer.swathWidthAt(self._alt)
        #always travel parallel to our first edge
        self._leading_edge = self._edges[0]
        if self._bearing is None:
            self._coords+= self._perimeter[:2]
            self._travel_dir = self._leading_edge.bearing
            first_point = None
            first_traverse = 1
        else:
            self._travel_dir = self._bearing
            first_point = self._center
            first_traverse = -1

        self._opp_dir = (180+self._travel_dir)%360

        parallel_dir1 = (self._travel_dir+90)%360
        parallel_dir2 = (self._travel_dir-90)%360
        self._coords += self._findIntersectionsInDirection(
                parallel_dir1,self._perimeter[2],first_point)[::first_traverse]
        if first_point is not None:
            first_point = llmath.atDistAndBearing(
                    self._center,self._width,parallel_dir2)

        self._coords += self._findIntersectionsInDirection(
                parallel_dir2,self._coords[-1],first_point)

        self._coords.append(self._home)

        #flip things around so that we start by travelling the shorter
        #route from home at the beginning
        end_edges = Edge(self._coords[1],self._coords[-2])
        end_dists = end_edges.distanceTo(self._home)
        if end_dists[0] > end_dists[1]:
            print(len(self._coords),end=' ')
            self._coords = [self._home]+self._coords[1:-1:][::-1]+[self._home]
            print(len(self._coords))
        return self._coords

    def _plotPoints(self,points,**kwargs):
        from matplotlib import pyplot as plt
        if isinstance(points,list):
            xs = [p['lon'] for p in points]
            ys = [p['lat'] for p in points]
        else:
            xs = points['lon']
            ys = points['lat']
        plt.plot(xs,ys,**kwargs)

    def plot(self,show=True,include=['perimeter','coords']):
        from matplotlib import pyplot as plt
        if 'perimeter' in include:
            self._plotPoints(self._perimeter+[self._perimeter[0]],color='blue',lw=2)
        if self._coords and 'coords' in include:
            self._plotPoints(self._coords,color='r',lw=2)
        if 'perimeter' in include:
            self._plotPoints(self._perimeter[0],color='g',marker='o')
        if show:
            plt.show()

    def toWayPoints(self):
        raise NotImplementedError

    @classmethod
    def fromFile(cls,fname,fformat=None):
        raise NotImplementedError

    @classmethod
    def rectangle(cls,home,NW,SE,**kwargs):
        perim = []
        perim.append(NW)
        perim.append({'lat':NW['lat'],'lon':SE['lon']})
        perim.append(SE)
        perim.append({'lat':SE['lat'],'lon':NW['lon']})
        return cls(home,perim)

    @classmethod
    def regularNGon(cls,home,sides,center,radius,**kwargs):
        perim = []
        for angl in np.linspace(0,360,sides+1)[:-1]:
            perim.append(llmath.atDistAndBearing(center,radius,angl))
        return cls(home,perim)

    @classmethod
    def irregularRectangle(cls,home,center,radius,angle=None,
            irregularity=.5,**kwargs):
        angle = angle or np.random.randint(360)
        armtilt = np.random.randint(15,35)
        armtilts = [armtilt,180+armtilt,180-armtilt,-armtilt]
        perim=[llmath.atDistAndBearing(center,radius+irregularity*radius*
            np.random.rand(),angle+angl) for angl in armtilts]
        return cls(home,perim)


    @classmethod
    def regularStar(cls,home,points,center,radius,**kwargs):
        sides = 2*points
        perim = []
        for i,angl in enumerate(np.linspace(0,360,sides+1)[:-1]):
            dist = radius*(.5+.5*(i%2))
            perim.append(llmath.atDistAndBearing(center,dist,angl))
        return cls(home,perim)

class ScanRegion(object):
    """Class to represent the entire region being scanned, consisting of 
    one or more non-overlapping continuous regions"""
    def __init__(self,home,spectrometer=None,alt = None,bearing=None):
        self._home = home
        self._scanareas = []
        self._spectrometer = spectrometer
        self._alt = alt 
        self._bearing = bearing

    def addScanArea(self,scanarea):
        scanarea.setAltitude(self._alt)
        scanarea.setSpectrometer(self._spectrometer)
        scanarea.setBearing(self._bearing)
        self._scanareas.append(scanarea)

    def setAltitude(self,altitude):
        self._alt = altitude
        for sa in self.scanAreas:
            sa.setAltitude(self._alt)

    def setSpectrometer(self,spectrometer):
        self._spectrometer = spectrometer
        for sa in self.scanAreas:
            sa.setSpectrometer(self._spectrometer)

    def setBearing(self,bearing):
        if bearing == 90:
            #trig stuff in LatLonMath doesn't like 90
            bearing = 89.99
        self._bearing = bearing
        for sa in self.scanAreas:
            sa.setBearing(self._bearing)


    @property
    def scanAreas(self):
        return self._scanareas

    @scanAreas.setter
    def scanAreas(self,scanareas):
        self._scanareas = scanareas
        #make scan area metadata uniform
        self.setAltitude(self._altitude)
        self.setBearing(self._bearing)
        self.setSpectrometer(self._spectrometer)

    def findScanLines(self):
        """Find the scan lines of each ScanArea, then chain them together"""
        self._coords = [self._home]
        home = self._home
        for sa in self.scanAreas:
            sa.setHome(home)
            new_coords = sa.findScanLines()[1:-1]
            self._coords+= new_coords
            home = self._coords[-1]
        self._coords.append(self._home)

    def plot(self,show=True):
        for sa in self.scanAreas[:-1]:
            sa.plot(show=False,include='perimeter')
        self.scanAreas[-1]._plotPoints(self._coords,color='r',lw=2)
        self.scanAreas[-1].plot(show=True,include='perimeter')

    
    @classmethod
    def fromKMLPolys(Cls,kml_fname,home=None,**kwargs):
        coords = KMLParse.findPolyCoords(kml_fname)
        home = home or coords[0][0]
        region = Cls(home,**kwargs)
        for perimeter in coords:
            region.addScanArea(ScanArea(home,perimeter))
        return region

    @classmethod
    def fromSHPPolys(Cls,shp_fname,home=None,**kwargs):
        coords = SHPParse.findPolyCoords(shp_fname)
        home = home or coords[0][0]
        region = Cls(home,**kwargs)
        for perimeter in coords:
            region.addScanArea(ScanArea(home,perimeter))
        return region

if __name__ == '__main__':
    '''
    home = {'lat':43.305587,'lon':-89.333022}
    center = {'lat':43.305303,'lon':-89.332033}
    radius = 60
    region = ScanRegion(home)
    region.setBearing(45)
    region.setAltitude(40)
    region.setSpectrometer(Spectrometer.HeadwallNanoHyperspec())
    area = ScanArea.irregularRectangle(home,center,radius)
    region.addScanArea(area)
    for i in range(5):
        new_center = {'lat':center['lat'],'lon':center['lon']+.0022*i}
        if i%2:
            area = ScanArea.irregularRectangle(home,new_center,radius)
        else:
            area = ScanArea.irregularRectangle(home,new_center,radius/2)
        region.addScanArea(area)

    center = new_center

    for i in range(5):
        new_center = {'lat':center['lat']+.0013,'lon':center['lon']-.0022*i}
        if not i%2:
            area = ScanArea.irregularRectangle(home,new_center,radius)
        else:
            area = ScanArea.irregularRectangle(home,new_center,radius/2)
        region.addScanArea(area)
    '''
    import sys
    region = ScanRegion.fromSHPPolys(sys.argv[1])
    region.setBearing(45)
    region.setAltitude(40)
    region.setSpectrometer(Spectrometer.HeadwallNanoHyperspec())
    region.findScanLines()
    region.plot()
