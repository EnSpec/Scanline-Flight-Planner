import numpy as np

class Spectrometer(object):
    """Class to represent an imaging spectrometer"""
    def __init__(self, fov, ifov, px,name='',frame_pd=.002):
        self._fov = fov
        self._ifov = ifov
        self._px = px
        self._frame_pd = frame_pd
        self._name = name

    def setFramePeriod(self,pd):
        self._frame_pd = pd

    @property
    def fieldOfView(self):
        return self._fov

    @property
    def crossFieldOfView(self):
        return self._ifov

    @property
    def scanLinePixels(self):
        return self._px

    @property
    def name(self):
        return self._name
    
    @property
    def frame(self):
        return self._frame_pd

    @property
    def pixels(self):
        return self._px

    def swathWidthAt(self,alt):
        return 2*alt*np.tan(np.radians(self.fieldOfView/2))
    
    def crossSwathWidthAt(self,alt):
        return 2*alt*np.tan(np.radians(self.crossFieldOfView/2))
    
    def altForPixelSize(self,px_size):
        return self._px*px_size/(2*np.tan(np.radians(self.fieldOfView/2)))

    def pixelSizeAt(self,alt):
        return self.swathWidthAt(alt)/self.scanLinePixels

    def squareScanSpeedAt(self,alt):
        """the speed the spectrometer must move at to record square pixels"""
        return self.crossSwathWidthAt(alt)/self._frame_pd
        

#Predefined Spectrometers
class AVIRISClassic(Spectrometer):
    def __init__(self):
        Spectrometer.__init__(self,34,0.027,677,"AVIRIS Classic")

class AVIRISNextGen(Spectrometer):
    def __init__(self):
        Spectrometer.__init__(self,36,0.023,640,"AVIRIS Next Gen")

class HeadwallNanoHyperspec(Spectrometer):
    def __init__(self):
        Spectrometer.__init__(self,15.9,0.0249,640,"Headwall Nano Hyperspec")

class HeadwallVNIR_SWIR_co_boresi(Spectrometer):
    def __init__(self):
        Spectrometer.__init__(self,20.887,0.030,380,"Headwall VNIR-SWIR co-boresi")

class SpecimFENIX(Spectrometer):
    def __init__(self):
        Spectrometer.__init__(self,32.3,0.028,384,"Specim FENIX")

class NorskElektroOp(Spectrometer):
    def __init__(self):
        Spectrometer.__init__(self,34,0.02,384,"Norsk Elektro Optikk HySpex")

def spectrometerByName(name):
    return {
        "AVIRIS Classic":AVIRISClassic,
        "AVIRIS Next Gen":AVIRISNextGen,
        "Headwall Nano Hyperspec":HeadwallNanoHyperspec,
        "Headwall VNIR-SWIR co-boresi":HeadwallVNIR_SWIR_co_boresi,
        "Specim FENIX":SpecimFENIX,
        "Norsk Elektro Optikk HySpex":NorskElektroOp
    }[name]


if __name__ == '__main__':
    spec = HeadwallNanoHyperspec()
    spec.setFramePeriod(0.005)
    print(spec.swathWidthAt(20.12))
    print(spec.crossSwathWidthAt(20.12))
    print(spec.squareScanSpeedAt(20.12))
    px_w = spec.pixelSizeAt(610)
    print(px_w)
    print(spec.altForPixelSize(px_w))
