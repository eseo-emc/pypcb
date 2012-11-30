import numpy
from geometry import *

from strokefont import *

class LayerMarker(object):
    def __init__(self,startArrow,numberOfLayers,characterHeight=1.0,lowerMargin=1.0,upperMargin=0.6,sideMargins=0.4):
        self.startArrow = startArrow
        self.numberOfLayers = numberOfLayers
        self.lowerMargin = lowerMargin
        self.upperMargin = upperMargin
        self.sideMargins = sideMargins
        self.characterHeight = characterHeight
        
    def draw(self,gerberFile):
        width = (self.numberOfLayers*2-1)*self.characterHeight + 2*self.sideMargins
        height = self.lowerMargin + self.characterHeight + self.upperMargin
        Rectangle(self.startArrow,width,height,gerberLayer=gerberFile[1]).draw()
        
        textStart = self.startArrow.alongArrow(self.sideMargins).turnedLeft().alongArrow(self.lowerMargin).turnedRight()
        text = StrokeText(textStart.alongArrow((gerberFile.physicalLayer-1)*2*self.characterHeight),'{0:d}'.format(gerberFile.physicalLayer),gerberFile[2],height=self.characterHeight)
        text.draw()

class StrokeText(Drawable):
    def __init__(self,startArrow,textString,gerberLayer,lineWidth=None,height=1.0,align=-1,mirrored=False):
        self.startArrow = startArrow
        self.textString = textString
        self.gerberLayer = gerberLayer
        if lineWidth is None:
            lineWidth = height/6.5
        self.lineWidth = lineWidth
        self.height = height
        self.align = align
        self.mirrored = mirrored
    def __str__(self):
        return '{className}({startArrow},"{text}")'.format(className=self.__class__.__name__,startArrow=self.startArrow,text=self.textString)
    def draw(self):
        strokes = font.stringStrokes(self.textString)
        strokes = strokes - (self.align+1)*numpy.array([float(len(self.textString))/2.,0])
        if self.mirrored:
            strokes = strokes * numpy.array([-1.,1.])
        strokes = strokes * self.height

        # TODO : there must be an accelerated numpy solution for this
        rotation = Arrow.rotationMatrix(self.startArrow.angle())
        strokes = numpy.apply_along_axis(lambda coordinates: rotation.dot(coordinates),arr=strokes,axis=1)
        strokes = strokes + self.startArrow.origin
        
        apertureNumber = self.gerberLayer.gerberFile.addCircularAperture(self.lineWidth)
        for (fromLocation,toLocation) in zip(strokes[0::2,:],strokes[1::2,:]):
            self.gerberLayer.addSingleStroke(fromLocation,toLocation,apertureNumber)
    def rectangularHull(self):
        # TODO: fix this
        return Rectangle(self.startArrow,0,0)

class Character(object):
    def __init__(self,strokeList,scale):
        self.strokes = numpy.array(strokeList)/numpy.array(scale)

class Font(object):
    def __init__(self,fileName):
        assert fileName == 'strokefont.txt'
        fontFile = fontDefinition.splitlines() #open('pypcb/'+fileName)
        self.characters = {' ':Character(numpy.ndarray(shape=(0,2)),1.)}
        scale = [None,None]
        for line in fontFile:
            if line.startswith('XSIZE'):
                scale[0] = float(line.split()[1])
            elif line.startswith('YSIZE'):
                scale[1] = float(line.split()[1])
            elif line.startswith('CHAR'):
                currentCharacter = line.split()[1]
                currentStrokes = []
            elif line.startswith('ECHAR'):
                self.characters.update({currentCharacter:Character(currentStrokes,scale)})
            elif line.startswith('LINE'):
                words = line.split()
                currentStrokes += [[float(words[1]),float(words[2])]]
                currentStrokes += [[float(words[3]),float(words[4])]]
        
        lowerLeft = numpy.min(self.characters['X'].strokes)
        for character in self.characters.values():
            character.strokes = character.strokes - lowerLeft
            
#        fontFile.close()
    
    def stringStrokes(self,textString):
        strokes = numpy.ndarray(shape=(0,2))
        for (position,symbol) in enumerate(textString):
            shiftedStrokes = self.characters[symbol].strokes + numpy.array([1.*position,0.])
            strokes = numpy.vstack((strokes,shiftedStrokes))
        return strokes

font = Font('strokefont.txt')

if __name__ == '__main__':
    from rs274x import *

    testFile = GerberFile('TextTest',decimalPlaces=4)    
    text = StrokeText(Arrow(Location(20.,10.),E),'Xest',testFile[0],height=5.0,align=-1)
    text.draw()
    
    testFile.writeOut('TextTest')
