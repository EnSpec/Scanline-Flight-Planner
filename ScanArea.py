import LonLatMath as llmath
import numpy as np
import time
import Spectrometer
import KMLParse
import SHPParse
import WaypointParse
from shapely import geometry
import os


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
    def __init__(self,home,perimeter,spectrometer=None,alt = None,bearing=None,
            vehicle='quadcopter',overshoot=0,find_scanline_bounds=False):
        self._home = home
        self._perimeter = perimeter
        self.setBearing(bearing)
        self._buildEdges()
        self._coords = []
        self._alt = alt
        self._spectrometer = spectrometer
        self._boundBox = None
        self._waypoints = []
        self._sidelap = 0
        self._overshoot = 0
        self._find_bounds = find_scanline_bounds
        self._scanline_bounds = []
    
    def setHome(self,home):
        self._home = home

    def setOvershoot(self,overshoot):
        #distance to pass beyond borders of scanarea before turning
        #useful for fullscale flight vehicles
        self._overshoot = overshoot

    def setFindScanLineBounds(self,find_bounds):
        self._find_bounds = find_bounds

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

    def addWayPoint(self,waypoint):
        self._waypoints.append(waypoint)

    @property
    def boundBox(self):
        """return the Northeast and Southwest corners of the area"""
        NS = sorted(self._perimeter,key=lambda p:p['lat'])
        WE = sorted(self._perimeter,key=lambda p:p['lon']) 
        SW = {'lat':NS[0]['lat'],'lon':WE[0]['lon']}
        NE = {'lat':NS[-1]['lat'],'lon':WE[-1]['lon']}
        return [SW,NE]

    @property
    def scanLineBoundBoxes(self):
        return self._scanline_bounds

    def _computeCenter(self,perimeter):
        """Find the center of the set of points. This is the cartesian center
        rather than geographic, hopefully it doesn't make that much of a
        difference on the scale we're working at.
        """
        #use Shapely's builtin centroid calculator
        coordlist = [(l['lat'],l['lon'])for l in self._perimeter]
        center = geometry.Polygon(coordlist).centroid.coords
        print(center)
        return {'lat':center[0][0],'lon':center[0][1]}

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

    def setSidelap(self,sidelap):
        self._sidelap = sidelap

    def _addScanlineBoundBox(self,scan_edge):
        bound_box = []
        normal_dir = (scan_edge.bearing+90)%360
        antinormal_dir = (normal_dir+180)%360
        bound_box.append(llmath.atDistAndBearing(scan_edge.start,
            self._scanline_width/2,normal_dir))
        bound_box.append(llmath.atDistAndBearing(scan_edge.start,
            self._scanline_width/2,antinormal_dir))
        bound_box.append(llmath.atDistAndBearing(scan_edge.end,
            self._scanline_width/2,antinormal_dir))
        bound_box.append(llmath.atDistAndBearing(scan_edge.end,
            self._scanline_width/2,normal_dir))

        self._scanline_bounds.append(bound_box)


    def _findIntersectionsInDirection(self,direction,start,curr_point=None):
        """Travel self._travel_width meters in direction, then scan for an intersect
        with an edge both parallel and antiparallel to self._leading_edge.
        If no intersect is found in either direction, we've exited the ScanArea
        and can return
        """
        curr_point = curr_point or llmath.atDistAndBearing(
                self._perimeter[0],self._travel_width,direction)
        found_intersect = True
        
        dir_coords = [start]
        while found_intersect:
            #don't check the leading edge
            new_points = []
            for t_dir in self._travel_dir,self._opp_dir:
                for edge in self._edges:
                    intersect = edge.intersection(curr_point,t_dir)
                    if intersect:# and len(new_points) < 2:
                        new_points.append(intersect['point'])
                        found_intersect = True
            
            curr_point = llmath.atDistAndBearing(
                     curr_point,self._travel_width,direction)
            #append new_points to dir_coords such that the new_point closer 
            #to the last coord is added first
            if len(new_points) > 0:
                #if we cross multiple times (eg in a concave area), just take
                #the two most extreme
                if len(new_points) > 2:
                    n = len(new_points)
                    combos = [(i,j+1,j-i)for i in range(n)for j in range(i+1,n)]
                    new_edge = sorted([Edge(*new_points[slice(*c)])
                        for c in combos], key=lambda x:x.length)[-1]
                else:
                    new_edge = Edge(*new_points)

                new_points = new_edge.endpoints
                if self._find_bounds:
                    self._addScanlineBoundBox(new_edge)

                #if we have an overshoot, stick 2 additional points beyond 
                #the extrema
                if self._overshoot > 0:
                    os1 = llmath.atDistAndBearing(new_points[0],
                            self._overshoot,(180+new_edge.bearing)%360)
                    os2 = llmath.atDistAndBearing(new_points[1],
                            self._overshoot,new_edge.bearing)
                    new_points = [os1,*new_points,os2]

                dists_from_coords = new_edge.distanceTo(dir_coords[-1])
                if dists_from_coords[0] > dists_from_coords[1]:
                    dir_coords += new_points[::-1]
                else:
                    dir_coords += new_points
            else:
                found_intersect = False
        return dir_coords[1:]

    def findScanLines(self):
        self._scanline_bounds = []
        self._coords = [self._home]
        self._scanline_width =self._spectrometer.swathWidthAt(self._alt) 
        self._travel_width = self._scanline_width*(1-self._sidelap)
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
                    self._center,self._travel_width,parallel_dir2)

        self._coords += self._findIntersectionsInDirection(
                parallel_dir2,self._coords[-1],first_point)

        #flip things around so that we start by travelling the shorter
        #route from home at the beginning
        end_edges = Edge(self._coords[1],self._coords[-2])
        end_dists = end_edges.distanceTo(self._home)
        if end_dists[0] > end_dists[1]:
            print(len(self._coords),end=' ')
            self._coords = [self._home]+self._coords[1:][::-1]
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

    def plot(self,show=True,include=['perimeter','coords','bounds']):
        from matplotlib import pyplot as plt
        if 'perimeter' in include:
            self._plotPoints(self._perimeter+[self._perimeter[0]],
                    color='blue',lw=2)
        if 'bounds' in include:
            for line in self._scanline_bounds:
                self._plotPoints(line+[line[0]],color='purple',lw=2)
        if self._coords and 'coords' in include:
            self._plotPoints(self._coords,color='r',lw=2)
        if 'perimeter' in include:
            self._plotPoints(self._center,color='g',marker='o')
        if show:
            plt.show()


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

    VEHICLES='quadcopter','fullscale'
    
    def __init__(self,home,spectrometer=None,alt = None,bearing=None,
            vehicle='quadcopter',overshoot=0,find_scanline_bounds=False):
        self._home = home
        self._scanareas = []
        self._waypoints = []
        self._spectrometer = spectrometer
        self._alt = alt 
        self._bearing = bearing
        self._sidelap = 0
        self._coords = None
        self._overshoot = overshoot
        self._vehicle = 'quadcopter'
        self._find_bounds = find_scanline_bounds

    def addWayPoint(self,waypoint):
        self._waypoints.append(waypoint)

    def addScanArea(self,scanarea):
        scanarea.setAltitude(self._alt)
        scanarea.setSpectrometer(self._spectrometer)
        scanarea.setBearing(self._bearing)
        self._scanareas.append(scanarea)

    #so many setters I think I went wrong somewhere
    def setAltitude(self,altitude):
        self._alt = altitude
        for sa in self.scanAreas:
            sa.setAltitude(self._alt)

    def setFindScanLineBounds(self,find_bounds):
        self._find_bounds = find_bounds
        for sa in self.scanAreas:
            sa.setFindScanLineBounds(self._find_bounds)

    def setSpectrometer(self,spectrometer):
        self._spectrometer = spectrometer
        for sa in self.scanAreas:
            sa.setSpectrometer(self._spectrometer)

    def setVehicle(self,vehicle):
        if not vehicle in self.VEHICLES:
            raise ValueError("Vehicle {} not supported.".format(vehicle))
        else:
            self._vehicle = vehicle

    def setOvershoot(self,overshoot):
        self._overshoot = overshoot
        for sa in self.scanAreas:
            sa.setOvershoot(self._overshoot)

    def setSidelap(self,sidelap):
        self._sidelap = sidelap
        for sa in self.scanAreas:
            sa.setSidelap(self._sidelap)

    def setBearing(self,bearing):
        if bearing == 90:
            #trig stuff in LatLonMath doesn't like 90
            bearing = 89.99
        self._bearing = bearing
        for sa in self.scanAreas:
            sa.setBearing(self._bearing)

    @property
    def allPerimeterPoints(self):
        points = []
        for area in self.scanAreas:
            points += area._perimeter
        return points

    @property
    def boundBox(self):
        points = self.allPerimeterPoints
        NS = sorted(points,key=lambda p:p['lat'])
        WE = sorted(points,key=lambda p:p['lon']) 
        SW = {'lat':NS[0]['lat'],'lon':WE[0]['lon']}
        NE = {'lat':NS[-1]['lat'],'lon':WE[-1]['lon']}
        return [SW,NE]

    @property
    def center(self):
        return self._scanareas[0]._center

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

    def _reorderScanAreas(self):
        """Order scan areas from closest to home to farthest from home"""
        def _prox_to_home(a):
            return min(Edge(*a.boundBox).distanceTo(self._home))
        self._scanareas.sort(key=_prox_to_home) 

    def findScanLines(self):
        """Find the scan lines of each ScanArea, then chain them together"""
        self._coords = [self._home]
        home = self._home
        self._reorderScanAreas()
        for sa in self.scanAreas:
            sa.setHome(home)
            new_coords = sa.findScanLines()[1:]
            self._coords+= new_coords
            home = self._coords[-1]
        
        if self._vehicle == 'fullscale':
            #full-scale airplanes don't need a home to be set
            self._coords = self._coords[1:]
        return self._coords

    @property
    def totalScanLength(self):
        sum_dist=0
        for i,coord in enumerate(self._coords[1:]):
            sum_dist+=llmath.distanceTo(coord,self._coords[i])

        sum_dist+=llmath.distanceTo(self._coords[0],self._coords[-1])
        return sum_dist

    @property
    def totalScanTime(self):
        return self.totalScanLength/self.scanVelocity

    @property
    def scanVelocity(self):
        return self._spectrometer.squareScanSpeedAt(self._alt)

    @property
    def scanLineBoundBoxes(self):
        boxes = []
        for sa in self._scanareas:
            boxes += sa.scanLineBoundBoxes
        return boxes

    def plot(self,show=True):
        for sa in self.scanAreas[:-1]:
            sa.plot(show=False,include=['perimeter','bounds'])
        self.scanAreas[-1]._plotPoints(self._coords,color='r',lw=2)
        self.scanAreas[-1].plot(show=True,include=['perimeter','bounds'])

    def toWayPoints(self,fname):
        assert self._vehicle == 'quadcopter'
        if self._coords is None:
            self.findScanLines()
        speed = self._spectrometer.squareScanSpeedAt(self._alt)
        WaypointParse.waypointsFromCoords(fname,
                self._coords,self._alt,self._bearing,speed)

    def toShapeFile(self,fname):
        assert self._vehicle == 'fullscale'
        if self._coords is None:
            self.findScanLines()
        speed = self._spectrometer.squareScanSpeedAt(self._alt)
        SHPParse.flightPlanFromCoords(fname,
                self._coords,self.scanLineBoundBoxes,self._alt,speed)
        
    
    @classmethod
    def from2DLatLonArray(Cls,coords,home=None,**kwargs):
        home = home or coords[0][0]
        region = Cls(home,**kwargs)
        for perimeter in coords:
            region.addScanArea(ScanArea(home,perimeter))
        return region

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
    
    @classmethod
    def fromSHPPoints(Cls,shp_fname,home=None,**kwargs):
        raise NotImplementedError
 
    @classmethod
    def fromKMLPoints(Cls,kml_fname,home=None,**kwargs):
        raise NotImplementedError

    @classmethod
    def fromFile(Cls,fname,home=None,**kwargs):
        #which function to use to instantiate from file
        FILE_FUNC_TREE={
                ".kml":{
                    "type":KMLParse.findRegionType,
                    "Polygon":Cls.fromKMLPolys,
                    "Point":Cls.fromKMLPoints
                },
                (".shp",".shx",".dbf"):{
                    "type":SHPParse.findRegionType,
                    "Polygon":Cls.fromSHPPolys,
                    "Point":Cls.fromSHPPoints
                },
        }
        ext = os.path.splitext(fname)[1].lower()
        for key in FILE_FUNC_TREE:
            if ext in key:
                dtype=FILE_FUNC_TREE[key]['type'](fname)
                return FILE_FUNC_TREE[key][dtype](fname,home,**kwargs)
        raise IOError("Unable to parse file {} into ScanRegion".format(fname))
            

if __name__ == '__main__':
    import sys
    region = ScanRegion.fromFile(sys.argv[1])
    if len(sys.argv) > 3:
        region.setAltitude(int(sys.argv[3]))
    else:
        region.setAltitude(60)
    if len(sys.argv) > 4:
        region.setBearing(int(sys.argv[4]))
    else:
        region.setBearing(45)
    if len(sys.argv) > 5:
        region.setSidelap(float(sys.argv[5]))
    region.setFindScanLineBounds(True)
    scanner = Spectrometer.HeadwallNanoHyperspec()
    scanner.setFramePeriod(0.005)
    region.setSpectrometer(scanner)
    region.setOvershoot(30)
    region.setVehicle('fullscale')

    region.findScanLines()
    region.toShapeFile(sys.argv[2])
