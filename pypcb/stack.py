from excellon import Excellon
from geometry import *
from rs274x import GerberFile

class Stack():
    def __init__(self,numberOfLayers):
        assert numberOfLayers == 4
        ## file initialisation
        self.platedFile = Excellon('Drill Plated',plated=True)
        self.nonPlatedFile = Excellon('Drill Non-plated',plated=False)
        self.drillFile = HoleFile()
        
        self.top = GerberFile('Signal 1 Top',physicalLayer=1)
        self.topSolderMask = GerberFile('Soldermask Top')
        self.topSilkScreen = GerberFile('Silkscreen Top')
        self.topSilkScreenLine = self.topSilkScreen.addCircularAperture(0.23)
        
        self.bottomSolderMask = GerberFile('Soldermask Bottom')
        self.bottomSilkScreen = GerberFile('Silkscreen Bottom')
        
        
        self.innerOneFile = GerberFile('Signal 2 Inner',physicalLayer=2)
        self.innerTwoFile = GerberFile('Signal 3 Inner',physicalLayer=3)
        self.bottom = GerberFile('Signal 4 Bottom',physicalLayer=4)
        
        self.mechanical = GerberFile('Mechanical Outline')
        self.mechanicalApertureDiameter = 0.2
        self.mechanicalAperture = self.mechanical.addCircularAperture(self.mechanicalApertureDiameter)
    def writeOut(self):
        ## writing out of gerber and NC excellon files
        self.topSolderMask.writeOut()
        self.top.writeOut()
        self.topSilkScreen.writeOut()
        
        self.innerOneFile.writeOut()
        self.innerTwoFile.writeOut()
        
        self.bottomSolderMask.writeOut()
        self.bottom.writeOut()
        self.bottomSilkScreen.writeOut()
        
        self.mechanical.writeOut()
        # breakRouting.writeOut()
        
        self.drillFile.draw(self.platedFile,self.nonPlatedFile)
        self.platedFile.writeOut()
        self.nonPlatedFile.writeOut()
