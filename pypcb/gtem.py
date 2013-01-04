# -*- coding: windows-1252 -*-
from geometry import *
from stroketext import *
from copy import deepcopy

lightSpeed = m(2.99792458e8) #mm/s

class GtemCard():
    def __init__(self,pcbSize=105.,cellOpeningWidth=93.5,wallThickness=2.0,frequencyLimit = 18e9,noGroundFraction=0.26):
        self.pcbSize = pcbSize
        self.bottomWidth = cellOpeningWidth - wallThickness #45 degree taper
        self.frequencyLimit = frequencyLimit
        self.noGroundFraction = noGroundFraction
        
    def center(self):
        return Location(self.pcbSize/2,self.pcbSize/2)
     
    def stitchingPitch(self):
        waveLength = 0.66*lightSpeed/self.frequencyLimit
        return waveLength/10
           
    def draw(self,stack):
        self.groundPlane = Rectangle(Arrow(Location(0.,0.),E),self.pcbSize,self.pcbSize)
        
        for face in stack:
            Rectangle(rectangle=self.groundPlane,gerberLayer=face.copper[0]).draw()
         
        bottomCornerHeight = 6.0
        Rectangle(rectangle=self.groundPlane,gerberLayer = stack[3].solderMask[0]).draw()

        groundVoidRectangle(self.center(),self.bottomWidth,bottomCornerHeight,outset=-2*stack.classification.solderMaskMisalignment).draw(stack[3].solderMask[1])
        groundVoidRectangle(self.center(),self.bottomWidth,bottomCornerHeight).draw(stack[3].copper[1])
        groundVoidRectangle(self.center(),self.bottomWidth,bottomCornerHeight,outset=stack[2].depth-stack[3].depth).draw(stack[2].copper[1])
        groundVoidRectangle(self.center(),self.bottomWidth,bottomCornerHeight,outset=stack[1].depth-stack[3].depth).draw(stack[1].copper[1])
        
        extraGroundPlane = Rectangle(Arrow(self.center()-self.bottomWidth*Vector([0.5,0.5-self.noGroundFraction]),E),
                                     self.bottomWidth,
                                     (1-self.noGroundFraction)*self.bottomWidth)

        Rectangle(rectangle=extraGroundPlane,gerberLayer=stack[2].copper[2]).draw()
        Rectangle(rectangle=extraGroundPlane,gerberLayer=stack[1].copper[2]).draw()
        
        stitchingPitch = max(self.stitchingPitch(),stack.classification.viaStitchingPitch(stack.classification.minimumFinishedHoleDiameter))
        
        def viaStamp(arrowAlongBorder):
            MinimumVia(arrowAlongBorder.turnedRight(),stack=stack,inner=True).draw()     
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
            
        Legend(Arrow(self.center()+PlaneVector(holeRadius,0),E),stack).draw()
            

class ESensor:
    def __init__(self,startArrow,face,diameter=3.):
        self.startArrow = startArrow
        self.diameter = diameter
        self.face = face
    def draw(self):
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
        traceWidth = self.face.minimumViaPad(finishedHoleDiameter)
        
        connector = MolexSma(self.startArrow,face=self.face.opposite,signalFaceDiameterTuples=[(self.face,traceWidth)])
        connector.draw()        
        
        traceLength = 0.5*connector.groundGapDiameter + 0.5*traceWidth + self.extraLength
        trace = LineSegment(traceLength,self.startArrow)
        trace.paint(self.face.copper[10],traceWidth)

        Via(trace.endArrow.origin,finishedHoleDiameter,padFaceDiameterTuples=[(self.face,traceWidth)],skipFaces=[self.face.opposite],stack=self.face.stack).draw()
        
        Circle(self.startArrow.origin,(traceLength+0.5*traceWidth)*2.*2.,self.face.solderMask[10]).draw()      
        
        loopLength = traceLength - productionHoleDiameter
        StrokeText(connector.labelArrow,'H ({loopLength:.2f}x{height:.2f}mm)'.format(loopLength=loopLength,height=self.face.depth-self.face.thickness),self.face.opposite.silkscreen[0],align=0).draw()

        
class Via(DrawGroup):
    def __init__(self,location=None,finishedHoleDiameter=None,padFaceDiameterTuples=[],antipadDiameter=None,isolateFaces=[],skipFaces=[],stack=None):
        self.location = location
        self.finishedHoleDiameter = finishedHoleDiameter
        self.padFaceDiameterTuples = padFaceDiameterTuples
        self.isolateFaces = isolateFaces
        self.skipFaces = skipFaces
        self.antipadDiameter = antipadDiameter
        self.stack = stack
        
        facesNeedAntipad = self.stack[:]
        maximumFinishedHoleSize = +numpy.inf
        self.largestPadDiameter = 0.
                
        for (face,padDiameter) in self.padFaceDiameterTuples:
            padDiameter = max(padDiameter,face.minimumViaPad())
            self.append(Circle(self.location,padDiameter,face.copper[20]))
            if face in self.isolateFaces:
                self.append(Circle(self.location,self.stack.classification.minimumViaClearPad(padDiameter),face.copper[11]))
            maximumFinishedHoleSize = min(face.maximumFinishedHoleDiameter(padDiameter),maximumFinishedHoleSize)
            self.largestPadDiameter = max(padDiameter,self.largestPadDiameter)
            facesNeedAntipad.remove(face)
        for face in self.skipFaces:
            facesNeedAntipad.remove(face)
        
        if not self.antipadDiameter:
            self.antipadDiameter = self.largestPadDiameter
        if self.antipadDiameter:
            for face in facesNeedAntipad:
                self.append(Circle(self.location,self.antipadDiameter,face.copper[21]))
          
        if not self.finishedHoleDiameter:
            self.finishedHoleDiameter = maximumFinishedHoleSize
        assert self.finishedHoleDiameter <= maximumFinishedHoleSize
        self.append(Hole(self.location,self.finishedHoleDiameter,plated=True,stack=self.stack))
        
    

            
class MinimumVia(Via):
    def __init__(self,startArrow=None,location=None,finishedHoleDiameter=None,stack=None,inner=False,*args,**kwargs):
        if not finishedHoleDiameter:
            finishedHoleDiameter = stack.classification.minimumFinishedHoleDiameter
        padDiameter = stack.classification.viaClearance(finishedHoleDiameter,inner=inner)
        if type(location) == type(None):
            location = startArrow.along(padDiameter)
                
        super(MinimumVia,self).__init__(location = location,finishedHoleDiameter=finishedHoleDiameter,stack=stack,*args,**kwargs)
    
class MolexSma:
    '''http://www.molex.com/pdm_docs/sd/732511850_sd.pdf'''
    mountingHoleClearance = 3.58
    mountingHoleDiameter = 2.2#1.6

    groundPadDiameter = 4.32 #+ 0.5
    groundGapDiameter = 2.57
    signalPadDiameter = 0.76
    
    keepOutWidth = 5.66
    keepOutHeight = 15.88


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
        Via(self.center,antipadDiameter=self.groundGapDiameter,padFaceDiameterTuples=[(self.face,self.signalPadDiameter)]+self.signalFaceDiameterTuples,stack=stack).draw()        
        
        # Ground vias
        if len(self.groundFaces) > 0:
            if self.groundStopAngle:
                viaAngles = numpy.linspace(self.groundStartAngle,self.groundStopAngle,self.groundVias)
            else:
                viaAngles = numpy.linspace(self.groundStartAngle,self.groundStartAngle+2.*numpy.pi,self.groundVias,endpoint=False)
            
            for viaAngle in viaAngles:
                MinimumVia(self.startArrow.rotated(viaAngle).alongArrow(self.groundGapDiameter/2.),inner=True,skipFaces=[self.face]+self.groundFaces,stack=stack).draw()

        # Mounting holes
        stack.addHole(Hole(self.startArrow.right(self.mountingHoleClearance),self.mountingHoleDiameter,plated=False))
        stack.addHole(Hole(self.startArrow.left(self.mountingHoleClearance),self.mountingHoleDiameter,plated=False))
        
        # Placement outline
        Rectangle(self.startArrow.alongArrow(-self.keepOutWidth/2).outsetArrow(self.keepOutHeight/2),self.keepOutWidth,self.keepOutHeight,stack[0].silkscreen[0],0).draw()

class MolexSmdSma(DrawGroup):
    padSpacing = 4.75
    groundPadSize = 1.91
    centerPadSize = 1.52    
    groundViaDiameter = 0.35
    
    def __init__(self,startArrow,face,drawVias=False):
        DrawGroup.__init__(self)        
        self.startArrow = startArrow
        self.face = face
        
        sides = Square(centerArrow=self.startArrow, width=self.padSpacing).outline().lines()

        for side in sides:
            groundCopperPad = Square(centerArrow=side.startArrow, width=self.groundPadSize)
            groundPad = RectanglePad(groundCopperPad,self.face,solderMask = True)
            self.append(groundPad)
            if drawVias:
                self.append(Via(groundPad.center,finishedHoleDiameter=self.groundViaDiameter,skipFaces=self.face.stack,stack=self.face.stack))
                
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
        Via(self.startArrow.origin,padFaceDiameterTuples,stack=stack).draw()
        
               
class RingResonator(DrawGroup):
    '''
    J. Vorlicek, J. Rusz, L. Oppl, and J. Vrba. Complex permittivity measurement of substrates using ring resonator. In Technical Computing Bratislava, 2010.
    http://phobos.vscht.cz/konference_matlab/MATLAB10/full_text/107_Vorlicek.pdf
    C.-C. Yu and K. Chang. Transmission-line analysis of a capacitively coupled microstrip-ring resonator. Microwave Theory and Techniques, IEEE Transactions on, 45(11):2018 –2024, nov 1997.
    http://ieeexplore.ieee.org/xpl/articleDetails.jsp?tp=&arnumber=644224
    '''
    gapToTraceWidthRatio = 0.5

    def __init__(self,face,traceWidth,firstResonanceFrequency,effectiveRelativePermittivity,startArrow=Arrow(Location(0,0),E),startLayer=10):
        self.startArrow = deepcopy(startArrow)
        self.face = face
        self.firstResonanceFrequency = firstResonanceFrequency
        self.traceWidth = traceWidth
        self.effectiveRelativePermittivity = effectiveRelativePermittivity

        DrawGroup.__init__(self,
           [Circle(self.startArrow.origin,self.outerDiameter(),self.face.copper[startLayer]),
            Circle(self.startArrow.origin,self.innerDiameter(),self.face.copper[startLayer+1]) ])
        if self.face.solderMask:
            self.append(Circle(self.startArrow.origin,self.outerDiameter()+2.*self.traceWidth,self.face.solderMask[10]))

        self.label = StrokeText(self.startArrow,'°{innerDiameter:.2f}mm\nw={traceWidth:.2f}mm\ng={gapWidth:.2f}mm'.format(innerDiameter=self.innerDiameter(),traceWidth=self.traceWidth,gapWidth=self._gapWidth),self.face.silkscreen[0],align=0)
        self.append(self.label)

    def innerDiameter(self):
        velocity = lightSpeed/numpy.sqrt(self.effectiveRelativePermittivity)
        waveLength = velocity/self.firstResonanceFrequency  
        return waveLength # http://www.microwaves101.com/encyclopedia/mitered_bends.cfm
    def outerDiameter(self):
        return self.innerDiameter() + 2.*self.traceWidth 
    @property
    def _gapWidth(self):
        return self.traceWidth * self.gapToTraceWidthRatio
    def endArrows(self):
        outset = self.outerDiameter()/2.+self._gapWidth
        
        return [self.startArrow.alongArrow(outset),
                self.startArrow.turnedRight().alongArrow(outset)]
        
class Legend(DrawGroup):
    def __init__(self,startArrow,stack):
        permittivitiesString = ''
        for (key,value) in stack.classification.permittivity.iteritems():
            permittivitiesString += '@ {frequency} GHz{epsilon:7.2f}\n'.format(frequency=key/1e9,epsilon=value)
        legendString = '''{title}
{timeStamp}
{author}

eurocircuits STD-4L
Cu+Au  35 um
prepreg 7628 362 um
er {permittivitiesString}
Made with PyPCB'''.format(title=stack.title,timeStamp=stack.timeStamp,author=stack.author,permittivitiesString=permittivitiesString)
        self.append(StrokeText(startArrow=startArrow,textString=legendString,
                               align=1,gerberLayer=stack[0].silkscreen[0]))

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
#    GtemCard().draw(Stack(4))
    stack = Stack(4)
    connector = MolexSmdSma(Arrow(Location(0,0),E),stack[0],True)
    print stack[0].maximumFinishedHoleDiameter(0.6)

        