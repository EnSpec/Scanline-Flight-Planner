# Hello world example. Doesn't depend on any third party GUI framework.
# Tested with CEF Python v55.3+.

from cefpython3 import cefpython as cef
import platform
import sys
import os
import glob
import time
import ScanArea
import Spectrometer
from tkinter import Tk,filedialog
Tk().withdraw()


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
        self._vehicle="quadcopter"
        self._overshoot = 30 
        self._sidelap = .2
    
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

    def setBearing(self,val):
        if(self._isfloat(val)):
            self._bearing = float(val)

    def setScanPeriod(self,val):
        if(self._isfloat(val)):
            self._scan_pd = float(val)
    
    def setSpectrometer(self,val):
        self._spectrometer = Spectrometer.spectrometerByName(val)()

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
        fname = filedialog.askopenfilename()
        if isinstance(fname,str) and os.path.exists(fname):
            self._fname = fname
            fname = os.path.split(self._fname)[1]
            js_callback.Call(fname,self.noop)

    def polygonizePoints(self,points,js_callback):
        area = ScanArea.ScanArea(points[0],points)
        js_callback.Call(area._perimeter,self.noop)

    def centerOfPoints(self,points,js_callback):
        area = ScanArea.ScanArea(points[0],points)
        js_callback.Call(area._center,self.noop)

    def createPath(self,coords,js_callback):
        if coords:
            region = ScanArea.ScanRegion.from2DLatLonArray(coords,self._home)
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
        region.setSpectrometer(scanner)
        coords = region.findScanLines()
        bounds= region.boundBox
        scanlines=region.scanLineBoundBoxes
        dist = "%.2f"%(region.totalScanLength/1000)
        speed = "%.2f"%region.scanVelocity
        self._region = region
        js_callback.Call(coords,bounds,dist,speed,scanlines)

    def savePath(self):
        if self._region is None:
            return
        if self._vehicle == 'fullscale':
            fname = filedialog.askdirectory()
            if isinstance(fname,str):
                try:
                    self._region.toShapeFile(fname)
                except FileNotFoundError:
                    pass
        if self._vehicle == 'quadcopter':
            fname = filedialog.asksaveasfilename()
            if isinstance(fname,str):
                try:
                    self._region.toWayPoints(fname)
                except FileNotFoundError:
                    pass


def main():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    url= 'file://%s/gui/index.html'%script_dir
    check_versions()
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error

    
    cef.Initialize()
    #set up a browser
    window_info = cef.WindowInfo()
    window_info.SetAsChild(0, [0,0,1280,720])
    browser = cef.CreateBrowserSync(
            window_title="NanoSpec Scan Route Preview", 
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


def check_versions():
    print("[{prog}] CEF Python {ver}".format(prog=sys.argv[0],ver=cef.__version__))
    print("[{prog}] Python {ver} {arch}".format(prog=sys.argv[0],
          ver=platform.python_version(), arch=platform.architecture()[0]))
    assert cef.__version__ >= "55.3", "CEF Python v55.3+ required to run this"


if __name__ == '__main__':
    main()
