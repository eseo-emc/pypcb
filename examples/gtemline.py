from pypcb import *


def drawMolexAndVias(startArrow,traceFace,traceWidth):
    groundFaces = map(lambda faceNumber: stack[faceNumber],range(1,traceFace.faceNumber))
    padDiameter = max(traceWidth,traceFace.minimumViaPad())
    connector = MolexSma(startArrow,stack[0],signalFaceDiameterTuples=[(traceFace,padDiameter)],groundFaces=groundFaces,groundStartAngle=+0.5*numpy.pi,groundStopAngle=-0.5*numpy.pi,groundVias=2)
    connector.draw()

class StraightTrace(DrawGroup):
    def __init__(self,length,traceWidth,startArrow,face):
        self.traceWidth = traceWidth
        self.trace = LineSegment(length,startArrow)
        self.face = face
        self.label = StrokeText(textString='microstrip ({traceLayer}-{groundLayer}) {length:.1f}mm'.format(traceLayer=face.faceNumber+1,groundLayer=face.faceNumber,length=length),
                                startArrow=self.trace.halfwayArrow,
                                align=0,
                                gerberLayer=stack[0].silkscreen[0])
    def draw(self):
        self.label.draw()
        self.trace.paint(self.face.copper[2],self.traceWidth)
        drawMolexAndVias(self.trace.startArrow,self.face,self.traceWidth)
        drawMolexAndVias(self.trace.endArrow,self.face,self.traceWidth)
    
class SnakeTrace(DrawGroup):
    def __init__(self,startArrow,face):
        self.face = face
        
        self.corneredTrace0 = LineSegment(longLength/2,startArrow)
        self.corner0 = LeftMiteredBend(self.corneredTrace0.endArrow,outerTraceWidth,stack.dielectricThicknesses[0])
        self.corneredTrace1 = LineSegment(longLength/3,self.corner0.endArrow)
        self.corner1 = RightMiteredBend(self.corneredTrace1.endArrow,outerTraceWidth,stack.dielectricThicknesses[0])
        self.corneredTrace2 = LineSegment(longLength/2,self.corner1.endArrow)
    @property
    def startArrow(self):
        return self.corneredTrace0.startArrow
    @property
    def endArrow(self):
        return self.corneredTrace2.endArrow
    def draw(self):
        self.corneredTrace0.paint(self.face.copper[10],outerTraceWidth)
        self.corner0.drawToFace(stack[-1])
        self.corneredTrace1.paint(self.face.copper[10],outerTraceWidth)
        self.corner1.drawToFace(stack[-1])
        self.corneredTrace2.paint(self.face.copper[10],outerTraceWidth)
        
        for trace in [self.corneredTrace0,self.corneredTrace1,self.corneredTrace2]:
            StrokeText(textString='{length:.1f}mm'.format(length=trace.length),
                        startArrow=trace.halfwayArrow,
                        align=0,
                        gerberLayer=stack[0].silkscreen[0]).draw()
        
        drawMolexAndVias(self.startArrow,self.face,outerTraceWidth)
        drawMolexAndVias(self.endArrow,self.face,outerTraceWidth)

class SoicAndTrace(DrawGroup):
    def __init__(self,startArrow):
        self.ic = Soic14(startArrow)
        self.ic.padHeight = outerTraceWidth
        self.ic.draw(stack[-1])
        self.inputTrace = LineSegment(longLength,self.ic.endArrows()[3])

        for (pinNumber,padTrace) in enumerate(self.ic.padTraces()):
            if pinNumber == 3:
                pass
            elif pinNumber == 10:
                Via(padTrace.halfwayArrow.origin,padFaceDiameterTuples=[(stack[0],outerTraceWidth),(stack[-1],outerTraceWidth)],isolateFaces=[stack[0]],stack=stack).draw()
            else:
                Via(padTrace.endArrow.reversed().along(outerTraceWidth/2),padFaceDiameterTuples=[(stack[-1],outerTraceWidth)],skipFaces=stack[:-1],stack=stack).draw()
                Via(padTrace.startArrow.along(outerTraceWidth/2),padFaceDiameterTuples=[(stack[-1],outerTraceWidth)],skipFaces=stack[:-1],stack=stack).draw()
        
        
        
        self.outputTrace = LineSegment(8.,self.ic.padTraces()[10].halfwayArrow)
        self.label = StrokeText(textString='microstrip (4-3) {length:.1f}mm'.format(length=self.inputTrace.length),
                        startArrow=self.inputTrace.halfwayArrow.reversed(),
                        align=0,
                        gerberLayer=stack[0].silkscreen[0])
        
    @property
    def endArrow(self):
        return self.inputTrace.endArrow
        
    def draw(self):        
        self.outputTrace.outline(outerTraceWidth).drawToFace(stack[0],isolation=None)
        
        R0805ToGround(self.outputTrace.startArrow.alongArrow(2.2).outsetArrow(outerTraceWidth/2).turnedLeft()).draw(stack[0])
        
        MolexSmdSma(self.outputTrace.endArrow,stack[0]).draw()        
        
        self.inputTrace.paint(stack[-1].copper[2],outerTraceWidth)
        self.label.draw()
        drawMolexAndVias(self.endArrow,stack[-1],outerTraceWidth)


# Ring resonators
class Resonator(DrawGroup):
    margin = 5.0
        
class OuterResonator(Resonator):    
    def __init__(self,traceWidth,firstResonanceFrequency,effectiveRelativePermittivity,startLayer=10):
        ringTop = RingResonator(stack[0],traceWidth,firstResonanceFrequency,effectiveRelativePermittivity,startLayer=startLayer)
        ringBottom = RingResonator(stack[-1],traceWidth,firstResonanceFrequency,effectiveRelativePermittivity,startLayer=startLayer)
        Resonator.__init__(self,[ringTop,ringBottom])
        
        for (drawVias,ring) in zip([True,False],[ringTop,ringBottom]):
            for endArrow in ring.endArrows():
                feedTrace = MicrostripTrace([LineSegment(5.,endArrow)],traceWidth,ring.face)
                self.append(feedTrace)
                self.append(MolexSmdSma(feedTrace.endArrow,ring.face,drawVias))
                
            ring.label.align = -1
            ring.label.startArrow = Arrow(self[-1].topRight,E).alongArrow(self[-1].width/2).outsetArrow(self[-1].width/2)
                        
        groundPlane = self.rectangularHull().outset(self.margin)
        self.append(Rectangle(rectangle=groundPlane,gerberLayer=stack[1].copper[0]))
        self.append(Rectangle(rectangle=groundPlane,gerberLayer=stack[2].copper[0]))

class InnerResonator(Resonator):
    def __init__(self,traceWidth,firstResonanceFrequency,effectiveRelativePermittivity,startLayer=10):
        ring = RingResonator(stack[1],traceWidth,firstResonanceFrequency,effectiveRelativePermittivity,startLayer=startLayer)
        Resonator.__init__(self,[ring])
        
        for endArrow in ring.endArrows():
            feedTrace = MicrostripTrace([LineSegment(5.,endArrow)],traceWidth,ring.face)
            self.append(feedTrace)
            self.append(MolexSmdSma(feedTrace.endArrow,stack[0],True))
            self.append(Via(feedTrace.endArrow.origin,
                            padFaceDiameterTuples=[(stack[1],traceWidth)],
                            isolateFaces=[stack[2]],
                            skipFaces=[stack[0]],
                            stack=stack))
                            
        ring.label.align = -1
        ring.label.startArrow = Arrow(self[-2].topRight,E).alongArrow(self[-2].width/2).outsetArrow(self[-2].width/2)
                
        groundPlane = self.rectangularHull().outset(self.margin)
        self.append(Rectangle(rectangle=groundPlane,gerberLayer=stack[2].copper[0]))

class ResonatorCard(DrawGroup):
    def __init__(self,traceWidth,resonator):
        self.append(resonator(traceWidth,2e9,effectiveRelativePermittivity,startLayer=10))
        self.append(resonator(traceWidth,9e9,effectiveRelativePermittivity,startLayer=14))
        self.append(Legend(Arrow(self.topRight-PlaneVector(5.,5.),E),stack))
   
class SubstrateSample(DrawGroup):
    bandWaveguideSizes = {'L':(165.1,82.55), 'S':(72.14,34.04),'C':(47.55,22.149),'X':(22.86,10.16)}
    
    def __init__(self,bandLetter,eFieldVertical=True):
        (width,height) = self.bandWaveguideSizes[bandLetter]
        textMargin = 0.8
        emptySubstrateText = ('EMPTY SUBSTRATE ' if bandLetter != 'X' else 'EMTY ')
        noCopperText = ('mm NO COPPER ' if bandLetter != 'X' else '')
        leftLabel = StrokeText(None,'{letter} {emptySubstrateText}{orientation}'.format(letter=bandLetter,orientation=('Ey' if eFieldVertical else 'Ex'),emptySubstrateText=emptySubstrateText),gerberLayer=stack[0].silkscreen[0])
        rightLabel = StrokeText(None,'{width:.1f}x{height:.1f}{noCopperText}'.format(width=width,height=height,noCopperText=noCopperText),gerberLayer=stack[0].silkscreen[0])
        
        
        oversize = 2.*stack.classification.millingTolerance
        if not eFieldVertical:
            (width,height) = (height,width)
        rectangle = Rectangle(Arrow(Location(0,0),E),width=width+oversize,height=height+oversize)
        if eFieldVertical:
            leftLabel.startArrow = Arrow(rectangle.topLeft,S)
            rightLabel.startArrow = Arrow(rectangle.bottomRight,N)
        else:
            leftLabel.startArrow = Arrow(rectangle.bottomLeft,E)
            rightLabel.startArrow = Arrow(rectangle.topRight,W)
        leftLabel.startArrow = leftLabel.startArrow.alongArrow(textMargin).outsetArrow(-textMargin)
        rightLabel.startArrow = rightLabel.startArrow.alongArrow(textMargin).outsetArrow(-textMargin)
            
        self.append(Rectangle(rectangle=rectangle,gerberLayer=stack[0].solderMask[0]))
        self.append(Rectangle(rectangle=rectangle,gerberLayer=stack[-1].solderMask[0]))
                
        self.append(leftLabel)
        self.append(rightLabel)
        
        

# Card
outerTraceWidth = 0.67 # 0.67 # 50 ohm microstrip on h=360um, er=4.1, t=25um, f=10GHz, according to http://www1.sphere.ne.jp/i-lab/ilab/tool/ms_line_e.htm
innerTraceWidth = 0.468 # 50 ohm microstrip according to ATLC2 refined with CST
effectiveRelativePermittivity = 3.25 # 50 ohm microstrip on h=360um, er=4.1, t=25um, f=10GHz, according to ADS LineCalc
longLength = 50.

stack = Stack(numberOfFaces=4,title='GTEM field-to-line demo',author='Sjoerd OP \'T LAND\nGroupe ESEO, France')
stack[-1].silkscreen.export = False # cheaper

# Resonators
outerResonator = ResonatorCard(outerTraceWidth,OuterResonator)
innerResonator = ResonatorCard(innerTraceWidth,InnerResonator)


card = GtemCard(frequencyLimit=20e9)
#card.pcbSize = outerResonator.width
bottomCenterArrow = Arrow(card.center()+Vector([0,-32]),E)
card.draw(stack)



soicAndTrace = SoicAndTrace(Arrow(card.center()+Location(0.5*longLength,30.),E))
soicAndTrace.draw()

snakeTrace = SnakeTrace(Arrow(card.center()+Location(-0.5*longLength,0.),E),stack[-1])
snakeTrace.draw()
#StraightTrace(longLength,outerTraceWidth,snakeTrace.startArrow.outsetArrow(10.),stack[-1]).draw()
StraightTrace(longLength,outerTraceWidth,bottomCenterArrow.alongArrow(-longLength+15.).outsetArrow(-20.),stack[-1]).draw()

# Sensors
ESensor(bottomCenterArrow.alongArrow(+25),stack[-1]).draw()
HSensor(bottomCenterArrow.alongArrow(+35),stack[-1]).draw()
StraightTrace(longLength,innerTraceWidth,bottomCenterArrow.alongArrow(-longLength+15.),stack[1]).draw()

# Resonators
outerResonator.bottomLeft = card.groundPlane.bottomRight + PlaneVector(stack.classification.breakRoutingGap,0)
innerResonator.bottomLeft = outerResonator.bottomRight + PlaneVector(stack.classification.breakRoutingGap,0)

# Substrate samples
sampleSHorizontal = SubstrateSample('S',eFieldVertical=True)
sampleCVertical = SubstrateSample('C',eFieldVertical=False)
sampleCHorizontal = SubstrateSample('C',eFieldVertical=True)
sampleXVertical = SubstrateSample('X',eFieldVertical=False)
sampleXHorizontal = SubstrateSample('X',eFieldVertical=True)

sampleSHorizontal.topLeft = card.groundPlane.bottomLeft + PlaneVector(0,-stack.classification.breakRoutingGap)
sampleCVertical.topLeft = sampleSHorizontal.topRight + PlaneVector(stack.classification.breakRoutingGap,0)
sampleCHorizontal.topLeft = sampleCVertical.topRight + PlaneVector(stack.classification.breakRoutingGap,0)
sampleXVertical.topLeft = sampleCHorizontal.bottomLeft + PlaneVector(0,-stack.classification.breakRoutingGap)
sampleXHorizontal.topLeft = sampleXVertical.topRight + PlaneVector(stack.classification.breakRoutingGap,0)

sampleSHorizontal.draw()
sampleCVertical.draw()
sampleCHorizontal.draw()
sampleXVertical.draw()
sampleXHorizontal.draw()


stack.boardOutline = DrawGroup([card.groundPlane,
                      innerResonator.rectangularHull(),
                      outerResonator.rectangularHull(),
                      sampleSHorizontal.rectangularHull(),
                      sampleCVertical.rectangularHull(),
                      sampleCHorizontal.rectangularHull(),
                      sampleXVertical.rectangularHull(),
                      sampleXHorizontal.rectangularHull()])
stack.skipLayerMarkerOutlineNumbers = [3,4,5,6,7]
#stack.boardOutline = card.groundPlane.outline()
                                   


outerResonator.draw()
innerResonator.draw()


stack.writeOut(toZip=True)