from pypcb import *
stack = Stack(numberOfFaces=4)
stack[-1].silkscreen.export = False # cheaper

card = GtemCard(frequencyLimit=20e9)
card.draw(stack)

outerTraceWidth = 0.67 # 50 ohm microstrip on h=360um, er=4.3, t=25um, f=10GHz, according to http://www1.sphere.ne.jp/i-lab/ilab/tool/ms_line_e.htm
innerTraceWidth = 0.468 # 50 ohm microstrip according to ATLC2 refined with CST
effectiveRelativePermittivity = 3.243 # 50 ohm microstrip on h=360um, er=4.3, t=25um, f=10GHz, according to ADS LineCalc
longLength = 30.


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
    def draw(self):
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
        
        drawMolexAndVias(self.startArrow,self.face,outerTraceWidth)
        drawMolexAndVias(self.endArrow,self.face,outerTraceWidth)

class SoicAndTrace(DrawGroup):
    def __init__(self,startArrow):
        self.ic = Soic14(startArrow)
        self.ic.padHeight = outerTraceWidth
        self.ic.draw(stack[-1])
        self.trace2 = LineSegment(longLength,self.ic.endArrows()[3])

        for (pinNumber,padTrace) in enumerate(self.ic.padTraces()):
            if pinNumber == 3:
                pass
            elif pinNumber == 10:
                Via(padTrace.halfwayArrow.origin,padFaceDiameterTuples=[(stack[0],outerTraceWidth),(stack[-1],outerTraceWidth)],isolateFaces=[stack[0]],stack=stack).draw()
            else:
                Via(padTrace.endArrow.reversed().along(outerTraceWidth/2),padFaceDiameterTuples=[(stack[-1],outerTraceWidth)],skipFaces=stack[:-1],stack=stack).draw()
                Via(padTrace.startArrow.along(outerTraceWidth/2),padFaceDiameterTuples=[(stack[-1],outerTraceWidth)],skipFaces=stack[:-1],stack=stack).draw()
        
        
        
        self.outputTrace = LineSegment(8.,self.ic.padTraces()[10].halfwayArrow)
        
    @property
    def endArrow(self):
        return self.trace2.endArrow
        
    def draw(self):        
        self.outputTrace.outline(outerTraceWidth).drawToFace(stack[0],isolation=None)
        
        R0805ToGround(self.outputTrace.startArrow.alongArrow(2.2).outsetArrow(outerTraceWidth/2).turnedLeft()).draw(stack[0])
        
        MolexSmdSma(self.outputTrace.endArrow,stack[0]).draw()        
        
        self.trace2.paint(stack[-1].copper[2],outerTraceWidth)
        drawMolexAndVias(self.endArrow,stack[-1],outerTraceWidth)

soicAndTrace = SoicAndTrace(Arrow(card.center()+Location(0.5*longLength,30.),E))
soicAndTrace.draw()

snakeTrace = SnakeTrace(soicAndTrace.endArrow.reversed().outsetArrow(25.),stack[-1])
snakeTrace.draw()
StraightTrace(longLength,outerTraceWidth,snakeTrace.startArrow.outsetArrow(15.),stack[-1]).draw()


# Sensors
bottomCenterArrow = Arrow(card.center()+Vector([0,-32]),E)
ESensor(bottomCenterArrow.alongArrow(+15),stack[-1]).draw()
HSensor(bottomCenterArrow.alongArrow(+30),stack[-1]).draw()
StraightTrace(longLength,innerTraceWidth,bottomCenterArrow.alongArrow(-longLength),stack[1]).draw()

# Ring resonators
class Resonator(DrawGroup):
    margin = 5.0
    
    def __init__(self,outerTraceWidth,firstResonanceFrequency,effectiveRelativePermittivity):
        ringTop = RingResonator(stack[0],outerTraceWidth,firstResonanceFrequency,effectiveRelativePermittivity)
        ringBottom = RingResonator(stack[-1],outerTraceWidth,firstResonanceFrequency,effectiveRelativePermittivity)
#        ringTop = Square(center=Location(0,0),width=20) 
#        ringTop.gerberLayer= stack[0].copper[1]
        DrawGroup.__init__(self,[ringTop,ringBottom])
        
        for (drawVias,ring) in zip([True,False],[ringTop,ringBottom]):
            for endArrow in ring.endArrows():
                feedTrace = MicrostripTrace([LineSegment(5.,endArrow)],outerTraceWidth,ring.face)
                self.append(feedTrace)
                self.append(MolexSmdSma(feedTrace.endArrow,ring.face,drawVias))

                
        hull = self.rectangularHull().outset(self.margin)

        self.append(Rectangle(rectangle=hull,gerberLayer=stack[1].copper[0]))
        self.append(Rectangle(rectangle=hull,gerberLayer=stack[2].copper[0]))


resonator = Resonator(outerTraceWidth,9e9,effectiveRelativePermittivity)

resonator.topRight = card.groundPlane.bottomRight


stack.boardOutline = ClosedStrokeContour([resonator.topLeft,
                                    resonator.bottomLeft,
                                    resonator.bottomRight,
                                    card.groundPlane.topRight,
                                    card.groundPlane.topLeft,
                                    card.groundPlane.bottomLeft])
                                   


resonator.draw()

stack.writeOut()

print 'Written out board {width:.2f} x {height:.2f} mm'.format(width=stack.width,height=stack.height)