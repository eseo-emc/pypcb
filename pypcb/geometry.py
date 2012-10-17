import numpy
import copy

collisionDetection = False # set to False to speed up (useful for debugging)

def mil(length):
    return length*0.0254

class Hole(object):
    margin = 0.1
        
    def __init__(self,location,diameter,plated=True):
        self.location = location
        self.diameter = diameter
        self.plated = plated
    def tooClose(self,other):
#         margin = (self.diameter + other.diameter)/2 + .3+ 0.150
        return other.location.approximately(self.location,self.margin)
    def mergeInPlace(self,other):
        assert self.diameter == other.diameter
        assert self.plated == other.plated
        self.location = (self.location + other.location)/2
        
            
class HoleFile(object):
    def __init__(self):
        self.fixedHoles = []
        self.looseHoles = []
        
    def addHole(self,newHole,fixed=True):
        if fixed or collisionDetection == False:
            self.fixedHoles.append(newHole)
        else:
            for looseHole in self.looseHoles:
                if looseHole.tooClose(newHole):
                    looseHole.mergeInPlace(newHole)
                    self.fixedHoles.append(looseHole)
                    self.looseHoles.remove(looseHole)
                    break
            else:
                self.looseHoles.append(newHole)
    
    def draw(self,platedFile,nonPlatedFile):
        for hole in self.fixedHoles + self.looseHoles:
            if hole.plated:
                platedFile.addHole(hole.location,hole.diameter)
            else:
                nonPlatedFile.addHole(hole.location,hole.diameter)
        

class VectorLike(numpy.ndarray):
    def __new__(cls,dx,dy=None):
        if isinstance(dx,numpy.ndarray):
            dy=dx[1]
            dx=dx[0]
        return numpy.ndarray.__new__(cls,(2,),buffer=numpy.array([dx,dy]),dtype=numpy.float) 
    def assertAlmostEqual(self,other,margin=1e-6):
        assert self.approximately(other,margin), '{self} is not almost {other}'.format(self=self,other=other)
    def approximately(self,other,margin=1e-6):
        return numpy.linalg.norm(self-other) < margin

class Location(VectorLike):
    def __sub__(self,other):
        difference = numpy.ndarray.__sub__(self,other)
        return Vector(difference[0],difference[1])
    def __add__(self,other):
        sum = numpy.ndarray.__add__(self,other)
        return Location(sum[0],sum[1])

class Vector(VectorLike):
    def length(self):
        return numpy.linalg.norm(self)

class UnitVector(Vector):
    def __new__(cls,x,y=None):
        newVector = Vector.__new__(cls,x,y)
        newVector /= newVector.length()
        return newVector


class Arrow(object):
    def __init__(self,origin,direction):
        self.origin = origin
        self.direction = direction
    def __repr__(self):
        return 'Arrow({origin},{direction})'.format(origin=self.origin,direction=self.direction)
    def __add__(self,vector):
        return Arrow(self.origin + vector,self.direction)
    def assertAlmostEqual(self,other,margin=1e-6):
        assert self.approximately(other,margin), '{self} is not almost {other}'.format(self=self,other=other)
    def approximately(self,other,margin=1e-6):
        return self.origin.approximately(other.origin,margin) and self.direction.approximately(other.direction,margin)
        
    def angle(self):
        return numpy.arctan2(self.direction[1],self.direction[0])
    def along(self,length):
        return Location(self.origin+self.direction*length)
    def alongArrow(self,length):
        return Arrow(self.along(length),self.direction)
    def reversed(self):
        return self.rotated(numpy.pi)
    def rotated(self,rotationAngle):
        return Arrow(self.origin,UnitVector(numpy.cos(self.angle()+rotationAngle),numpy.sin(self.angle()+rotationAngle)))
    @classmethod
    def rotationMatrix(cls,rotationAngle):
        return numpy.array([[numpy.cos(rotationAngle),-numpy.sin(rotationAngle)],
                      [numpy.sin(rotationAngle), numpy.cos(rotationAngle)]])
    def rotatedAround(self,rotationOrigin,rotationAngle):
        rotationMatrix = self.rotationMatrix(rotationAngle)
        radius = self.origin - rotationOrigin
        newLocation = rotationOrigin + numpy.dot(rotationMatrix,radius)
        newDirection = UnitVector(numpy.dot(rotationMatrix,self.direction))
        return Arrow(newLocation,newDirection)
    
    def turnedLeft(self):
        return self.rotated(+.5*numpy.pi)
    def turnedRight(self):
        return self.rotated(-.5*numpy.pi)
    def left(self,clearance):
        return self.turnedLeft().along(clearance)
    def right(self,clearance):
        return self.turnedRight().along(clearance)
    def leftRight(self,clearance):
        return [self.left(clearance),self.right(clearance)]

class Segment(object):
    pass
class Stroke(Segment):
    def __init__(self,targetLocation):
        self.targetLocation = targetLocation
class Arc(Segment):
    def __init__(self,targetLocation,origin,counterClockWise):
        self.targetLocation = targetLocation
        self.origin = origin
        self.counterClockWise = counterClockWise

class Path(object):
    pass
class Bend(Path):
    def __init__(self,length,bendRadius,startArrow=Arrow(Location(0.,0.),UnitVector(1.,0.))):
        self.startArrow = startArrow
        self.length = length
        self.bendRadius = bendRadius
    def __repr__(self):
        return 'Bend({length},{bendRadius} ({ccw}))'.format(length=self.length,bendRadius=self.bendRadius,ccw=('CCW' if self.bendRadius > 0 else 'CW'))
    @property
    def endArrow(self):
        return self.alongArrow(self.length)
    @endArrow.setter
    def endArrow(self,newEndArrow):
        origin = self.absoluteOrigin(newEndArrow)
        self.startArrow = newEndArrow.rotatedAround(origin,-self.length/self.bendRadius)
        
        self.absoluteOrigin().assertAlmostEqual(origin)
        self.endArrow.assertAlmostEqual(newEndArrow)
        
    def absoluteOrigin(self,arrow=None):
        if not(arrow):
            arrow = self.startArrow
        return arrow.rotated(numpy.pi/2).along(self.bendRadius)
    def alongArrow(self,pathLength):
        return self.startArrow.rotatedAround(self.absoluteOrigin(),pathLength/self.bendRadius)
  
    def paint(self,gerberLayer,width):
        startEdge = self.startArrow.leftRight(width/2)
        endEdge = self.endArrow.leftRight(width/2)
        outlineSegments = [Stroke(startEdge[1]), \
                            Arc(endEdge[1],  self.absoluteOrigin(),self.bendRadius>=0.), \
                            Stroke(endEdge[0]), \
                            Arc(startEdge[0],self.absoluteOrigin(),self.bendRadius< 0.)]
        gerberLayer.addOutline(outlineSegments)
        
class Line(Path):
    def __init__(self,length,startArrow=None):
        self.startArrow = startArrow
        self.length = length
    def __repr__(self):
        return 'Line({length})'.format(length=self.length)
    @property
    def endArrow(self):
        return self.alongArrow(self.length)
    @endArrow.setter
    def endArrow(self,newEndArrow):
        self.startArrow = newEndArrow.alongArrow(-self.length)
        self.endArrow.assertAlmostEqual(newEndArrow)
        
    def alongArrow(self,length):
        return self.startArrow.alongArrow(length)
    def paint(self,gerberLayer,width):
        startEdge = self.startArrow.leftRight(width/2)
        endEdge = self.endArrow.leftRight(width/2)
        gerberLayer.addOutline([Stroke(startEdge[1]), \
                                Stroke(endEdge[1]),  \
                                Stroke(endEdge[0]), \
                                Stroke(startEdge[0])])

class Rectangle(list):
    def __init__(self,startArrow,width,height,apertureNumber=None):
        self.startArrow = startArrow
        self.apertureNumber = apertureNumber
        self.width = width
        self.height = height
    def draw(self,gerberLayer):
        gerberLayer.addOutline([Stroke(self.startArrow.origin), \
                                Stroke(self.startArrow.along(self.width)),  \
                                Stroke(self.startArrow.alongArrow(self.width).left(self.height)), \
                                Stroke(self.startArrow.left(self.height))],self.apertureNumber)

class Trace(list):
    def __init__(self,startArrow,width=None):
        super(Trace,self).__init__()
        self.startArrow = startArrow
        self.width = width
        
    def append(self,newPath):
        super(Trace,self).append(newPath)
        self.propagateArrows()
    def insert(self,index,newPath):
        super(Trace,self).insert(index,newPath)
        for (path,followingPath) in zip(self[index::-1],self[index+1:0:-1]):
            path.endArrow = followingPath.startArrow
        self.startArrow = self[0].startArrow
        
    def propagateArrows(self):
        startArrow = self.startArrow
        for path in self:
            path.startArrow = startArrow
            startArrow = path.endArrow
        
    @property
    def endArrow(self):
        return self[-1].endArrow
    @property
    def length(self):
        accumulatedLength = 0.
        for path in self:
            accumulatedLength += path.length
        return accumulatedLength
            
    def alongArrow(self,length):
        accumulatedLength = length
        for path in self:
            if accumulatedLength <= path.length:
                return path.alongArrow(accumulatedLength)
            else:
                accumulatedLength -= path.length
        else:
            return path.endArrow.alongArrow(accumulatedLength)
#             raise ValueError,'{0:f} is longer than {1:f}'.format(length,self.length)
            
    def paint(self,gerberLayer,width):
        for path in self:
            path.paint(gerberLayer,width)

class CoplanarTrace(Trace):
    @classmethod
    def fromTrace(cls,trace,**kwargs):
        newTrace = cls(trace.startArrow,trace.width,**kwargs)
        for segment in trace:
            newTrace.append(segment)
        return newTrace
        
    def __init__(self,startArrow,width,gap,viaPitch=2.,viaDiameter=0.15,viaStartOffset=0.,viaEndOffset=0.,viaClearance=0.3):
        super(CoplanarTrace,self).__init__(startArrow,width)
        
        self.gap = gap
        self.viaPitch = viaPitch
        self.viaDiameter = viaDiameter
        self.viaStartOffset = viaStartOffset
        self.viaEndOffset = viaEndOffset
        self.viaClearance = viaClearance
        
    def append(self,newPath):
        super(CoplanarTrace,self).append(newPath)
        if self.viaEndOffset is not None:
            self.viaEndOffset += newPath.length
    def insert(self,index,newPath):
        super(CoplanarTrace,self).insert(index,newPath)
        if (index == 0) and self.viaStartOffset is not None:
            self.viaStartOffset -= newPath.length 
    
    @property
    def copperClearance(self):
        return 2*self.gap
    @property
    def solderMaskClearance(self):
        return self.copperClearance+4*self.viaClearance
    def draw(self,conductorFile,solderMaskFile=None,drillFile=None,drillLeftSkip=[],drillRightSkip=[]):
        self.paint(conductorFile[2],self.width)
        
        if drillFile:
            viaEnd = self.length-self.viaEndOffset
            
            viaSpan = self.width+2*self.gap+2*self.viaClearance
            numberOfVias = int((viaEnd-self.viaStartOffset)/self.viaPitch)
            for (viaNumber,viaAlongLength) in enumerate(numpy.linspace(self.viaStartOffset,viaEnd,numberOfVias)):
                leftRight = self.alongArrow(viaAlongLength).leftRight(viaSpan/2)
                if viaNumber not in drillLeftSkip:
                    drillFile.addHole(Hole(leftRight[0],self.viaDiameter),fixed=False)
                if viaNumber not in drillRightSkip:
                    drillFile.addHole(Hole(leftRight[1],self.viaDiameter),fixed=False)
                
        
#         self.append(Line(self.gap))
#         self.insert(0,Line(self.gap))
        self.paint(conductorFile[1],self.width+2*self.gap)
        
        if solderMaskFile:
#             self.append(Line(2.*self.viaClearance))
#             self.insert(0,Line(2.*self.viaClearance))
            self.paint(solderMaskFile[0],self.width+self.solderMaskClearance)

class Sma(object):
    # TODO: refactor as End
    tabLengthTop = mil(179)
    tabLengthBottom = mil(65)
    padLengthTop = tabLengthTop + mil(39) # 218 mil
    padLengthBottom = tabLengthBottom + mil(39)
    padWidth = mil(320)
    gapLength = mil(5)
        
    pinLength = mil(30)
    pinClearance = mil(30)
    
    dropWidth = 0.35 
    
    @classmethod
    def addStub(cls,trace,atBeginning=False):
        trace.append(Line(cls.tabLengthTop))
        if atBeginning:
            trace.viaStartOffset = mil(25)
        else:
            trace.viaEndOffset = mil(25)
        
    def __init__(self,startArrow,trace):
        self.startArrow = startArrow
        self.trace = trace
    
    def draw(self,topFile,solderMaskTop,solderMaskBottom=None):
        def drawMask(gerberFile,length):
            topMask = Line(length,self.startArrow)
            topMask.paint(gerberFile[0],self.padWidth)
        
        drawMask(solderMaskTop,self.padLengthTop)
        if solderMaskBottom:
            drawMask(solderMaskBottom,self.padLengthBottom)
        
        drop = Line(self.dropWidth,self.startArrow.alongArrow(self.pinLength+self.pinClearance))
        drop.paint(solderMaskTop[1],self.trace.width+self.trace.gap)
        
        pullBack = Line(self.gapLength,self.startArrow)
        pullBack.paint(topFile[3],self.trace.width+2*self.trace.gap)

class Soic8(object):
    padWidth = 1.52
    pitch = 1.27
    span = 5.52
    
    dropWidth = 0.35
    dropExcessHeight = 0.15
        
    def __init__(self,origin=Location(0.,0.),padClearance=0.4,solderMaskClearance=.1):
        self.origin = origin
        self.padClearance = padClearance
        self.solderMaskClearance = solderMaskClearance
    
    def padCentersAndArrows(self):
        padCenters = []
        padArrows = []
        for (xCenter,padOffset,xArrowDirection) in zip(self.origin[0] + numpy.array([-self.span/2,self.span/2]), [Location(-self.padWidth/2,0),Location(+self.padWidth/2,0)], [-1.,1.]):
            yCenters = self.origin[1] + 1.5*self.pitch + numpy.arange(0.0,-self.pitch*4,-self.pitch)
            if xArrowDirection > 0.:
                yCenters = yCenters[::-1]
            
            for yCenter in yCenters:
                padCenter = Location(xCenter,yCenter)
                padCenters.append(padCenter)
                padArrows.append(Arrow(padCenter-padOffset,UnitVector(xArrowDirection,0.)))
            
        return (padCenters,padArrows)
    
    def padTraces(self):
        for startArrow in self.padCentersAndArrows()[1]:
            newTrace = Trace(startArrow,self.padHeight)
            newTrace.append(Line(self.padWidth))
            yield newTrace
        
    def draw(self,conductorFile=None,solderMaskFile=None):
        if conductorFile:
            traceLayer = conductorFile[2]    
            traceAperture = conductorFile.addRectangularAperture(self.padWidth,self.padHeight)

            clearanceLayer = conductorFile[1]    
            clearanceAperture = conductorFile.addRectangularAperture(self.padWidth+2*self.padClearance,self.padHeight+2*self.padClearance)

        if solderMaskFile:
            solderMaskLayer = solderMaskFile[0]    
            solderMaskClearanceAperture = solderMaskFile.addRectangularAperture(self.padWidth+2*self.solderMaskClearance,self.padHeight+2*self.solderMaskClearance)
            solderMaskDropLayer = solderMaskFile[1] 
            solderMaskDropAperture = solderMaskFile.addRectangularAperture(self.dropWidth,self.padHeight+2*self.dropExcessHeight)
                
        (centers,arrows) = self.padCentersAndArrows()
        for (padCenter,arrow) in zip(centers,arrows):
            if conductorFile:
                traceLayer.flashAperture(padCenter,traceAperture)
                clearanceLayer.flashAperture(padCenter,clearanceAperture)
            
            if solderMaskFile:
                solderMaskLayer.flashAperture(padCenter,solderMaskClearanceAperture)
                solderMaskDropLayer.flashAperture(arrow.along(self.padWidth+self.dropWidth/2.),solderMaskDropAperture)

class End(object):
    backViaOffset = 0.
        
    def __init__(self,trace,atBeginning=False):
        self.trace = trace
        self.atBeginning = atBeginning

        viaOffset = -self.length - self.trace.viaClearance
        if self.atBeginning:
            self.trace.viaStartOffset = viaOffset
            self.startArrow = self.trace.startArrow.reversed()
        else:
            self.trace.viaEndOffset = viaOffset
            self.startArrow = self.trace.endArrow
    def draw(self,topLayerFile,solderMaskFile,holesFile):
        holesFile.addHole(Hole(self.startArrow.along(self.length+self.trace.viaClearance+self.backViaOffset),self.trace.viaDiameter),fixed=True)
        

class OpenEnd(End):
    def __init__(self,trace,gap,atBeginning=False):
        self.gap = gap
        super(OpenEnd,self).__init__(trace,atBeginning)
    @property
    def length(self):
        return self.gap
    def draw(self,topLayerFile,solderMaskFile,holesFile):
        super(OpenEnd,self).draw(topLayerFile,solderMaskFile,holesFile)
        Line(self.gap,self.startArrow).paint(topLayerFile[1],self.trace.width+self.trace.copperClearance)
        Line(self.gap+2.*self.trace.viaClearance,self.startArrow).paint(solderMaskFile[0],self.trace.width+self.trace.solderMaskClearance)
        

class ShortEnd(End):
    def __init__(self,trace,atBeginning=False):
        super(ShortEnd,self).__init__(trace,atBeginning)
    @property
    def length(self):
        return 0.
    def draw(self,topLayerFile,solderMaskFile,holesFile):
        super(ShortEnd,self).draw(topLayerFile,solderMaskFile,holesFile)
        Line(2.*self.trace.viaClearance,self.startArrow).paint(solderMaskFile[0],self.trace.width+self.trace.solderMaskClearance)
        
class ResistorEnd(End):
    # supposed that the trace width is compatible with the resistor
    # a Vishay 0402 flip-chip (F) thin film microwave resistor does
    padLength = 0.35
    gapLength = 0.5
    dropLength = 0.35
    
    def __init__(self,trace,atBeginning=False):
        super(ResistorEnd,self).__init__(trace,atBeginning)
        assert not(atBeginning)
        trace.append(Line(self.padLength))
    @property
    def length(self):
        return self.gapLength + 2*self.padLength
    def draw(self,topLayerFile,solderMaskFile,holesFile):
        super(ResistorEnd,self).draw(topLayerFile,solderMaskFile,holesFile)
        Line(self.padLength+self.gapLength,self.startArrow).paint(topLayerFile[1],self.trace.width+self.trace.copperClearance)
        firstSolderMask = Line(self.padLength+self.gapLength/2.,self.startArrow)
        firstSolderMask.paint(solderMaskFile[0],self.trace.width+self.trace.solderMaskClearance)
        secondSolderMask = Line(self.gapLength/2.+self.padLength,firstSolderMask.endArrow)
        secondSolderMask.paint(solderMaskFile[0],self.trace.width+self.trace.copperClearance/2.)
        
        Line(self.dropLength,self.startArrow.reversed()).paint(solderMaskFile[1],self.trace.width+self.trace.copperClearance/2.)
        
# class SmaEnd(object):
#     tabLengthTop = mil(179)
#     tabLengthBottom = mil(65)
#     padLengthTop = tabLengthTop + mil(39) # 218 mil
#     padLengthBottom = tabLengthBottom + mil(39)
#     padWidth = mil(320)
#     gapLength = mil(5)
#         
#     pinLength = mil(30)
#     pinClearance = mil(30)
#     
#     dropWidth = 0.35 
#     
#     @property
#     def length(self):
#         return -mil(25)
#         
#     def __init__(self,trace,atBeginning=False):
#         super(SmaEnd,self).__init__(trace,atBeginning)
#         if atBeginning:
#             trace.insert(0,Line(self.padLength))
#         else:
#             trace.append(Line(self.padLength))
#     
#     def draw(self,solderMaskTop,solderMaskBottom=None):
#         def drawMask(gerberFile,length):
#             topMask = Line(length,self.startArrow)
#             topMask.paint(gerberFile[0],self.padWidth)
#         
#         drawMask(solderMaskTop,self.padLengthTop)
#         if solderMaskBottom:
#             drawMask(solderMaskBottom,self.padLengthBottom)
#         
#         drop = Line(self.dropWidth,self.startArrow.alongArrow(self.pinLength+self.pinClearance))
#         drop.paint(solderMaskTop[1],self.trace.width+self.trace.gap)
                                
                                                                                                                                                
if __name__ == '__main__':
    trace = Trace(Arrow(Location(0.,0.),UnitVector(1.,0.)))
    trace.append(Bend(numpy.pi/2,1.))
    trace.append(Line(1.))
    trace.append(Bend(numpy.pi/2,-1.))
        
    alongArrow = trace.alongArrow(numpy.pi/2+1+numpy.pi/4)
    alongArrow.assertAlmostEqual(Arrow(Location(2.-1./numpy.sqrt(2),2.+1./numpy.sqrt(2)),UnitVector(1.,1.)))