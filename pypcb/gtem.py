from geometry import *
from stroketext import *

class GtemCard():
    def __init__(self,pcbSize=105,bottomWidth=91.5):
        ## board outline creation
        self.pcbSize = pcbSize
        self.bottomWidth = bottomWidth #93.5-2
        
        self.groundPlane = Rectangle(Arrow(Location(0.,0.),UnitVector(1.,0.)),pcbSize,pcbSize)
        self.layerMarker = LayerMarker(Arrow(Location(0.,0.),UnitVector(1.,0.)), 4)
        
    def centerLocation(self):
        return Location(self.pcbSize/2,self.pcbSize/2)
                
    def draw(self,stack):
        self.groundPlane.draw(stack.top[0])
        self.groundPlane.draw(stack.innerOneFile[0])
        self.groundPlane.draw(stack.innerTwoFile[0])
        self.groundPlane.draw(stack.bottom[0])
        self.groundPlane.draw(stack.mechanical[0],stack.mechanicalAperture)

        
        bottomCornerHeight = 6.0
        groundVoidRectangle(self.centerLocation(),self.bottomWidth,bottomCornerHeight,stack.bottom)
        groundVoidRectangle(self.centerLocation(),self.bottomWidth-0.360,bottomCornerHeight,stack.innerTwoFile)
        groundVoidRectangle(self.centerLocation(),self.bottomWidth-0.360-0.710,bottomCornerHeight,stack.innerOneFile)
        
        
        ## fixation holes
        holeDiagonal = 129.0
        holeRadius = holeDiagonal/numpy.sqrt(2)/2
        holeCoordinates = numpy.array([[-1,-1],
                                       [-1,+1],
                                       [+1,+1],
                                       [+1,-1]])*holeRadius + self.centerLocation()
        for coordinate in holeCoordinates.tolist():
            stack.drillFile.addHole(Hole(Location(numpy.array(coordinate)),3.5,plated=False))
            
        for file in [stack.top,stack.innerOneFile,stack.innerTwoFile,stack.bottom]:
            self.layerMarker.draw(file)


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