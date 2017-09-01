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
    
    def echo(self,js_callback):
        try:
            js_callback.Call(self.ser.recieve_chars(),self.noop)
        except AttributeError as e:
            return
        except Exception as e:
            self.raise_serial_err(e)


    def setHome(self,lat,lon):
        self._home = {'lat':lat,'lon':lon}

    def setAlt(self,val):
        self._alt = float(val)

    def setScanPd(self,val):
        self._scan_pd = float(val)

    def setBearing(self,val):
        self._bearing = float(val)

    def loadFile(self,js_callback):
        fname = filedialog.askopenfilename()
        if isinstance(fname,str) and os.path.exists(fname):
            self._fname = fname
            fname = os.path.split(self._fname)[1]
            js_callback.Call(fname,self.noop)

    def polygonizePoints(self,points,js_callback):
        area = ScanArea.ScanArea(points[0],points)
        print(area._perimeter)
        js_callback.Call(area._perimeter,self.noop)

    def createPath(self,coords,js_callback):
        if coords:
            region = ScanArea.ScanRegion.from2DLatLonArray(coords,self._home)
        else:
            region = ScanArea.ScanRegion.fromFile(self._fname,self._home)
        region.setAltitude(self._alt)
        region.setBearing(self._bearing)
        scanner = Spectrometer.HeadwallNanoHyperspec()
        scanner.setFramePeriod(0.005)
        region.setSpectrometer(scanner)
        coords = region.findScanLines()
        bounds= region.boundBox
        self._region = region
        js_callback.Call(coords,bounds)

    def savePath(self):
        if self._region is None:
            return
        fname = filedialog.askopenfilename()
        self._region.toWayPoints(fname)



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
