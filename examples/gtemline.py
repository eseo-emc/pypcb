from pypcb import *
stack = Stack(numberOfFaces=4)
stack[-1].silkscreen.export = False # cheaper

card = GtemCard(frequencyLimit=20e9)
card.draw(stack)

traceWidth = 0.67 # 50 ohm microstrip on h=360um, er=4.3, t=25um, f=10GHz, according to http://www1.sphere.ne.jp/i-lab/ilab/tool/ms_line_e.htm
effectiveRelativePermittivity = 3.243 # 50 ohm microstrip on h=360um, er=4.3, t=25um, f=10GHz, according to ADS LineCalc
longLength = 30.


def drawMolexAndVias(startArrow,traceFace):
    groundFaces = map(lambda faceNumber: stack[faceNumber],range(1,traceFace.faceNumber))
    connector = MolexSma(startArrow,stack[0],signalFaceDiameterTuples=[(traceFace,traceWidth)],groundFaces=groundFaces,groundStartAngle=+0.5*numpy.pi,groundStopAngle=-0.5*numpy.pi,groundVias=2)
    connector.draw()

# 20mm trace
def drawTrace(length,startArrow,face):
    trace = LineSegment(length,startArrow)
    trace.paint(face.copper[2],traceWidth)
    drawMolexAndVias(trace.startArrow,face)
    drawMolexAndVias(trace.endArrow,face)
    
drawTrace(longLength,Arrow(card.center(),E).alongArrow(-0.5*longLength),stack[-1])

# Corners
corneredTrace0 = LineSegment(longLength/2,Arrow(card.center()+Location(-0.5*longLength,30),E))
corner0 = LeftMiteredBend(corneredTrace0.endArrow,traceWidth,stack.dielectricThicknesses[0])
corneredTrace1 = LineSegment(longLength/3,corner0.endArrow)
corner1 = RightMiteredBend(corneredTrace1.endArrow,traceWidth,stack.dielectricThicknesses[0])
corneredTrace2 = LineSegment(longLength/2,corner1.endArrow)

corneredTrace0.paint(stack[-1].copper[10],traceWidth)
corner0.drawToFace(stack[-1])
corneredTrace1.paint(stack[-1].copper[10],traceWidth)
corner1.drawToFace(stack[-1])
corneredTrace2.paint(stack[-1].copper[10],traceWidth)


# SOIC8 and trace
ic = Soic8(Arrow(card.center()+Location(0.5*longLength,20),E))
ic.padHeight = traceWidth
ic.draw(stack[-1])
trace2 = LineSegment(longLength,ic.endArrows()[0])
groundFacePadTuples = map(lambda face: (face,traceWidth),stack)

def padCenterArrow(pinNumber):
    return ic.endArrows()[pinNumber].alongArrow(-ic.padWidth/2)
for groundPinNumber in range(1,7):
    Via(padCenterArrow(groundPinNumber).origin,padFaceDiameterTuples=groundFacePadTuples).draw(stack)
Via(padCenterArrow(7).origin,padFaceDiameterTuples=[(stack[0],traceWidth),(stack[-1],traceWidth)],isolateFaces=[stack[0]]).draw(stack)

outputTrace = LineSegment(8.,padCenterArrow(7))
outputTrace.outline(traceWidth).drawToFace(stack[0],isolation=None)

R0805ToGround(outputTrace.startArrow.alongArrow(2.).outsetArrow(traceWidth/2).turnedLeft()).draw(stack[0])

MolexSmdSma(outputTrace.endArrow,stack[0]).draw()

trace2.paint(stack[-1].copper[2],traceWidth)
drawMolexAndVias(trace2.endArrow,stack[-1])

# Sensors
bottomCenterArrow = Arrow(card.center()+Vector([0,-32]),E)
ESensor(bottomCenterArrow.alongArrow(+15),stack[-1]).draw()
HSensor(bottomCenterArrow.alongArrow(+30),stack[-1]).draw()
drawTrace(longLength,bottomCenterArrow.alongArrow(-longLength),stack[1])

# Ring resonators
class Resonator(DrawGroup):
    margin = 5.0
    
    def __init__(self,traceWidth,firstResonanceFrequency,effectiveRelativePermittivity):
        ring = RingResonator(stack[0],traceWidth,firstResonanceFrequency,effectiveRelativePermittivity)
        DrawGroup.__init__(self,[ring])
        
        for endArrow in ring.endArrows():
            feedTrace = MicrostripTrace([LineSegment(5.,endArrow)],traceWidth,stack[0])
            self.append(feedTrace)
            self.append(MolexSmdSma(feedTrace.endArrow,stack[0]))
        
        self.groundPlane = self.rectangularHull().outset(self.margin)
        self.groundPlane.gerberLayer = stack[1].copper[0]
        self.append(self.groundPlane)

resonator = Resonator(traceWidth,9e9,effectiveRelativePermittivity)
#print resonator[0]
resonator.topRight = card.groundPlane.bottomRight

boardOutline = ClosedStrokeContour([resonator.groundPlane.topLeft,
                                    resonator.groundPlane.bottomLeft,
                                    resonator.groundPlane.bottomRight,
                                    card.groundPlane.topRight,
                                    card.groundPlane.topLeft,
                                    card.groundPlane.bottomLeft])
                                    
boardOutline = card.outline() + resonator.outline()                                    
                                    
boardOutline.draw(stack.mechanical[0],stack.mechanicalAperture)


resonator.draw()

stack.writeOut()