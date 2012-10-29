# import os
# os.chdir('Y://Python//centimeterlayout//')

import unittest
import nose
import numpy

from pypcb import *

class GerberLayer_test(unittest.TestCase):
    def setUp(self):
        self.file = GerberFile('testfile')
        self.layer = GerberLayer(self.file)
    def test_string(self):
        self.assertEqual(str(self.layer), \
'''%LPD*%
''')

class GerberFile_test(unittest.TestCase):
    def setUp(self):
        self.gerberFile = GerberFile('gerberFileUnderTest',decimalPlaces=4)
    
    def test_layer(self):
        self.assertFalse(self.gerberFile[0].inverted)
        
    def test_location(self):
        self.assertEqual(self.gerberFile.locationToString(Location(1.123456,0)),'X+11235Y+0000')
    def test_offset(self):
        self.assertEqual(self.gerberFile.locationToString(Location(-1.1,2),offset=True),'I-11000J+20000')
        
    def test_aperture(self):
        apertureNumber = self.gerberFile.addRectangularAperture(.1,1.45)
        self.assertEqual(self.gerberFile._aperturesAsString(),'%ADD{apertureNumber:02d}R,0.1000X1.4500*%\n'.format(apertureNumber=apertureNumber))
    def test_circularAperture(self):
        apertureNumber = self.gerberFile.addCircularAperture(.5)
        self.assertEqual(self.gerberFile._aperturesAsString(),'%ADD{apertureNumber:02d}C,0.5000*%\n'.format(apertureNumber=apertureNumber))
    def test_outlineTrace(self):
        aperture = self.gerberFile.addCircularAperture(.5)
        layer = self.gerberFile[0]
        layer.addOutline([Stroke(Location(1.,1.)), \
                                Stroke(Location(4.,1.)), \
                                Stroke(Location(4.,4.)), \
                                Stroke(Location(1.,4.))],apertureNumber=aperture)
        self.assertEqual(layer.drawCommands, \
'''D10*
G75*
G01X+10000Y+10000D02*
G01X+40000Y+10000D01*
G01X+40000Y+40000D01*
G01X+10000Y+40000D01*
G01X+10000Y+10000D01*
''')



if __name__ == '__main__':
    import nose
    nose.run(argv=['-w','../test','-v'])
#     nose.run(defaultTest=__name__)
#     suite = unittest.defaultTestLoader.loadTestsFromTestCase(GerberFile_test)
#     unittest.TextTestRunner(verbosity=2).run(suite)