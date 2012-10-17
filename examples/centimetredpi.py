from pypcb import *
import datetime

## eurociruits particularities
breakRoutingGap = 2.0

# 6C pattern/drill class
euroCircuitsOuterAnnularRing = 0.125
euroCircuitsOuterPadPad = 0.150

def euroCircuitsProductionHoleDiameter(finishedHoleDiameter):
    if finishedHoleDiameter <= 0.45:
        return finishedHoleDiameter + 0.100
    else:
        return finishedHoleDiameter + 0.150
def euroCircuitsViaClearance(finishedHoleDiameter):
    return 0.5*euroCircuitsProductionHoleDiameter(finishedHoleDiameter)+euroCircuitsOuterAnnularRing
def euroCircuitsViaPitch(finishedHoleDiameter):
#     return euroCircuitsProductionHoleDiameter(finishedHoleDiameter)+2*euroCircuitsOuterAnnularRing+euroCircuitsOuterPadPad
    return euroCircuitsProductionHoleDiameter(finishedHoleDiameter)+0.15


## Coplanar Grounded Waveguide properties
traceWidth = 0.6
Soic8.padHeight = traceWidth
traceGap = 0.26 # limit of Eurocircuits process 0.6+2*0.26+0.15=1.27
openGap = 1.5*traceGap

def bendLength(straightLength,bendRadius):
    return straightLength/(1-(traceWidth/(2*bendRadius)))
def straightLength(bendLength,bendRadius):
    return bendLength*(1-(traceWidth/(2*bendRadius)))
assert straightLength(numpy.pi/2*10,10) - (numpy.pi/2*10 - numpy.pi*traceWidth/4) < .0000001
assert bendLength(straightLength(42.,10.),10.) - 42. < .0000001

smallTraceLength = 15. #15
smallRadius = smallTraceLength*2./numpy.pi
bigRadius = 28. # 28
bigTraceLength = bendLength(straightLength(smallTraceLength,smallRadius),bigRadius)
mechanicalConnectorWidth = 11.203 # fitted to get 'right' angles...

viaFinishedHoleDiameter = 0.34 # minimum of the 6C class, Emerson-spec mil(16)
viaPitch = euroCircuitsViaPitch(viaFinishedHoleDiameter) + 0.7 # fitted to put via between traces as close as permitted
Hole.margin = euroCircuitsViaPitch(viaFinishedHoleDiameter)

if euroCircuitsViaPitch(viaFinishedHoleDiameter) > mil(50/2):
    End.backViaOffset = numpy.sqrt(euroCircuitsViaPitch(viaFinishedHoleDiameter)**2 - mil(50/2)**2)
else:
    End.backViaOffset = 0.


## stroke utility functions
class VerticalStep(object):
    def strokes(self,pointBefore,pointAfter):
        midWay = (pointBefore[0]+pointAfter[0])/2.
        return [Stroke(Location(midWay,pointBefore[1])),Stroke(Location(midWay,pointAfter[1]))]
class HorizontalStep(object):
    def strokes(self,pointBefore,pointAfter):
        print [pointBefore, pointAfter]
        midWay = (pointBefore[1]+pointAfter[1])/2.
        return [Stroke(Location(pointBefore[0],midWay)),Stroke(Location(pointAfter[0],midWay))]
class VerticalAt(object):
    def __init__(self,xPosition):
        self.xPosition = xPosition
    def strokes(self,pointBefore,pointAfter):
        return [Stroke(Location(self.xPosition,pointBefore[1])),Stroke(Location(self.xPosition,pointAfter[1]))]

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

groundFile = GerberFile('ground')

mechanical = GerberFile('Mechanical Outline')
mechanicalAperture = mechanical.addCircularAperture(0.2)
# breakRouting = GerberFile('Mechanical Breakrouting example')
# breakRoutingAperture = mechanical.addCircularAperture(breakRoutingGap)

layerMarkers = []


def soic8pcb(soicLocation):
    ## creation of the IC footprint
    dutFootprint = Soic8(soicLocation,padClearance=traceGap)
    padTraces = dutFootprint.padTraces()
    drillFile.addHole(Hole(soicLocation+Vector(0.,+10.),3.,plated=False))
    drillFile.addHole(Hole(soicLocation+Vector(0.,-10.),3.,plated=False))

    startArrow = Arrow(soicLocation+Vector(0.,13.),UnitVector(1.,0.))
    StrokeText(startArrow,'Groupe ESEO',height=1.5,align=0).draw(topSilkScreen[0])
    StrokeText(startArrow,datetime.date.today().strftime('%Y%m%d'),height=1.5,align=0,mirrored=True).draw(bottomSilkScreen[0])

    ## drawing the traces
    traces = []
    for (padTrace,bendRadius,bendLength) in zip(padTraces,[-smallRadius,-bigRadius,bigRadius,smallRadius]*2,[smallTraceLength,bigTraceLength,bigTraceLength,smallTraceLength]*2):
        trace = CoplanarTrace.fromTrace(padTrace,gap=traceGap,viaPitch=viaPitch,viaDiameter=viaFinishedHoleDiameter,viaStartOffset=0.,viaEndOffset=None,viaClearance=euroCircuitsViaClearance(viaFinishedHoleDiameter))
        trace.append(Bend(bendLength,bendRadius))
        traces.append(trace)


    for (traceNumber,trace) in enumerate(traces):
        openEnd = OpenEnd(trace, openGap, atBeginning=True)
        openEnd.gap = openGap
        openEnd.draw(topFile,topSolderMask,drillFile)
            
        Sma.addStub(trace)
        sma = Sma(trace[-1].endArrow.reversed(),trace)
        sma.draw(topFile,topSolderMask,bottomSolderMask)

        # manual removal of impossible vias (overlap with traces)
        skipInnerVias = range(1,5)
        if traceNumber % 4 in [0,1,2]:
            drillLeftSkip = skipInnerVias
        else:
            drillLeftSkip = []
        if traceNumber % 4 in [1,2,3]:
            drillRightSkip = skipInnerVias
        else:
            drillRightSkip = []
                    
        trace.draw(topFile,topSolderMask, drillFile, drillLeftSkip, drillRightSkip)
        
    ## board outline creation
    boardOutline = StrokedOutline()
    for trace in traces:
        leftRight = trace.endArrow.leftRight(mechanicalConnectorWidth/2)
        boardOutline.addPointsAfter(leftRight)
    boardOutline.draw()

    dutFootprint.solderMaskClearance = traces[0].solderMaskClearance/2.
    dutFootprint.draw(None,topSolderMask)
    
    outerRectangle = boardOutline.rectangle
    layerMarkers.append(LayerMarker(Arrow(Location(outerRectangle[2]-27.9,outerRectangle[1]),UnitVector(1.,0.)), 4))
    
        
    return outerRectangle

origin = Location(50.,50.)
rectangleA = soic8pcb(origin)
leftOfOrigin = origin[0] - rectangleA[0]
rectangleB = soic8pcb(Location(rectangleA[2]+leftOfOrigin+2.,50.))
rectangleC = soic8pcb(Location(rectangleB[2]+leftOfOrigin+2.,50.))

## calibration kit definition
standardSpacing = mechanicalConnectorWidth + 3.
calibrationKitOutline = StrokedOutline()
kitLeft = rectangleA[0]
kitRight = rectangleC[2]
firstStandardStart = Arrow(Location(kitLeft + standardSpacing/2,rectangleA[1]-2.),UnitVector(0.,-1.))

def drawThru(startArrow,thruLength,bendTraceLength=bigTraceLength,bendTraceRadius=bigRadius):
    thru = CoplanarTrace(startArrow,traceWidth,traceGap,viaPitch,viaFinishedHoleDiameter,viaStartOffset=None,viaEndOffset=None,viaClearance=euroCircuitsViaClearance(viaFinishedHoleDiameter))
    Sma.addStub(thru,atBeginning=True)
    thru.append(Bend(bendTraceLength,bendTraceRadius))
    beforeLine = thru.endArrow
    thru.append(Line(thruLength))
    afterLine = thru.endArrow
    thru.append(Bend(bendTraceLength,-bendTraceRadius))
    Sma.addStub(thru)
    
    Sma(thru.startArrow,thru).draw(topFile,topSolderMask,bottomSolderMask)
    Sma(thru.endArrow.reversed(),thru).draw(topFile,topSolderMask,bottomSolderMask)
    thru.draw(topFile,topSolderMask, drillFile)
    
    calibrationKitOutline.addPointsAfter(thru.startArrow.leftRight(mechanicalConnectorWidth/2))
    calibrationKitOutline.addPointsBefore(thru.endArrow.reversed().leftRight(mechanicalConnectorWidth/2))
    calibrationKitOutline.addPointsBefore([VerticalStep()])
    
    midArrow = Arrow(Location((beforeLine.origin+afterLine.origin)/2.),beforeLine.direction)
    if thruLength == 0.:
        StrokeText(midArrow.turnedRight().alongArrow(3.5).turnedLeft(),'thru',height=1.5,align=0).draw(topSilkScreen[0])
    else:
        topSilkScreen[0].addSingleStroke(beforeLine.left(1.9),afterLine.left(1.9),topSilkScreenLine)
        StrokeText(midArrow.turnedLeft().alongArrow(2.7).turnedRight(),'{0:.2f}mm'.format(thruLength),height=1.5,align=0).draw(topSilkScreen[0])
        StrokeText(midArrow.turnedRight().alongArrow(3.5).turnedLeft(),'line',height=1.5,align=0).draw(topSilkScreen[0])
        
    return thru.endArrow.reversed()
    
# thrus
drawThru(firstStandardStart,9.98)
drawThru(firstStandardStart+Vector(1*standardSpacing,0.),4.04)
thruEndArrow = drawThru(firstStandardStart+Vector(2*standardSpacing,0.),0.)
drawThru(firstStandardStart+Vector(5*standardSpacing,0.),0.,smallTraceLength,smallRadius)

# sol
def drawStandard(startArrow,Standard,name='',inverted=False):
    trace = CoplanarTrace(startArrow,traceWidth,traceGap,viaPitch,viaFinishedHoleDiameter,viaStartOffset=None,viaEndOffset=None,viaClearance=euroCircuitsViaClearance(viaFinishedHoleDiameter))
    Sma.addStub(trace,atBeginning=True)
    trace.append(Bend(bigTraceLength,bigRadius))
    Sma(trace.startArrow,trace).draw(topFile,topSolderMask,bottomSolderMask)
    end = Standard(trace)
    end.draw(topFile,topSolderMask,drillFile)
    trace.draw(topFile,topSolderMask,drillFile)
    
    textStartArrow = end.startArrow.alongArrow(2)
    if inverted:
        textStartArrow = textStartArrow.reversed()
    label = StrokeText(textStartArrow.turnedRight().alongArrow(0.75).turnedLeft(),name,height=1.5)
    if inverted:
        label.align = +1
    label.draw(topSilkScreen[0])
    
    return startArrow.leftRight(mechanicalConnectorWidth/2)

drawStandard(firstStandardStart+Vector(3*standardSpacing,0.),lambda trace: OpenEnd(trace,openGap),'open')
drawStandard(firstStandardStart+Vector(4*standardSpacing,0.),ShortEnd,'short')
loadLeftRight = drawStandard(thruEndArrow + Vector(1.5*standardSpacing,0.),ResistorEnd,'load ',inverted=True)

# outline
calibrationKitOutline[0] = VerticalAt(kitRight)
calibrationKitOutline.insert(4*3,VerticalAt(kitLeft))
calibrationKitOutline[4] = loadLeftRight[1]
calibrationKitOutline.draw()

layerMarkers.append(LayerMarker(thruEndArrow.turnedRight() + Vector(6.65,0.), 4))

# docs
topRightCorner = Location(calibrationKitOutline.rectangle[2],calibrationKitOutline.rectangle[3])
textArrow = Arrow(topRightCorner-Vector(2.0,3.5),UnitVector(1.,0.))
StrokeText(textArrow,'Made with Python',height=1.5,align=-1,mirrored=True).draw(bottomSilkScreen[0])
for line in [   'SOIC8 Centimetre DPI',
                datetime.date.today().strftime('%Y-%m-%d'),
                'Sjoerd OP \'T LAND',
                'Groupe ESEO, France',
                '-',
              'eurocircuits  STD-4L',
                     'Cu+Au   35 um',
              'prepreg 7628  362 um',
                 'er @ 2GHz     4.1',
                     'width  .60 mm',
                       'gap  .26 mm']:
    StrokeText(textArrow,line,height=1.3,align=+1).draw(topSilkScreen[0])
    textArrow = textArrow + Vector(0.,-1.3-1)



## creation of different ground layers
innerOne = copy.deepcopy(groundFile)
innerOne.name = 'Signal 2 Inner'
innerOne.physicalLayer = 2
innerTwo = copy.deepcopy(groundFile)
innerTwo.name = 'Signal 3 Inner'
innerTwo.physicalLayer = 3
bottomFile = copy.deepcopy(groundFile)
bottomFile.physicalLayer = 4
bottomFile.name = 'Signal 4 Bottom'

for file in [topFile,innerOne,innerTwo,bottomFile]:
    for layerMarker in layerMarkers:
        layerMarker.draw(file)

## writing out of gerber and NC excellon files
topSolderMask.writeOut()
topFile.writeOut()
topSilkScreen.writeOut()

innerOne.writeOut()
innerTwo.writeOut()

bottomSolderMask.writeOut()
bottomFile.writeOut()
bottomSilkScreen.writeOut()

mechanical.writeOut()
# breakRouting.writeOut()

drillFile.draw(platedFile,nonPlatedFile)
platedFile.writeOut()
nonPlatedFile.writeOut()