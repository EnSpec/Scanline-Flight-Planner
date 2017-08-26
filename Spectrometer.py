import numpy as np

class Spectrometer(object):
    """Class to represent an imaging spectrometer"""
    def __init__(self, fov, px):
        self._fov = fov
        self._px = px


    @property
    def fieldOfView(self):
        return self._fov

    @property
    def scanLinePixels(self):
        return self._px

    def swathWidthAt(self,alt):
        return 2*alt*np.tan(np.radians(self.fieldOfView/2))

    def pixelSizeAt(self,alt):
        return self.swathWidthAt(alt)/self.scanLinePixels

#Predefined Spectrometers
class AVRISNextGen(Spectrometer):
    def __init__(self):
        Spectrometer.__init__(self,36,640)

class HeadwallNanoHyperspec(Spectrometer):
    def __init__(self):
        Spectrometer.__init__(self,15.9,640)

class HeadwallVNIR_SWIR_co_boresi(Spectrometer):
    def __init__(self):
        Spectrometer.__init__(self,20.887,380)

class SpecimFENIX(Spectrometer):
    def __init__(self):
        Spectrometer.__init__(self,32.3,384)
