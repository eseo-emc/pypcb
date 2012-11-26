from excellon import Excellon
from geometry import *
from rs274x import GerberFile

class Classification:
    pass
class EuroCircuits(Classification):
    solderMaskMisalignment = 0.1
    permittivity = 4.3
    
    def productionHoleDiameter(self,finishedHoleDiameter):
        if finishedHoleDiameter <= 0.450:
            return finishedHoleDiameter + 0.100
        else:
            return finishedHoleDiameter + 0.150
    def finishedHoleDiameter(self,productionHoleDiameter):
        if productionHoleDiameter < 0.100:
            raise ValueError
        elif productionHoleDiameter <= (0.450 + 0.100):
            return productionHoleDiameter - 0.100
        elif productionHoleDiameter <= (0.450 + 0.150):
            return ValueError
        else:
            return productionHoleDiameter - 0.150
    @property
    def minimumFinishedHoleDiameter(self):
        return self.finishedHoleDiameter(self.minimumProductionHoleDiameter)
    def minimumViaPad(self,finishedHoleDiameter):
        return self.productionHoleDiameter(finishedHoleDiameter) + 2.*self.minimumOuterAnnularRing
    def minimumViaClearPad(self,padDiameter):
        return padDiameter + 2.*self.minimumOuterPadToPad
    
    
    def maximumFinishedHoleDiameter(self,viaPadDiameter):
        return self.finishedHoleDiameter(viaPadDiameter - 2.*self.minimumOuterAnnularRing)
    
    def viaClearance(self,finishedHoleDiameter):
        return 0.5*self.minimumViaPad(finishedHoleDiameter)
    def viaStitchingPitch(self,finishedHoleDiameter):
         return self.productionHoleDiameter(finishedHoleDiameter)+0.15
         
    
class EuroCircuits6C(EuroCircuits):
    minimumOuterPadToPad = 0.150
    minimumOuterAnnularRing = 0.125
    minimumProductionHoleDiameter = 0.35
class EuroCircuits5B(EuroCircuits):
    minimumOuterPadToPad = 0.150
    minimumOuterAnnularRing = 0.125
    minimumProductionHoleDiameter = 0.45

class FaceList(list):
    pass

class Face():
    def __init__(self,stack,copper,solderMask=None,silkscreen=None,thickness=0.025):
        self.stack = stack
        self.copper = copper
        self.solderMask = solderMask
        self.silkscreen = silkscreen
        self.thickness = thickness
    @property
    def permittivity(self):
        return self.stack.classification.permittivity
    @property
    def faceNumber(self):
        return self.stack.index(self)
    @property
    def depth(self):
        if self.faceNumber == 0:
            return 0.
        else:
            return self.stack[self.faceNumber-1].depth + self.stack.dielectricThicknesses[self.faceNumber-1] + self.thickness
    def writeOut(self):
        self.copper.writeOut()
        if self.solderMask:
            self.solderMask.writeOut()
        if self.silkscreen:
            self.silkscreen.writeOut()

class Stack(list):
    classification = EuroCircuits6C()    
    dielectricThicknesses = [0.180+0.180, 0.710, 0.180+0.180 ]        
    
    @property
    def numberOfFaces(self):
        return len(self)
    def __init__(self,numberOfFaces):
        list.__init__(self,[None]*numberOfFaces)
        ## file initialisation
        self._platedFile = Excellon('Drill Plated',plated=True)
        self._nonPlatedFile = Excellon('Drill Non-plated',plated=False)
        self._drillFile = HoleFile(self._platedFile,self._nonPlatedFile)
        self.addHole = self._drillFile.addHole
        
        self.top = GerberFile('Signal 1 Top',physicalLayer=1)
        self.topSolderMask = GerberFile('Soldermask Top')
        self.topSilkScreen = GerberFile('Silkscreen Top')
        self.topSilkScreenLine = self.topSilkScreen.addCircularAperture(0.23)
        self[0] = Face(self,self.top,self.topSolderMask,self.topSilkScreen,thickness=0.025)
        
        self.innerOneFile = GerberFile('Signal 2 Inner',physicalLayer=2)
        self[1] = Face(self,self.innerOneFile,thickness=0.035)        
        
        self.innerTwoFile = GerberFile('Signal 3 Inner',physicalLayer=3)
        self[2] = Face(self,self.innerTwoFile,thickness=0.035)
        
        self.bottom = GerberFile('Signal 4 Bottom',physicalLayer=4)
        self.bottomSolderMask = GerberFile('Soldermask Bottom')
        self.bottomSilkScreen = GerberFile('Silkscreen Bottom')
        self[3] = Face(self,self.bottom,self.bottomSolderMask,self.bottomSilkScreen,thickness=0.025)
        
        self[-1].opposite = self[ 0]
        self[ 0].opposite = self[-1]        
        
        self.mechanical = GerberFile('Mechanical Outline')
        self.mechanicalApertureDiameter = 0.2
        self.mechanicalAperture = self.mechanical.addCircularAperture(self.mechanicalApertureDiameter)
        
        assert self.numberOfFaces == numberOfFaces
 
                    
    @property
    def thickness(self):
        return self[0].thickness + self[-1].depth
        
    def writeOut(self):
        for face in self:
            face.writeOut()
        
        self.mechanical.writeOut()      
        self._drillFile.writeOut()
        
if __name__ == '__main__':
    print Stack(4).thickness
