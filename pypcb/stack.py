from excellon import Excellon
from geometry import *
from rs274x import GerberFile
from stroketext import StrokeText,LayerMarker
import zipfile
import os
import datetime

class Classification:
    pass
class EuroCircuits(Classification):
    solderMaskMisalignment = 0.1
    permittivity = {1e9: 4.10, 2e9: 4.08} #Technolam_data_sheets_NP-115.pdf
    breakRoutingGap = 2.0
    drillIncrement = 0.05
    
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
    def normaliseProductionHoleDiameter(self,productionHoleDiameter):
        return self.drillIncrement*round(productionHoleDiameter/self.drillIncrement)
    def normaliseProductionHoleDiameterDown(self,productionHoleDiameter):
        return self.drillIncrement*numpy.floor(productionHoleDiameter/self.drillIncrement)
    @property
    def minimumFinishedHoleDiameter(self):
        return self.finishedHoleDiameter(self.minimumProductionHoleDiameter)
    def minimumAnnularRing(self,inner=True):
        return (self.minimumInnerAnnularRing if inner else self.minimumOuterAnnularRing)
    def minimumViaPad(self,finishedHoleDiameter=None,inner=True):
        if not finishedHoleDiameter:
            finishedHoleDiameter = self.minimumFinishedHoleDiameter
        return self.productionHoleDiameter(finishedHoleDiameter) + 2.*self.minimumAnnularRing(inner)
    def minimumViaClearPad(self,padDiameter):
        return padDiameter + 2.*self.minimumPadToPad
    
    
    def maximumFinishedHoleDiameter(self,viaPadDiameter,inner=True):
        return self.normaliseProductionHoleDiameterDown(round(self.finishedHoleDiameter(viaPadDiameter - 2.*self.minimumAnnularRing(inner)),3))
    
    def viaClearance(self,finishedHoleDiameter,inner=True):
        return 0.5*self.minimumViaPad(finishedHoleDiameter,inner)
    def viaStitchingPitch(self,finishedHoleDiameter):
         return self.productionHoleDiameter(finishedHoleDiameter)+0.15
         
class EuroCircuitsC(EuroCircuits):
    minimumProductionHoleDiameter = 0.35
    
class EuroCircuitsB(EuroCircuits):
    minimumProductionHoleDiameter = 0.45

class EuroCircuits6(EuroCircuits):
    minimumPadToPad = 0.150
    minimumOuterAnnularRing = 0.125
    minimumInnerAnnularRing = 0.175

class EuroCircuits5(EuroCircuits):
    minimumPadToPad = 0.200
    minimumOuterAnnularRing = 0.150
    minimumInnerAnnularRing = 0.200
    
class EuroCircuits6C(EuroCircuits6,EuroCircuitsC):
    pass    
    
    


class FaceList(list):
    pass

class Face():
    def __init__(self,stack,copper,solderMask=None,silkscreen=None,thickness=0.025):
        self.stack = stack
        self.copper = copper
        self.solderMask = solderMask
        self._silkscreen = silkscreen
        self.thickness = thickness
    @property
    def isInner(self):
        return not(self.faceNumber == 0 or self.faceNumber == len(self.stack)-1)
    @property
    def permittivity(self):
        return self.stack.classification.permittivity
    @property
    def faceNumber(self):
        return self.stack.index(self)
    @property
    def closestOuterFace(self):
        return self.stack[int(round(float(self.faceNumber)/(len(self.stack)-1)))*(len(self.stack)-1)]
    @property
    def depth(self):
        if self.faceNumber == 0:
            return 0.
        else:
            return self.stack[self.faceNumber-1].depth + self.stack.dielectricThicknesses[self.faceNumber-1] + self.thickness
    @property
    def silkscreen(self):
        return self.closestOuterFace._silkscreen
    def writeOut(self,*args,**kwargs):
        self.copper.writeOut(*args,**kwargs)
        if self.solderMask:
            self.solderMask.writeOut(*args,**kwargs)
        if self._silkscreen:
            self._silkscreen.writeOut(*args,**kwargs)
        
    def minimumViaPad(self,finishedHoleDiameter=None):
        return self.stack.classification.minimumViaPad(finishedHoleDiameter,self.isInner)
    def viaClearance(self,finishedHoleDiameter):
        return self.stack.classification.minimumViaPad(finishedHoleDiameter,self.isInner)
    def maximumFinishedHoleDiameter(self,padDiameter):
        return self.stack.classification.maximumFinishedHoleDiameter(padDiameter,self.isInner)

class Stack(list):
    classification = EuroCircuits6C()    
    dielectricThicknesses = [0.180+0.180, 0.710, 0.180+0.180 ]        
    
    @property
    def numberOfFaces(self):
        return len(self)
    def __init__(self,numberOfFaces,title='Untitled',author='Author',notes=''):
        self.title = title
        self.author = author
        self.creationMoment = datetime.datetime.now()
        self.notes = notes
        list.__init__(self,[None]*numberOfFaces)
        ## file initialisation
        self._platedFile = Excellon('Drill Plated',plated=True)
        self._nonPlatedFile = Excellon('Drill Unplated',plated=False)
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
        self.boardOutline = Square(center=Location(0,0),width=100).outline()        
        
        assert self.numberOfFaces == numberOfFaces
 
                    
    @property
    def thickness(self):
        return self[0].thickness + self[-1].depth
    @property
    def rectangularHull(self):
        return self.boardOutline.rectangularHull()
    @property 
    def width(self):
        return self.rectangularHull.width
    @property 
    def height(self):
        return self.rectangularHull.height
    @property
    def timeStamp(self):
        return self.creationMoment.strftime('%Y-%m-%d %H:%M')
        
    def writeOut(self,toZip=False):
        if toZip:
            zipFile = zipfile.ZipFile('../'+self.title+'.zip','w',zipfile.ZIP_DEFLATED)
            outputFile = zipFile.filename
        else:
            outputFile = '../output/'
            zipFile = None
            
        def addApertureAndShapesTo(gerberFile):
            apertureNumber = gerberFile.addCircularAperture(self.mechanicalApertureDiameter)
            for shape in self.boardOutline:
                shape.outline().draw(gerberFile[0],apertureNumber)
            
        addApertureAndShapesTo(self.mechanical)
        StrokeText(textString='{title} {timeStamp}\n{notes}'.format(title=self.title,timeStamp=self.timeStamp,notes=self.notes),
                   startArrow=Arrow(self.rectangularHull.bottomLeft,E).outsetArrow(2.5),
                   gerberLayer=self.mechanical[0]).draw() 
        self.mechanical.writeOut(zipFile=zipFile)   

        layerMarkers = []
        for shape in self.boardOutline:
            layerMarkers += [LayerMarker(Arrow(shape.bottomLeft,E), 4)]

        for face in self:
            addApertureAndShapesTo(face.copper)
            for layerMarker in layerMarkers:
                layerMarker.draw(face.copper)
            face.writeOut(zipFile=zipFile)
        
   
        self._drillFile.writeOut(zipFile=zipFile)
        
        if zipFile:
            zipFile.close()
            
        print 'Written out {width:.2f} x {height:.2f} mm to {outputFile}'.format(width=self.width,height=self.height,outputFile = os.path.abspath(outputFile))
        
if __name__ == '__main__':
    stack = Stack(4)
    print stack.thickness
