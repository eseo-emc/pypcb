from pypcb import *
import datetime
#import numpy

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
        topFile[0].addOutline(self.strokes)
        groundFile[0].addOutline(self.strokes)
        mechanical[0].addOutline(self.strokes,apertureNumber=mechanicalAperture)
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


## file initialisation
platedFile = Excellon('Drill Plated',plated=True)
nonPlatedFile = Excellon('Drill Non-plated',plated=False)
drillFile = HoleFile()

topFile = GerberFile('Signal 1 Top',physicalLayer=1)
topSolderMask = GerberFile('Soldermask Top')
topSilkScreen = GerberFile('Silkscreen Top')
topSilkScreenLine = topSilkScreen.addCircularAperture(0.23)

bottomSolderMask = GerberFile('Soldermask Bottom')
bottomSilkScreen = GerberFile('Silkscreen Bottom')


innerOneFile = GerberFile('Signal 2 Inner',physicalLayer=2)
innerTwoFile = GerberFile('Signal 3 Inner',physicalLayer=3)
bottomFile = GerberFile('Signal 4 Bottom',physicalLayer=4)

mechanical = GerberFile('Mechanical Outline')
mechanicalApertureDiameter = 0.2
mechanicalAperture = mechanical.addCircularAperture(mechanicalApertureDiameter)


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
        topFile[0].addOutline(self.strokes)
        groundFile[0].addOutline(self.strokes)
        mechanical[0].addOutline(self.strokes,apertureNumber=mechanicalAperture)
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
                
        trace.draw(topFile,topSolderMask, drillFile, drillLeftSkip, drillRightSkip)
        
## board outline creation
pcbSize = 105.
groundPlane = Rectangle(Arrow(Location(0.,0.),UnitVector(1.,0.)),pcbSize,pcbSize)
groundPlane.draw(topFile[0])
groundPlane.draw(innerOneFile[0])
groundPlane.draw(innerTwoFile[0])
groundPlane.draw(bottomFile[0])
groundPlane.draw(mechanical[0],mechanicalAperture)


layerMarker = LayerMarker(Arrow(Location(0.,0.),UnitVector(1.,0.)), 4)

def groundVoidRectangle(centerLocation,width,cornerHeight,gerberFile,platedFile=None):
    radius = width/2
    outlineCoordinates = numpy.array([[-radius,-radius+cornerHeight],
                                      [-radius,+radius-cornerHeight],
                                      [-radius+cornerHeight,+radius],
                                      [+radius-cornerHeight,+radius],
                                      [+radius,+radius-cornerHeight],
                                      [+radius,-radius+cornerHeight],
                                      [+radius-cornerHeight,-radius],
                                      [-radius+cornerHeight,-radius]]) + centerLocation
    
    outline = []
    for coordinate in outlineCoordinates.tolist():
        stroke = Stroke(Location(numpy.array(coordinate)))
        outline += [stroke]
                
    gerberFile[1].addOutline(outline)
    
centerLocation = Location(pcbSize/2,pcbSize/2)

bottomWidth = 93.5-2
bottomCornerHeight = 6.0
groundVoidRectangle(centerLocation,bottomWidth,bottomCornerHeight,bottomFile)
groundVoidRectangle(centerLocation,bottomWidth-0.360,bottomCornerHeight,innerTwoFile)
groundVoidRectangle(centerLocation,bottomWidth-0.360-0.710,bottomCornerHeight,innerOneFile)


## fixation holes
holeDiagonal = 129.0
holeRadius = holeDiagonal/numpy.sqrt(2)/2
holeCoordinates = numpy.array([[-1,-1],
                               [-1,+1],
                               [+1,+1],
                               [+1,-1]])*holeRadius + centerLocation
for coordinate in holeCoordinates.tolist():
    drillFile.addHole(Hole(Location(numpy.array(coordinate)),3.5,plated=False))

#origin = Location(50.,50.)
#rectangleA = soic8pcb(origin)
#leftOfOrigin = origin[0] - rectangleA[0]
#rectangleB = soic8pcb(Location(rectangleA[2]+leftOfOrigin+2.,50.))
#rectangleC = soic8pcb(Location(rectangleB[2]+leftOfOrigin+2.,50.))


# docs
#topRightCorner = Location(calibrationKitOutline.rectangle[2],calibrationKitOutline.rectangle[3])
#textArrow = Arrow(topRightCorner-Vector(2.0,3.5),UnitVector(1.,0.))
#StrokeText(textArrow,'Made with pyPCB',height=1.5,align=-1,mirrored=True).draw(bottomSilkScreen[0])
#for line in [   'SOIC8 Centimetre DPI',
#                datetime.date.today().strftime('%Y-%m-%d'),
#                'Sjoerd OP \'T LAND',
#                'Groupe ESEO, France',
#                '-',
#              'eurocircuits  STD-4L',
#                     'Cu+Au   35 um',
#              'prepreg 7628  362 um',
#                 'er @ 2GHz     4.1',
#                     'width  .60 mm',
#                       'gap  .26 mm']:
#    StrokeText(textArrow,line,height=1.3,align=+1).draw(topSilkScreen[0])
#    textArrow = textArrow + Vector(0.,-1.3-1)


for file in [topFile,innerOneFile,innerTwoFile,bottomFile]:
    layerMarker.draw(file)

## writing out of gerber and NC excellon files
topSolderMask.writeOut()
topFile.writeOut()
topSilkScreen.writeOut()

innerOneFile.writeOut()
innerTwoFile.writeOut()

bottomSolderMask.writeOut()
bottomFile.writeOut()
bottomSilkScreen.writeOut()

mechanical.writeOut()
# breakRouting.writeOut()

drillFile.draw(platedFile,nonPlatedFile)
platedFile.writeOut()
nonPlatedFile.writeOut()