import os

class Tool(object):
    def __init__(self,excellon,number,diameter):
        self.diameter = diameter
        self.number = number
        self.excellon = excellon
        self.drillInstructions = ''
    def __str__(self):
        return 'T{number:d}C{diameter:.{precision}f}\n'.format(number=self.number,diameter=self.diameter,precision=self.excellon.decimalPlaces)
    def addHole(self,location):
        def lengthToString(lengthInMm):
            assert lengthInMm < 10.**self.excellon.integerPlaces
            return '{length:+.0{decimalPlaces}f}'.format(length=lengthInMm,decimalPlaces=self.excellon.decimalPlaces)
        
        self.drillInstructions += 'X{x}Y{y}\n'.format(x=lengthToString(location[0]),y=lengthToString(location[1]))
    def drillString(self):
        return 'T{number:02d}\n{drillInstructions}'.format(number=self.number,drillInstructions=self.drillInstructions)

class Excellon(object):
    def __init__(self,name,plated=None):
        self.decimalPlaces = 3
        self.integerPlaces = 3
        self.lastToolNumber = 0
        self.tools = []
        
        self.name = name
        self.plated = plated
    def __str__(self):
        return \
'''M48
METRIC,TZ
VER,1
FMAT,2
;FILE_FORMAT={integerPlaces:d}:{decimalPlaces:d}
'''.format(integerPlaces=self.integerPlaces,decimalPlaces=self.decimalPlaces)+self.platedString()+ self.toolString()+self.drillString()

    def addHole(self,location,diameter):
        for existingTool in self.tools:
            if existingTool.diameter == diameter:
                tool = existingTool
                break
        else:
            tool = self._addTool(diameter)
        tool.addHole(location)

    def _addTool(self,diameter):
        self.lastToolNumber += 1
        newTool = Tool(self,self.lastToolNumber,diameter)
        self.tools.append(newTool)
        return newTool

    def platedString(self):
        if self.plated == None:
            return ''
        elif self.plated:
            return ';TYPE=PLATED\n'
        else:
            return ';TYPE=NON_PLATED\n'

    def toolString(self):
        string = ''
        for tool in self.tools:
            string += str(tool)
        return string

    def drillString(self):
        string = '%\n'
        for tool in self.tools:
            string += tool.drillString()
        string += 'M30\n'
        return string
        
    def writeOut(self,name=None,zipFile=None):
        if name == None:
            name = self.name
        
        if zipFile:
            zipFile.writestr(name + '.drl',str(self))
        else:
            outputDirectory = os.path.abspath('../output')
            if not os.path.exists(outputDirectory):
                print 'Creating output directory ' + outputDirectory
                os.makedirs(outputDirectory)
            self.fileHandle = open(outputDirectory + '/' + name + '.drl','w')
                
            self.fileHandle.write(str(self))
            self.fileHandle.close()
        
if __name__ == '__main__':
    file = Excellon('testDrillFile',plated=True)
    
    smallTool = file.addTool(0.5)
    largeTool = file.addTool(1.)
    largeTool.addHole(Location(1.,0.))
    smallTool.addHole(Location(1.5,-1))
    largeTool.addHole(Location(-1.5,-1.))
    
    print(file)