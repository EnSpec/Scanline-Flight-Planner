#TODO: Use PyQt5 instead
from cefpython3 import cefpython as cef
import platform
import sys
import os
import glob
import time
#from multiprocessing import Process,Queue
from threading import Thread
from queue import Queue
try:
    import ScanArea
    import Spectrometer
except ImportError:
    #don't know how to properly import both standalone and in-module
    from . import ScanArea
    from . import Spectrometer
from tkinter import Tk,filedialog
Tk().withdraw()

FILE_QUEUE = Queue()
def TkSaveSubProc(tQ):
    while True:
        args = tQ.get()
        fmt = args[1]
        if fmt is None:
            return
        if 'Load' in fmt:
            callback = args[0]
        else:
            region = args[0]
            if region is None:
                continue
        if 'SHP' in fmt:
            fname = filedialog.askdirectory()
            if isinstance(fname,str):
                try:
                    region.toShapeFile(fname)
                except FileNotFoundError:
                    pass
        elif 'GPX' in fmt:
            fname = filedialog.asksaveasfilename(defaultextension=".gpx",
                    filetypes=[("Garmin GPX",".gpx")])
            if isinstance(fname,str):
                try:
                    region.toGPX(fname)
                except FileNotFoundError:
                    pass
        elif 'Waypoints' in fmt:
            fname = filedialog.asksaveasfilename(defaultextension=".txt",
                    filetypes=[("APM Waypoints file",".txt")])
            if isinstance(fname,str):
                try:
                    region.toWayPoints(fname)
                except FileNotFoundError:
                    pass
        elif 'Project' in fmt:
            fname = filedialog.asksaveasfilename(defaultextension=".shp",
                    filetypes=[("Project Shapefile",".shp")])
            if isinstance(fname,str):
                try:
                    region.toProjectShapeFile(fname,'US')
                except FileNotFoundError:
                    pass
        elif 'Load' in fmt:
            fname = filedialog.askopenfilename(defaultextension=".shp",
                    filetypes=[("Project Shapefile",".shp")])
            if isinstance(fname,str):
                try:
                    callback(fname)
                except FileNotFoundError:
                    pass
            


class External(object):
    noop = lambda:None

    def __init__(self):
        self._fname = None
        self._bearing = 45
        self._alt = 45
        self._scan_pd = .002
        self._home = None
        self._region = None
        self._spectrometer = None
        self._vehicle="fullscale"
        self._overshoot = 30 
        self._sidelap = .2
        self._names = []
        self.p = None
    
    def _isfloat(self,val):
        try:
            float(val)
            return True
        except:
            return False

    #setter hell
    def setOvershoot(self,val):
        if(self._isfloat(val)):
            self._overshoot = max(1,float(val))

    def setSidelap(self,val):
        if(self._isfloat(val)):
            self._sidelap = float(val)/100.

    def setHome(self,val):
        self._home = val

    def setAlt(self,val):
        if(self._isfloat(val)):
            self._alt = float(val)

    def setScanPd(self,val):
        if(self._isfloat(val)):
            self._scan_pd = float(val)
    
    def setNames(self,val):
        self._names=val
        print(self._names)

    def setBearing(self,val):
        if(self._isfloat(val)):
            self._bearing = float(val)

    def setScanPeriod(self,val):
        if(self._isfloat(val)):
            self._scan_pd = float(val)
    
    def setSpectrometer(self,val,js_callback=None):
        try:
            self._spectrometer = Spectrometer.spectrometerByName(val)()
        except KeyError:
            #got an unknown spectrometer name, silently pass
            return
        if(js_callback):
            js_callback.Call(self._spectrometer.fieldOfView,
                    self._spectrometer.crossFieldOfView,
                    self._spectrometer.pixels)

    def setCustomSpectrometer(self,fov,ifov,px):
        fov = float(fov)
        ifov = float(ifov)
        px = int(px)
        self._spectrometer = Spectrometer.Spectrometer(fov,ifov,px,'Custom')

    def setVehicle(self,val):
        self._vehicle = val

    def getScanSpeed(self,js_callback):
        if self._region:
            self._region._spectrometer.setFramePeriod(self._scan_pd)
            speed = "%.2f"%self._region.scanVelocity
        else:
            speed = "0"
        js_callback.Call(speed,self.noop)

    def loadFile(self,js_callback):
        callback = lambda f:self.finishLoad(f,js_callback)
        FILE_QUEUE.put((callback,'Load'))

    def finishLoad(self,fname,js_callback):
        print("Callback called")

    def polygonizePoints(self,points,js_callback):
        area = ScanArea.ScanArea(points[0],points)
        js_callback.Call(area._perimeter,self.noop)

    def centerOfPoints(self,points,js_callback):
        area = ScanArea.ScanArea(points[0],points)
        js_callback.Call(area._center,self.noop)

    def createPath(self,coords,js_callback):
        if coords:
            region = ScanArea.ScanRegion.from2DLatLonArray(coords,self._home,
                    names = self._names)
        elif self._fname:
            region = ScanArea.ScanRegion.fromFile(self._fname,self._home)
        else:
            return
        region.setVehicle(self._vehicle)
        region.setAltitude(self._alt)
        region.setBearing(self._bearing)
        region.setSidelap(self._sidelap)
        region.setOvershoot(self._overshoot)

        region.setFindScanLineBounds(True)
        scanner = self._spectrometer or Spectrometer.HeadwallNanoHyperspec()
        scanner.setFramePeriod(self._scan_pd)
        px_size = scanner.pixelSizeAt(self._alt)
        region.setSpectrometer(scanner)
        region.findScanLines()
        coords = region.flattenCoords()
        bounds= region.boundBox
        scanlines=region.scanLineBoundBoxes
        dist = "%.2f"%(region.totalScanLength/1000)
        speed = "%.2f"%region.scanVelocity
        self._region = region
        js_callback.Call(coords,bounds,dist,speed,px_size,scanlines)

    def savePath(self,fmt):
        if self._region is None:
            return
        FILE_QUEUE.put((self._region,fmt))
        #self.p.join()

def main():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    url= 'file://%s/gui/index.html'%script_dir
    check_versions()
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error

    p = Thread(target=TkSaveSubProc,args=(FILE_QUEUE,))
    p.start()
    
    cef.Initialize()
    #set up a browser
    window_info = cef.WindowInfo()
    window_info.SetAsChild(0, [0,0,1280,720])
    browser = cef.CreateBrowserSync(
            window_title="PushBroom Planner",
            url=url, window_info=window_info)
    frame = browser.GetMainFrame()
    #set up the browser's javascript bindings
    external = External()
    bindings = cef.JavascriptBindings()
    bindings.SetObject("external",external)
    browser.SetJavascriptBindings(bindings)
    #enter main loop
    cef.MessageLoop()
    cef.Shutdown()
    #send the (overengineered) save dialog a poison pill
    FILE_QUEUE.put((None,None))
    p.join()


def check_versions():
    print("[{prog}] CEF Python {ver}".format(prog=sys.argv[0],ver=cef.__version__))
    print("[{prog}] Python {ver} {arch}".format(prog=sys.argv[0],
          ver=platform.python_version(), arch=platform.architecture()[0]))
    assert cef.__version__ >= "55.3", "CEF Python v55.3+ required to run this"


if __name__ == '__main__':
    main()
