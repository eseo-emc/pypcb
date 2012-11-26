# -*- coding: windows-1252 -*-
from geometry import *
from stroketext import *

lightSpeed = 2.99792458e8*1e3 #mm/s

class GtemCard():
    def __init__(self,pcbSize=105.,cellOpeningWidth=93.5,wallThickness=2.0,frequencyLimit = 18e9,noGroundFraction=0.3):
        ## board outline creation
        self.pcbSize = pcbSize
        self.bottomWidth = cellOpeningWidth - wallThickness #45 degree taper
        self.frequencyLimit = frequencyLimit
        self.noGroundFraction = noGroundFraction
        
    def center(self):
        return Location(self.pcbSize/2,self.pcbSize/2)
     
    def stitchingPitch(self):
        waveLength = 2e8/self.frequencyLimit
        return m(waveLength/10)
           
    def draw(self,stack):
        self.groundPlane = Rectangle(Arrow(Location(0.,0.),E),self.pcbSize,self.pcbSize)
        self.layerMarker = LayerMarker(Arrow(Location(0.,0.),E), 4)
        
        for face in stack:
            Rectangle(rectangle=self.groundPlane,gerberLayer=face.copper[0]).draw()
        Rectangle(rectangle=self.groundPlane,gerberLayer=stack.mechanical[0],apertureNumber = stack.mechanicalAperture).draw()
 
        bottomCornerHeight = 6.0
        Rectangle(rectangle=self.groundPlane,gerberLayer = stack[3].solderMask[0]).draw()

        groundVoidRectangle(self.center(),self.bottomWidth,bottomCornerHeight,outset=-2*stack.classification.solderMaskMisalignment).draw(stack[3].solderMask[1])
        groundVoidRectangle(self.center(),self.bottomWidth,bottomCornerHeight).draw(stack[3].copper[1])
        groundVoidRectangle(self.center(),self.bottomWidth,bottomCornerHeight,outset=stack[2].depth-stack[3].depth).draw(stack[2].copper[1])
        groundVoidRectangle(self.center(),self.bottomWidth,bottomCornerHeight,outset=stack[1].depth-stack[3].depth).draw(stack[1].copper[1])
        
        extraGroundPlane = Rectangle(Arrow(self.center()-self.bottomWidth*Vector([0.5,0.5-self.noGroundFraction]),E),
                                     self.bottomWidth,
                                     (1-self.noGroundFraction)*self.bottomWidth)


        Rectangle(rectangle=extraGroundPlane,gerberLayer=stack[2].copper[2])
        Rectangle(rectangle=extraGroundPlane,gerberLayer=stack[1].copper[2])
        
        stitchingPitch = max(self.stitchingPitch(),stack.classification.viaStitchingPitch(stack.classification.minimumFinishedHoleDiameter))
        
        def viaStamp(arrowAlongBorder):
            MinimumVia(arrowAlongBorder.turnedRight()).draw(stack)     
        extraGroundPlane.outline().lines()[0].reversed().stamp(stitchingPitch,viaStamp,center=True)
        groundVoidRectangle(self.center(),self.bottomWidth,bottomCornerHeight).lines().stamp(stitchingPitch,viaStamp)
        
        
        ## registration holes
        holeDiagonal = 129.0
        holeRadius = holeDiagonal/numpy.sqrt(2)/2
        holeCoordinates = numpy.array([[-1,-1],
                                       [-1,+1],
                                       [+1,+1],
                                       [+1,-1]])*holeRadius + self.center()
        for coordinate in holeCoordinates.tolist():
            stack.addHole(Hole(Location(numpy.array(coordinate)),3.5,plated=False))
            
        for file in [stack.top,stack.innerOneFile,stack.innerTwoFile,stack.bottom]:
            self.layerMarker.draw(file)

class ESensor:
    def __init__(self,startArrow,face,diameter=3.):
        self.startArrow = startArrow
        self.diameter = diameter
        self.face = face
    def draw(self):
#        Circle(center=self.startArrow.origin,diameter=self.diameter).draw(self.face.copper[10])
#        Via(self.startArrow.origin,self.face.stack.classification.minimumFinishedHoleDiameter).draw(self.face.stack)
        connector = MolexSma(self.startArrow,signalFaceDiameterTuples=[(self.face,self.diameter)],face=self.face.opposite)
        connector.draw()
        
        Circle(self.startArrow.origin,self.diameter*2,self.face.solderMask[10]).draw()              
        
        StrokeText(connector.labelArrow,'E (° {diameter:.2f}mm)'.format(diameter=self.diameter),self.face.opposite.silkscreen[0],align=0).draw()

class HSensor:
    def __init__(self,startArrow,face,length=0.):
        self.startArrow = startArrow
        self.extraLength = 0.
        self.face = face
    def draw(self):
                
        productionHoleDiameter = self.face.stack.classification.minimumProductionHoleDiameter
        finishedHoleDiameter = self.face.stack.classification.finishedHoleDiameter(productionHoleDiameter)
        traceWidth = self.face.stack.classification.minimumViaPad(finishedHoleDiameter)
        
        connector = MolexSma(self.startArrow,face=self.face.opposite,signalFaceDiameterTuples=[(self.face,traceWidth)])
        connector.draw()        
        
        traceLength = 0.5*connector.groundGapDiameter + 0.5*traceWidth + self.extraLength
        trace = LineSegment(traceLength,self.startArrow)
        trace.paint(self.face.copper[10],traceWidth)

        Via(trace.endArrow.origin,finishedHoleDiameter,padFaceDiameterTuples=[(self.face,traceWidth)],skipFaces=[self.face.opposite]).draw(self.face.stack)
        
        Circle(self.startArrow.origin,(traceLength+0.5*traceWidth)*2.*2.,self.face.solderMask[10]).draw()      
        
        loopLength = traceLength - productionHoleDiameter
        StrokeText(connector.labelArrow,'H ({loopLength:.2f}x{height:.2f}mm)'.format(loopLength=loopLength,height=self.face.depth-self.face.thickness),self.face.opposite.silkscreen[0],align=0).draw()

        
class Via(object):
    def __init__(self,location=None,finishedHoleDiameter=None,padFaceDiameterTuples=[],antipadDiameter=None,isolateFaces=[],skipFaces=[]):
        self.location = location
        self.finishedHoleDiameter = finishedHoleDiameter
        self.padFaceDiameterTuples = padFaceDiameterTuples
        self.isolateFaces = isolateFaces
        self.skipFaces = skipFaces
        self.antipadDiameter = antipadDiameter
    def draw(self,stack):
        facesNeedAntipad = stack[:]
        maximumFinishedHoleSize = +numpy.inf
        largestPadDiameter = None
                
        for (face,padDiameter) in self.padFaceDiameterTuples:
            Circle(self.location,padDiameter,face.copper[20]).draw()
            if face in self.isolateFaces:
                Circle(self.location,stack.classification.minimumViaClearPad(padDiameter),face.copper[11]).draw()
            maximumFinishedHoleSize = min(stack.classification.maximumFinishedHoleDiameter(padDiameter),maximumFinishedHoleSize)
            largestPadDiameter = max(padDiameter,largestPadDiameter)
            facesNeedAntipad.remove(face)
        for face in self.skipFaces:
            facesNeedAntipad.remove(face)
        
        if not self.antipadDiameter:
            self.antipadDiameter = largestPadDiameter
        if self.antipadDiameter:
            for face in facesNeedAntipad:
                Circle(self.location,self.antipadDiameter,face.copper[21]).draw()
          
        if not self.finishedHoleDiameter:
            self.finishedHoleDiameter = maximumFinishedHoleSize
        assert self.finishedHoleDiameter <= maximumFinishedHoleSize
        stack.addHole(Hole(self.location,self.finishedHoleDiameter,plated=True))
            
class MinimumVia(Via):
    def __init__(self,startArrow=None,*args,**kwargs):
        super(MinimumVia,self).__init__(*args,**kwargs)
        self.startArrow = startArrow
    def draw(self,stack):
        if not self.finishedHoleDiameter:
            self.finishedHoleDiameter = stack.classification.minimumFinishedHoleDiameter
        self.padDiameter = stack.classification.viaClearance(self.finishedHoleDiameter)
        if type(self.location) == type(None):
            self.location = self.startArrow.along(self.padDiameter)
        Via.draw(self,stack)

class MolexSma:
    '''http://www.molex.com/pdm_docs/sd/732511850_sd.pdf'''
    mountingHoleClearance = 3.58
    mountingHoleDiameter = 1.6

    groundPadDiameter = 4.32 + 0.5
    groundGapDiameter = 2.57
    signalPadDiameter = 0.76


    def __init__(self,startArrow,face,signalFaceDiameterTuples=[],groundFaces=[],groundStartAngle=0.,groundStopAngle=None,groundVias=10):
        self.startArrow = startArrow
        self.face = face
        self.signalFaceDiameterTuples = signalFaceDiameterTuples
        self.groundStartAngle = groundStartAngle
        self.groundStopAngle = groundStopAngle
        self.groundVias = groundVias
        self.groundFaces = groundFaces
    @property
    def center(self):
        return self.startArrow.origin 
    @property
    def labelArrow(self):
        return self.startArrow.alongArrow(3.5).turnedRight()
    def draw(self):     
        stack = self.face.stack
        Circle(self.center,self.groundPadDiameter+stack.classification.solderMaskMisalignment*2,self.face.solderMask[10]).draw()       
        Circle(self.center,self.groundPadDiameter,self.face.copper[10]).draw()
        Circle(self.center,self.groundGapDiameter,self.face.copper[11]).draw()
              
        # Central via
        Via(self.center,antipadDiameter=self.groundGapDiameter,padFaceDiameterTuples=[(self.face,self.signalPadDiameter)]+self.signalFaceDiameterTuples).draw(stack)        
        
        # Ground vias
        if len(self.groundFaces) > 0:
            if self.groundStopAngle:
                viaAngles = numpy.linspace(self.groundStartAngle,self.groundStopAngle,self.groundVias)
            else:
                viaAngles = numpy.linspace(self.groundStartAngle,self.groundStartAngle+2.*numpy.pi,self.groundVias,endpoint=False)
            
            for viaAngle in viaAngles:
                MinimumVia(self.startArrow.rotated(viaAngle).alongArrow(self.groundGapDiameter/2.),skipFaces=[self.face]+self.groundFaces).draw(stack)

        # Mounting holes
        stack.addHole(Hole(self.startArrow.right(self.mountingHoleClearance),self.mountingHoleDiameter,plated=False))
        stack.addHole(Hole(self.startArrow.left(self.mountingHoleClearance),self.mountingHoleDiameter,plated=False))

class MolexSmdSma(DrawGroup):
    padSpacing = 4.75
    groundPadSize = 1.91
    centerPadSize = 1.52    
    
    def __init__(self,startArrow,face):
        DrawGroup.__init__(self)        
        self.startArrow = startArrow
        self.face = face
        
        sides = Square(centerArrow=self.startArrow, width=self.padSpacing).outline().lines()
        for side in sides:
            groundCopperPad = Square(centerArrow=side.startArrow, width=self.groundPadSize)
            groundPad = RectanglePad(groundCopperPad,self.face,solderMask = True)
            self.append(groundPad)
            signalCopperPad = Circle(self.startArrow.origin,self.centerPadSize)
            signalPad = CirclePad(signalCopperPad,self.face,solderMask = True,isolation=None)
            self.append(signalPad)

class AgilentProbePads(object):
    groundRecess = 0.49
    groundOutsets = [-2.45,+1.95]
    padDiameter = 1.0
    
    def __init__(self,startArrow,face):
        self.startArrow = startArrow
        self.face = face
    def draw(self,groundVias=True):
        Circle(self.startArrow.origin,self.padDiameter).draw(self.face.copper[10])
        Via(self.startArrow.origin,padFaceDiameterTuples)
        
               
class RingResonator(DrawGroup):
    '''
    J. Vorlicek, J. Rusz, L. Oppl, and J. Vrba. Complex permittivity measurement of substrates using ring resonator. In Technical Computing Bratislava, 2010.
    http://phobos.vscht.cz/konference_matlab/MATLAB10/full_text/107_Vorlicek.pdf
    '''

    connectorClass = MolexSmdSma
    
    def __init__(self,face,traceWidth,firstResonanceFrequency,effectiveRelativePermittivity,startArrow=Arrow(Location(0,0),E)):
        self.startArrow = startArrow
        self.face = face
        self.firstResonanceFrequency = firstResonanceFrequency
        self.traceWidth = traceWidth
        self.effectiveRelativePermittivity = effectiveRelativePermittivity
        
        DrawGroup.__init__(self,
           [Circle(self.startArrow.origin,self.outerDiameter(),self.face.copper[10]),
            Circle(self.startArrow.origin,self.innerDiameter(),self.face.copper[11]),
            Circle(self.startArrow.origin,self.outerDiameter()+2.*self.traceWidth,self.face.solderMask[10]),
            StrokeText(self.startArrow,'°{innerDiameter:.2f}mm'.format(innerDiameter=self.innerDiameter()),self.face.silkscreen[0],align=0) ])

    def innerDiameter(self):
        velocity = lightSpeed/numpy.sqrt(self.effectiveRelativePermittivity)
        waveLength = velocity/self.firstResonanceFrequency  
        return waveLength # http://www.microwaves101.com/encyclopedia/mitered_bends.cfm
    def outerDiameter(self):
        return self.innerDiameter() + 2.*self.traceWidth 
    def endArrows(self):
        gapWidth = self.face.stack.classification.minimumOuterPadToPad      
        outset = self.outerDiameter()/2.+gapWidth*2.
        
        return [self.startArrow.alongArrow(outset),
                self.startArrow.turnedRight().alongArrow(outset)]
        
    

def groundVoidRectangle(centerLocation,width,cornerHeight,outset=0.):
    radius = width/2
    outlineCoordinates = numpy.array([[-radius+cornerHeight,-radius],
                                      [+radius-cornerHeight,-radius],
                                      [+radius,-radius+cornerHeight],
                                      [+radius,+radius-cornerHeight],
                                      [+radius-cornerHeight,+radius],
                                      [-radius+cornerHeight,+radius],
                                      [-radius,+radius-cornerHeight],
                                      [-radius,-radius+cornerHeight]]) + centerLocation
    
    outline = ClosedContour()
    for coordinate in outlineCoordinates.tolist():
        stroke = Stroke(Location(numpy.array(coordinate)))
        outline += [stroke]
    
    return outline.outset(outset)
    
if __name__ == '__main__':
    from pypcb import *
    GtemCard().draw(Stack(4))

        