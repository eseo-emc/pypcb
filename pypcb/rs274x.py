import numpy
import os

from geometry import *

class GerberLayer(object):
    def __init__(self,gerberFile,inverted=False):
        self.gerberFile = gerberFile
        self.inverted = inverted
        self.drawCommands = ''
    def __str__(self):
        return self.layerPolarity()+self.drawCommands
    def layerPolarity(self):
        if self.inverted:
            return '%LPC*%\n' # Clear
        else:
            return '%LPD*%\n' # Dark
            
    def addDrawCommands(self,commands):
        self.drawCommands += commands
    def flashAperture(self,location,apertureNumber):
        self.addDrawCommands('G54D{apertureNumber:02d}*\n{location}D03*\n'.format(apertureNumber=apertureNumber,location=self.gerberFile.locationToString(location)))

    def addSingleStroke(self,fromLocation,toLocation,apertureNumber):
        # TODO: merge with closed outline underneath
        edgeCommands = self.goTo(fromLocation,exposure=False)
        edgeCommands += self.goTo(toLocation)
        self.addDrawCommands('D{apertureNumber:02d}*\nG75*\n'.format(apertureNumber=apertureNumber) + edgeCommands)
    
    def addOutline(self,Segments,apertureNumber=None):
        def safeOffset(absoluteOrigin,point):
            if absoluteOrigin is not None:
                return absoluteOrigin - point
            else:
                return None
        
        
        edgeCommands = self.goTo(Segments[0].targetLocation,exposure=False)
        assert type(Segments[0]) == Stroke
        if apertureNumber:
            Segments.append(Segments[0])
        
        for (Segment,previousSegment) in zip(Segments[1:],Segments[:-1]):
            if type(Segment) == Stroke:
                edgeCommands += self.goTo(Segment.targetLocation)
            else:
                edgeCommands += self.goTo(Segment.targetLocation,relativeCircleOrigin=safeOffset(Segment.origin,previousSegment.targetLocation),counterClockWise=Segment.counterClockWise)
        if apertureNumber:
            self.addDrawCommands('D{apertureNumber:02d}*\nG75*\n'.format(apertureNumber=apertureNumber) + edgeCommands)
        else:
            self.addDrawCommands('G36*\nG75*\n' + edgeCommands + 'G37*\n')
    
    def goTo(self,edgePoint,exposure=True,relativeCircleOrigin=None,counterClockWise=None):
        exposureCommand = 'D01' if exposure else 'D02'
        if relativeCircleOrigin == None:
            return 'G01' + self.gerberFile.locationToString(edgePoint) + exposureCommand + '*\n'  
        else:
            assert counterClockWise is not None
            circularInterpolationCommand = 'G03' if counterClockWise else 'G02'
            return circularInterpolationCommand + self.gerberFile.locationToString(edgePoint) + self.gerberFile.locationToString(relativeCircleOrigin,offset=True) + exposureCommand + '*\n'
            
class GerberFile(object):
    @classmethod
    def comment(cls,commentString):
        return 'G04 {0}*\n'.format(commentString)
        
    def __init__(self,name,inverted=False,decimalPlaces=5,physicalLayer=None,export=True):
        self.name = name
        self.inverted = inverted
        self.decimalPlaces = decimalPlaces
        self._integerPlaces = 5
        self.physicalLayer = physicalLayer
        self.export = export
        
        self.layers = []
        self.addLayer()
        self.apertures = {}
    def addLayer(self,inverted=False):
        newLayer = GerberLayer(self,inverted)
        self.layers.append(newLayer)
        return newLayer
    def getLayerByName(self,name):
        raise DeprecationWarning
        for layer in self.layers:
            if layer.name == name:
                return layer
    def __getitem__(self,layerNumber):
        if len(self.layers) > layerNumber:
            return self.layers[layerNumber]
        else:
            previousLayer = self[layerNumber-1]
            return self.addLayer(inverted=not(previousLayer.inverted))
    def locationToString(self,location,offset=False):
        def lengthToString(lengthInMm):
            assert lengthInMm <= 10**self._integerPlaces
            return '{length:+0{decimalPlaces}d}'.format(length=int(round(lengthInMm*10**self.decimalPlaces)),decimalPlaces=self.decimalPlaces+1)
        string = 'X{x}Y{y}'.format(x=lengthToString(location[0]),y=lengthToString(location[1]))
        if offset:
            string = string.replace('X','I').replace('Y','J')
        return string
        
    def addRectangularAperture(self,width,height):
        return self._addAperture('R,{width:.{precision}f}X{height:.{precision}f}'.format(width=width,height=height,precision=self.decimalPlaces))
    def addCircularAperture(self,diameter):
        return self._addAperture('C,{diameter:.{precision}f}'.format(diameter=diameter,precision=self.decimalPlaces))
    def _addAperture(self,definition):
        if len(self.apertures) == 0:
            apertureNumber = 10
        else:                  
            apertureNumber = sorted(self.apertures.keys())[-1]+1
        self.apertures.update({apertureNumber:definition})
        return apertureNumber
    def _aperturesAsString(self):
        string = ''
        for aperture in iter(sorted(self.apertures.items())):
            string += '%ADD{aperture[0]:02d}{aperture[1]}*%\n'.format(aperture=aperture)
        return string
        
    def __str__(self):
        string = self.comment('===== Begin FILE IDENTIFICATION =====')
        string += self.comment('File Format:  Gerber RS274X')
        string += self.comment('===== End   FILE IDENTIFICATION =====')
        string += '%FSLAX5{decimalPlaces:d}Y5{decimalPlaces:d}*%\n'.format(decimalPlaces=self.decimalPlaces) + \
                  '%MOMM*%\n' + \
                  '%SFA1.0B1.0*%\n%OFA0.0B0.0*%\n'
        # omit Leading zeroes, Absolute coordinates, 5.decimalPlaces coordinate format, mm
        #GerberFile.comment('Format specification') + \
        
        string += self.comment('Image metadata')
        if self.physicalLayer is not None:
            string += self.comment('Layer_Physical_Order={0:d}'.format(self.physicalLayer))
        string += self.imageName()
        string += self.imagePolarity()
        
        string += self._aperturesAsString()
        
        for layer in self.layers:
            string += str(layer)
            
        string += 'M02*' # program stop
        return string

    def writeOut(self,name=None):
        if self.export:
            if name == None:
                name = self.name
            
            outputDirectory = os.path.abspath('../output')
            if not os.path.exists(outputDirectory):
                print 'Creating output directory ' + outputDirectory
                os.makedirs(outputDirectory)
            self.fileHandle = open(outputDirectory + '/' + name + '.gbr','w')
                
            self.fileHandle.write(str(self))
            self.fileHandle.close()

    def imageName(self):
        return '%IN{0}*%\n'.format(self.name.upper())

    def imagePolarity(self):
        if self.inverted:
            return '%IPNEG*%\n' 
        else:
            return '%IPPOS*%\n'



if __name__ == '__main__':
    import nose
    nose.run(argv=['-w','../test','-v'])