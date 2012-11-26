import numpy
import copy

from lazy import *

collisionDetection = False # set to False to speed up (useful for debugging)

def m(lengthInMeters):
    return lengthInMeters*1000.
def mil(lengthInMil):
    return lengthInMil*0.0254


    
def assertScalarAlmostEqual(first,second,margin=1e-6):
    assert numpy.linalg.norm(first-second) < margin, '{first} is not almost {second}'.format(first=first,second=second)

class DrawGroup(list):
    def draw(self):
        for drawable in self:
            drawable.draw()
    def translate(self,translationVector):
        for drawable in self:
            drawable.translate(translationVector)
    def rectangularHull(self):
        bottomLeft = Location(+numpy.inf,+numpy.inf)
        topRight = Location(-numpy.inf,-numpy.inf)
        for drawable in self:
            drawableRectangle = drawable.rectangularHull()
            bottomLeft = numpy.min([drawableRectangle.bottomLeft, bottomLeft],0)
            topRight =   numpy.max([drawableRectangle.topRight,   topRight],0)
        return Rectangle(bottomLeft=bottomLeft,topRight=topRight)
        
    @property
    def topRight(self):
        return self.rectangularHull().topRight
    @topRight.setter
    def topRight(self,newValue):
        self.translate(newValue-self.topRight)

class Drawable(object):
    def rectangularHull(self):
        raise NotImplementedError
    def translate(self,translationVector):
        self.startArrow = self.startArrow.translated(translationVector)
    def draw(self):
        raise NotImplementedError

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
    def __init__(self,platedFile,nonPlatedFile):
        self.platedFile = platedFile
        self.nonPlatedFile = nonPlatedFile        
        
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
    
    def writeOut(self):
        for hole in self.fixedHoles + self.looseHoles:
            if hole.plated:
                self.platedFile.addHole(hole.location,hole.diameter)
            else:
                self.nonPlatedFile.addHole(hole.location,hole.diameter)
                
        self.platedFile.writeOut()
        self.nonPlatedFile.writeOut()

## Collections
class ApproximateList(list):
    def assertAlmostEqual(self,other):
        assert len(self) == len(other), 'Both lists do not have the same lenght'
        for number,item in enumerate(self):
            item.assertAlmostEqual(other[number])

class RotatableList(ApproximateList):
    def __rshift__(self,steps):
        if steps > 1:
            return (self >> (steps-1)) >> 1
        elif steps == 1:
            return RotatableList([self[-1]] + self[:-1])
        elif steps == 0:
            return self
        else:
            raise ValueError
    def __lshift__(self,steps):
        if steps > 1:
            return (self << (steps-1)) << 1
        elif steps == 1:
            return RotatableList(self[1:] + [self[0]])
        elif steps == 0:
            return self
        else:
            raise ValueError
            

## Primitives
class Vector(numpy.ndarray):
    def __new__(cls,value):
        newArray = numpy.array(value).astype(numpy.float)
        return numpy.ndarray.__new__(cls,newArray.shape,buffer=newArray) 
    def length(self):
        return numpy.linalg.norm(self)
    def assertAlmostEqual(self,other,margin=1e-6):
        assert self.approximately(other,margin), '{self} is not almost {other}'.format(self=self,other=other)
    def approximately(self,other,margin=1e-6):
        return numpy.linalg.norm(self-other) < margin

class PlaneVector(Vector):
    def __new__(cls,dx,dy=None):
        if isinstance(dx,numpy.ndarray):
            dy=dx[1]
            dx=dx[0]
        return Vector.__new__(cls,[float(dx),float(dy)]) 


class Location(PlaneVector):
    def __sub__(self,other):
        difference = numpy.ndarray.__sub__(self,other)
        return PlaneVector(difference[0],difference[1])
    def __add__(self,other):
        sum = numpy.ndarray.__add__(self,other)
        return Location(sum[0],sum[1])


class Direction(PlaneVector):
    def __new__(cls,x,y=None):
        newVector = PlaneVector.__new__(cls,x,y)
        newVector /= newVector.length()
        return newVector
    def angle(self):
        return numpy.arctan2(self[1],self[0])
N  = Direction(0,1)
NW = Direction(-1,1)
W  = Direction(-1,0)
SW = Direction(-1,-1)
S  = Direction(0,-1)
SE = Direction(1,-1)
E  = Direction(1,0)
NE = Direction(1,1)

#Value

                

class Scalar(float):
    pass

class Angle(Convertible):
    # essence
    def normalise(self,radians):
        return Scalar(numpy.remainder(radians,2*numpy.pi))
    def radians(self):
        return self.essence()

class ALine(Convertible):  
    # essence  
    def normalise(self,rawEssence):
        return rawEssence/rawEssence.length()
    def coordinates(self):        
        return self.essence()
    def __str__(self):
        return 'ALine({coordinates})'.format(coordinates=self.coordinates())
            
    # derived
    @converter
    def yIntercept(self):
        return Vector([-1*self.coordinates()[0]/self.coordinates()[1],-1*self.coordinates()[2]/self.coordinates()[1]])
    @backConverter
    def yInterceptToEssence(self,slopeOffset):
        return self.normalise(Vector([slopeOffset[0],-1,slopeOffset[1]]))
        
    @converter
    def xIntercept(self):
        return Vector([-1*self.coordinates()[1]/self.coordinates()[0],-1*self.coordinates()[2]/self.coordinates()[0]])
    @backConverter
    def xInterceptToEssence(self,slopeOffset):
        return self.normalise(Vector([-1,slopeOffset[0],slopeOffset[1]]))
    
    @converter
    def arrow(self):
        raise NotImplementedError
    @backConverter
    def arrowToEssence(self,arrow):
        origin = arrow.origin
        slope = numpy.tan(arrow.direction.angle())
        return self.normalise(Vector([slope,-1,origin[1]-slope*origin[0]]))
        
    # intelligence
    def crossing(self,other):
        equations = numpy.array((self.coordinates(),other.coordinates()))
        crossing = Location(numpy.linalg.solve(equations[:,:2],-1*equations[:,2]))
        return crossing

    

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
        return Scalar(numpy.arctan2(self.direction[1],self.direction[0]))
    def reversed(self):
        return self.rotated(numpy.pi)
    def rotated(self,rotationAngle):
        return Arrow(self.origin,Direction(numpy.cos(self.angle()+rotationAngle),numpy.sin(self.angle()+rotationAngle)))
    @classmethod
    def rotationMatrix(cls,rotationAngle):
        return numpy.array([[numpy.cos(rotationAngle),-numpy.sin(rotationAngle)],
                      [numpy.sin(rotationAngle), numpy.cos(rotationAngle)]])
    def rotatedAround(self,rotationOrigin,rotationAngle):
        rotationMatrix = self.rotationMatrix(rotationAngle)
        radius = self.origin - rotationOrigin
        newLocation = rotationOrigin + numpy.dot(rotationMatrix,radius)
        newDirection = Direction(numpy.dot(rotationMatrix,self.direction))
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
    def rightLeft(self,clearance):
        return [self.right(clearance),self.left(clearance)]        
    def outsetArrow(self,clearance):
        return Arrow(self.right(clearance),self.direction)
    def repeatRight(self,pitch,repetitions):
        repeatedArrows = []
        for clearance in numpy.arange(repetitions)*pitch:
            repeatedArrows += [self.outsetArrow(clearance)]
        return repeatedArrows
        
    def along(self,length):
        return Location(self.origin+self.direction*length)
    def alongArrow(self,length):
        return Arrow(self.along(length),self.direction)
    def translated(self,translationVector):
        return Arrow(self.origin+translationVector,self.direction)
    
    def crossing(self,other):
        return ALine(arrow=self).crossing(ALine(arrow=other))

## Naked geometry
class Segment(object):
    pass
class Stroke(Segment):
    def __init__(self,targetLocation):
        self.targetLocation = targetLocation
    def __repr__(self):
        return 'Stroke({location})'.format(location=self.targetLocation)
    def assertAlmostEqual(self,other):
        self.targetLocation.assertAlmostEqual(other.targetLocation)
class Arc(Segment):
    def __init__(self,targetLocation,origin,counterClockWise):
        self.targetLocation = targetLocation
        self.origin = origin
        self.counterClockWise = counterClockWise
class ClosedContour(RotatableList):
    def outset(self,outsetClearance):
        strokes = []
        for location in self.lines().outsetLocations(outsetClearance):
            strokes += [Stroke(location)]
        return ClosedContour(strokes)
    def corners(self):
        locations = []
        for stroke in self:
            locations += [stroke.targetLocation]
        return locations
    def lines(self):
        trace = LineList([])
        for thisStroke,nextStroke in zip(self,self<<1):
            delta = nextStroke.targetLocation-thisStroke.targetLocation
            trace.append(LineSegment(numpy.linalg.norm(delta),startArrow=Arrow(thisStroke.targetLocation,Direction(delta))))
        return trace
    def draw(self,gerberLayer,apertureNumber=None):
        gerberLayer.addOutline(self,apertureNumber)
    def drawToFace(self,face,isolation=0.,solderMask=False):
        self.draw(face.copper[20])
        if isolation == None:
            isolation = face.stack.classification.minimumOuterPadToPad
        if isolation > 0.:
            self.outset(isolation).draw(face.copper[11])
        if solderMask:
            self.outset(face.stack.classification.solderMaskMisalignment).draw(face.solderMask[10])
            
    def rectangularHull(self):
        (minimumX,minimumY,maximumX,maximumY) = (+numpy.inf,+numpy.inf,-numpy.inf,-numpy.inf)
        for corner in self.corners():
            minimumX = min(minimumX,corner[0])
            minimumY = min(minimumY,corner[1])
            maximumX = max(maximumX,corner[0])
            maximumY = max(maximumY,corner[1])
        return Rectangle(bottomLeft=Location(minimumX,minimumY),topRight=Location(maximumX,maximumY) )

class ClosedStrokeContour(ClosedContour):
    def __init__(self,locationList):
        strokes = []
        for location in locationList:
            strokes += [Stroke(location)]
        ClosedContour.__init__(self,strokes)


## Visible geometry
class Path(object):
    def closed(self):
        return self.endArrow.origin.approximately(self.startArrow.origin)
    def stamp(self,targetPitch,stampFunctionOfArrow,center=False):
        if center:
            offset = 0.5*targetPitch
        else:
            offset = 0.
        numberOfStamps = int(self.length/float(targetPitch))
        realPitch = self.length/numberOfStamps
        if self.closed() or center:
            numberOfSteps = numberOfStamps
        else:
            numberOfSteps = numberOfStamps + 1
        for length in numpy.arange(numberOfSteps)*realPitch:
            stampFunctionOfArrow(self.alongArrow(length+offset))
class Bend(Path):
    def __init__(self,length,bendRadius,startArrow=Arrow(Location(0.,0.),Direction(1.,0.))):
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

class MiteredBend(Path):
    def __init__(self,startArrow,width,thickness):
        '''http://www.microwaves101.com/encyclopedia/mitered_bends.cfm'''
        self.startArrow = startArrow
        self.width = width
        self.thickness = thickness
    @property
    def _straightExtension(self):
        squareDiagonal = self.width * numpy.sqrt(2)
        halfDiagonal = squareDiagonal * (0.52 + 0.65*numpy.exp(-1.35*self.width/self.thickness))
        return (halfDiagonal-squareDiagonal/2)*numpy.sqrt(2)
    @property
    def _lengthToVirtualCorner(self):
        return self.width/2. + self._straightExtension
    def _startLeftRight(self):
        return self.startArrow.leftRight(self.width/2)
    def _endRightLeft(self):
        return self.endArrow.rightLeft(self.width/2)
    def drawToFace(self,*args,**kwargs):
        self.outline().drawToFace(*args,**kwargs)

    
class RightMiteredBend(MiteredBend): 
    @property
    def endArrow(self):
        return self.startArrow.alongArrow(self._lengthToVirtualCorner).turnedRight().alongArrow(self._lengthToVirtualCorner)
    def outline(self):
        return ClosedStrokeContour(self._startLeftRight() + 
            [self.startArrow.alongArrow(self._straightExtension).right(self.width/2)] +
            self._endRightLeft())
class LeftMiteredBend(MiteredBend): 
    @property
    def endArrow(self):
        return self.startArrow.alongArrow(self._lengthToVirtualCorner).turnedLeft().alongArrow(self._lengthToVirtualCorner)
    def outline(self):
        return ClosedStrokeContour(self._startLeftRight() + 
            self._endRightLeft() +
            [self.startArrow.alongArrow(self._straightExtension).left(self.width/2)])        
        
class LineSegment(Path):
    def __init__(self,length,startArrow=None):
        self.startArrow = startArrow
        self.length = length
    def __repr__(self):
        return 'LineSegment({length})'.format(length=self.length)
    def assertAlmostEqual(self,other):
        self.startArrow.assertAlmostEqual(other.startArrow)
        assertScalarAlmostEqual(self.length,other.length)
    @property
    def endArrow(self):
        return self.alongArrow(self.length)
    @endArrow.setter
    def endArrow(self,newEndArrow):
        self.startArrow = newEndArrow.alongArrow(-self.length)
        self.endArrow.assertAlmostEqual(newEndArrow)
    
    def reversed(self):
        return LineSegment(self.length,self.endArrow.reversed())
    
    def alongArrow(self,length):
        return self.startArrow.alongArrow(length)
    def paint(self,gerberLayer,width):
        self.outline(width).draw(gerberLayer)
    
    def outline(self,width):
        startEdge = self.startArrow.leftRight(width/2)
        endEdge = self.endArrow.leftRight(width/2)
        return ClosedContour([Stroke(startEdge[1]), \
                              Stroke(endEdge[1]),  \
                              Stroke(endEdge[0]), \
                              Stroke(startEdge[0])])


class Rectangle(Drawable): #was list
    def __init__(self,startArrow=None,width=None,height=None,gerberLayer=None,apertureNumber=None,bottomLeft=None,topRight=None,rectangle=None):
        if rectangle is not None:
            self.startArrow = rectangle.startArrow
            self.width = rectangle.width
            self.height = rectangle.height
        elif type(bottomLeft) is type(None):
            self.startArrow = startArrow
            self.width = width
            self.height = height
        else:
            self.startArrow = Arrow(bottomLeft,E)
            self.width = topRight[0]-bottomLeft[0]
            self.height = topRight[1]-bottomLeft[1]
        self.apertureNumber = apertureNumber
        self.gerberLayer = gerberLayer
    
    def outset(self,clearance):
        outsetVector = Vector([clearance,clearance])
        return Rectangle(bottomLeft=self.bottomLeft-outsetVector,topRight=self.topRight+outsetVector)
    def outline(self):
        return ClosedStrokeContour([self.bottomLeft,self.bottomRight,self.topRight,self.topLeft])
    def rectangularHull(self):
        return self.outline().rectangularHull()
        
    @property
    def bottomLeftArrow(self):
        return self.startArrow
    @property 
    def bottomLeft(self):
        return self.bottomLeftArrow.origin

    @property
    def bottomRightArrow(self):
        return self.startArrow.alongArrow(self.width).turnedLeft()
    @property 
    def bottomRight(self):
        return self.bottomRightArrow.origin
        
    @property
    def topRightArrow(self):
        return self.bottomRightArrow.alongArrow(self.height).turnedLeft()
    @property 
    def topRight(self):
        return self.topRightArrow.origin
        
    @property
    def topLeftArrow(self):
        return self.topRightArrow.alongArrow(self.width).turnedLeft()
    @property 
    def topLeft(self):
        return self.topLeftArrow.origin
        
    def draw(self):
        self.gerberLayer.addOutline(self.outline(),self.apertureNumber)
                                
class Square(Rectangle):
    def __init__(self,center=None,centerArrow=None,width=None):
        if not centerArrow:
            centerArrow = Arrow(center,E)
        startArrow = centerArrow.alongArrow(-0.5*width).outsetArrow(0.5*width)
        
        Rectangle.__init__(self,startArrow,width,width)
            
        
class Circle(Drawable):
    def __init__(self,center=None,diameter=None,gerberLayer=None):
        self.center = center
        self.diameter = diameter
        self.gerberLayer = gerberLayer
    def draw(self):
        self._drawToLayer(self.gerberLayer)    
    def outset(self,clearance):
        return Circle(self.center,self.diameter+2.*clearance)
    def rectangularHull(self):
        cornerVector = Vector([0.5,0.5])*self.diameter
        return Rectangle(bottomLeft=self.center-cornerVector,topRight=self.center+cornerVector)
    def translate(self,translationVector):
        self.center += translationVector
    
    
    #TODO: factor this out
    def _drawToLayer(self,gerberLayer):
        apertureNumber = gerberLayer.gerberFile.addCircularAperture(self.diameter)
        gerberLayer.flashAperture(self.center,apertureNumber)





class CompositeCurve(RotatableList,Path):
    '''
    Curve that may consist of LineSegments, Bends and Turns. Start and end
    arrows of segments do not necessarily kiss.
    '''
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



class Trace(CompositeCurve):
    '''
    Consists of LineSegments and Bends, start and end arrows automatically kiss.
    '''
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
         
class LineList(CompositeCurve):
    '''
    Contains only LineSegments, that must not kiss.
    '''
    @property
    def startArrow(self):
        return self[0].startArrow   
    
    def outsetLocations(self,clearance):
        outsetLines = RotatableList()
        for lineSegment in self:
            outsetLines.append(ALine(arrow=lineSegment.startArrow.outsetArrow(clearance)))
        locations = RotatableList()
        for (previousLine,currentLine) in zip(outsetLines >> 1,outsetLines):
            locations.append(previousLine.crossing(currentLine))
        return locations

class MicrostripTrace(CompositeCurve):
    def __init__(self,segments,traceWidth,face):
        self.traceWidth = traceWidth
        self.face = face
        CompositeCurve.__init__(self,segments)
    def rectangularHull(self):
        #TODO: fix this
        return Rectangle(self[0].startArrow,0,0)
    def translate(self,translationVector):
        for segment in self:
            segment.startArrow = segment.startArrow.translated(translationVector)
        
    def draw(self):
        for segment in self:
            copperOutline = segment.outline(self.traceWidth)
            copperOutline.drawToFace(self.face,isolation=None)
            copperOutline.outset(self.traceWidth).draw(self.face.solderMask[10])

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
                
        
#         self.append(LineSegment(self.gap))
#         self.insert(0,LineSegment(self.gap))
        self.paint(conductorFile[1],self.width+2*self.gap)
        
        if solderMaskFile:
#             self.append(LineSegment(2.*self.viaClearance))
#             self.insert(0,LineSegment(2.*self.viaClearance))
            self.paint(solderMaskFile[0],self.width+self.solderMaskClearance)



class Pad(Drawable):
    def rectangularHull(self):
        return self.primitive.rectangularHull()
    def translate(self,translationVector):
        self.primitive.translate(translationVector)
    # TODO: factor in below copy-pastism

class CirclePad(Pad):
    def __init__(self,primitive,face,isolation=0.,solderMask=False):
        self.primitive = primitive
        self.face = face
        self.isolation = isolation
        self.solderMask = solderMask
    def draw(self):
        self.primitive._drawToLayer(self.face.copper[20])
        if self.isolation == None:
            self.isolation = self.face.stack.classification.minimumOuterPadToPad
        if self.isolation > 0.:
            self.primitive.outset(self.isolation)._drawToLayer(self.face.copper[11])
        if self.solderMask:
            self.primitive.outset(self.face.stack.classification.solderMaskMisalignment)._drawToLayer(self.face.solderMask[10])

class RectanglePad(Pad):
    def __init__(self,primitive,face,isolation=0.,solderMask=False):
        self.primitive = primitive
        self.face = face
        self.isolation = isolation
        self.solderMask = solderMask
    def draw(self):
        outline = self.primitive.outline()
        outline.draw(self.face.copper[20])
        if self.isolation == None:
            self.isolation = self.face.stack.classification.minimumOuterPadToPad
        if self.isolation > 0.:
            outline.outset(self.isolation).draw(self.face.copper[11])
        if self.solderMask:
            outline.outset(self.face.stack.classification.solderMaskMisalignment).draw(self.face.solderMask[10])

        

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
        trace.append(LineSegment(cls.tabLengthTop))
        if atBeginning:
            trace.viaStartOffset = mil(25)
        else:
            trace.viaEndOffset = mil(25)
        
    def __init__(self,startArrow,trace):
        self.startArrow = startArrow
        self.trace = trace
    
    def draw(self,topFile,solderMaskTop,solderMaskBottom=None):
        def drawMask(gerberFile,length):
            topMask = LineSegment(length,self.startArrow)
            topMask.paint(gerberFile[0],self.padWidth)
        
        drawMask(solderMaskTop,self.padLengthTop)
        if solderMaskBottom:
            drawMask(solderMaskBottom,self.padLengthBottom)
        
        drop = LineSegment(self.dropWidth,self.startArrow.alongArrow(self.pinLength+self.pinClearance))
        drop.paint(solderMaskTop[1],self.trace.width+self.trace.gap)
        
        pullBack = LineSegment(self.gapLength,self.startArrow)
        pullBack.paint(topFile[3],self.trace.width+2*self.trace.gap)

class Soic8(object):
    padWidth = 1.52
    padHeight = 0.6
    pitch = 1.27
    span = 5.52
    
    dropWidth = 0.35
    dropExcessHeight = 0.15
        
    def __init__(self,startArrow=Arrow(Location(0.,0.),E),padClearance=0.4,solderMaskClearance=.1):
        self.startArrow = startArrow
        self.padClearance = padClearance
        self.solderMaskClearance = solderMaskClearance
    
    def padCentersAndArrows(self):
        startTopLeft = self.startArrow.reversed().alongArrow(self.span/2-self.padWidth/2).outsetArrow(1.5*self.pitch)
        startBottomRight =        self.startArrow.alongArrow(self.span/2-self.padWidth/2).outsetArrow(1.5*self.pitch)
        padArrows = startTopLeft.repeatRight(-self.pitch,4) + startBottomRight.repeatRight(-self.pitch,4)        
        padCenters = map(lambda arrow: arrow.along(self.padWidth/2),padArrows)            
        return (padCenters,padArrows)
    
    def endArrows(self):
        return map(lambda padArrow: padArrow.alongArrow(self.padWidth),self.padCentersAndArrows()[1])
    
    def padTraces(self):
        for startArrow in self.padCentersAndArrows()[1]:
            newTrace = Trace(startArrow,self.padHeight)
            newTrace.append(LineSegment(self.padWidth))
            yield newTrace
        
    def draw(self,face):
        for trace in self.padTraces():
            trace[0].paint(face.copper[10],self.padHeight)
            solderMaskOutset = face.stack.classification.solderMaskMisalignment
            trace[0].outline(self.padHeight).outset(solderMaskOutset).draw(face.solderMask[20])
            
#        if conductorFile:
#            traceLayer = conductorFile[2]    
#            traceAperture = conductorFile.addRectangularAperture(self.padWidth,self.padHeight)
#
#            clearanceLayer = conductorFile[1]    
#            clearanceAperture = conductorFile.addRectangularAperture(self.padWidth+2*self.padClearance,self.padHeight+2*self.padClearance)
#
#        if solderMaskFile:
#            solderMaskLayer = solderMaskFile[0]    
#            solderMaskClearanceAperture = solderMaskFile.addRectangularAperture(self.padWidth+2*self.solderMaskClearance,self.padHeight+2*self.solderMaskClearance)
#            solderMaskDropLayer = solderMaskFile[1] 
#            solderMaskDropAperture = solderMaskFile.addRectangularAperture(self.dropWidth,self.padHeight+2*self.dropExcessHeight)
#                
#        (centers,arrows) = self.padCentersAndArrows()
#        for (padCenter,arrow) in zip(centers,arrows):
#            if conductorFile:
#                traceLayer.flashAperture(padCenter,traceAperture)
#                clearanceLayer.flashAperture(padCenter,clearanceAperture)
#            
#            if solderMaskFile:
#                solderMaskLayer.flashAperture(padCenter,solderMaskClearanceAperture)
#                solderMaskDropLayer.flashAperture(arrow.along(self.padWidth+self.dropWidth/2.),solderMaskDropAperture)

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
        LineSegment(self.gap,self.startArrow).paint(topLayerFile[1],self.trace.width+self.trace.copperClearance)
        LineSegment(self.gap+2.*self.trace.viaClearance,self.startArrow).paint(solderMaskFile[0],self.trace.width+self.trace.solderMaskClearance)
        

class ShortEnd(End):
    def __init__(self,trace,atBeginning=False):
        super(ShortEnd,self).__init__(trace,atBeginning)
    @property
    def length(self):
        return 0.
    def draw(self,topLayerFile,solderMaskFile,holesFile):
        super(ShortEnd,self).draw(topLayerFile,solderMaskFile,holesFile)
        LineSegment(2.*self.trace.viaClearance,self.startArrow).paint(solderMaskFile[0],self.trace.width+self.trace.solderMaskClearance)
        
class ResistorEnd(End):
    # supposed that the trace width is compatible with the resistor
    # a Vishay 0402 flip-chip (F) thin film microwave resistor does
    padLength = 0.35
    gapLength = 0.5
    dropLength = 0.35
    
    def __init__(self,trace,atBeginning=False):
        super(ResistorEnd,self).__init__(trace,atBeginning)
        assert not(atBeginning)
        trace.append(LineSegment(self.padLength))
    @property
    def length(self):
        return self.gapLength + 2*self.padLength
    def draw(self,topLayerFile,solderMaskFile,holesFile):
        super(ResistorEnd,self).draw(topLayerFile,solderMaskFile,holesFile)
        LineSegment(self.padLength+self.gapLength,self.startArrow).paint(topLayerFile[1],self.trace.width+self.trace.copperClearance)
        firstSolderMask = LineSegment(self.padLength+self.gapLength/2.,self.startArrow)
        firstSolderMask.paint(solderMaskFile[0],self.trace.width+self.trace.solderMaskClearance)
        secondSolderMask = LineSegment(self.gapLength/2.+self.padLength,firstSolderMask.endArrow)
        secondSolderMask.paint(solderMaskFile[0],self.trace.width+self.trace.copperClearance/2.)
        
        LineSegment(self.dropLength,self.startArrow.reversed()).paint(solderMaskFile[1],self.trace.width+self.trace.copperClearance/2.)

class R0805ToGround:
    padWidth = 1.2
    padLength = 1.14
    padGap = 0.76    
    
    def __init__(self,startArrow):
        self.startArrow = startArrow
    def draw(self,face):
        Rectangle(self.startArrow,self.padLength,self.padWidth).outline().drawToFace(face,solderMask=True,isolation=None)
        Rectangle(self.startArrow.alongArrow(self.padLength+self.padGap),self.padLength,self.padWidth).outline().drawToFace(face,solderMask=True)
     
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
#             trace.insert(0,LineSegment(self.padLength))
#         else:
#             trace.append(LineSegment(self.padLength))
#     
#     def draw(self,solderMaskTop,solderMaskBottom=None):
#         def drawMask(gerberFile,length):
#             topMask = LineSegment(length,self.startArrow)
#             topMask.paint(gerberFile[0],self.padWidth)
#         
#         drawMask(solderMaskTop,self.padLengthTop)
#         if solderMaskBottom:
#             drawMask(solderMaskBottom,self.padLengthBottom)
#         
#         drop = LineSegment(self.dropWidth,self.startArrow.alongArrow(self.pinLength+self.pinClearance))
#         drop.paint(solderMaskTop[1],self.trace.width+self.trace.gap)
         
class StrokedOutline(RotatableList):
    def addPointsBefore(self,newPoints,verticalStep=None):
        for point in newPoints:
            self.insert(0,point)
    def addPointsAfter(self,newPoints):
        for point in newPoints[::-1]:
            self.append(point)
    @property
    def strokes(self):
        theStrokes = []
        for (point,pointBefore,pointAfter) in zip(self,self >> 1, self << 1):
            if isinstance(point,Location):
                theStrokes += [Stroke(point)]
            else:
                theStrokes += point.strokes(pointBefore,pointAfter)
        return theStrokes
    def draw(self):
        stack.topFile[0].addOutline(self.strokes)
        groundFile[0].addOutline(self.strokes)
        stack.mechanical[0].addOutline(self.strokes,apertureNumber=stack.mechanicalAperture)
    
    #TODO rename to rectangularHull()
    @property
    def rectangle(self):
        (minimumX,minimumY,maximumX,maximumY) = (+numpy.inf,+numpy.inf,-numpy.inf,-numpy.inf)
        for stroke in self.strokes:
            point = stroke.targetLocation
            minimumX = min(minimumX,point[0])
            minimumY = min(minimumY,point[1])
            maximumX = max(maximumX,point[0])
            maximumY = max(maximumY,point[1])
        return (minimumX,minimumY,maximumX,maximumY) 


def soic8(soicLocation,angle=0.0):
    dutFootprint = Soic8(soicLocation,padClearance=traceGap)
    padTraces = dutFootprint.padTraces()
 
    ## drawing the traces
    for (padTrace,bendRadius,bendLength) in zip(padTraces,[-smallRadius,-bigRadius,bigRadius,smallRadius]*2,[smallTraceLength,bigTraceLength,bigTraceLength,smallTraceLength]*2):
        trace = CoplanarTrace.fromTrace(padTrace,gap=traceGap,viaPitch=viaPitch,viaDiameter=viaFinishedHoleDiameter,viaStartOffset=0.,viaEndOffset=None,viaClearance=euroCircuitsViaClearance(viaFinishedHoleDiameter))
        trace.append(Bend(bendLength,bendRadius))
                
        trace.draw(stack.topFile,stack.topSolderMask, stack.stack.drillFile, drillLeftSkip, drillRightSkip)

                                                                                                                                                
if __name__ == '__main__':
    a = Arrow(Location(2,1),NE)
    m = ALine(Vector([1,2,3]))
#    trace = Trace(Arrow(Location(0.,0.),Direction(1.,0.)))
#    trace.append(Bend(numpy.pi/2,1.))
#    trace.append(LineSegment(1.))
#    trace.append(Bend(numpy.pi/2,-1.))
#        
#    alongArrow = trace.alongArrow(numpy.pi/2+1+numpy.pi/4)
#    alongArrow.assertAlmostEqual(Arrow(Location(2.-1./numpy.sqrt(2),2.+1./numpy.sqrt(2)),Direction(1.,1.)))