import unittest
import nose
import numpy

from rs274x import *
from geometry import *

class LineToGerber_test(unittest.TestCase):
    def setUp(self):
        self.line = Line(startArrow=Arrow(Location(0.0,1.0),UnitVector(1.,1.)),length=3*numpy.sqrt(2.))
        self.gerberLayer = GerberFile('gerberFile',decimalPlaces=1)[0]

    def test_lineGerber(self):
        self.line.paint(self.gerberLayer,width=2.*numpy.sqrt(2.))
        self.assertEqual(str(self.gerberLayer), \
'''%LPD*%
G36*
G75*
G01X+10Y+0D02*
G01X+40Y+30D01*
G01X+20Y+50D01*
G01X-10Y+20D01*
G37*
''')


class Coplanar_test(unittest.TestCase):
    def setUp(self):
        self.path = CoplanarTrace(startArrow=Arrow(Location(0.,0.),UnitVector(1.,0.)) ,width=10., gap=0.2)
        self.gerberFile = GerberFile('gerberFile',decimalPlaces=1)
    
    def test_bendGerber(self):
        self.path.append(Bend(length=numpy.pi*20./2, bendRadius=20.))
        self.path.draw(self.gerberFile)
        self.assertEqual(str(self.gerberFile[2]), \
'''%LPD*%
G36*
G75*
G01X+0Y-50D02*
G03X+250Y+200I+0J+250D01*
G01X+150Y+200D01*
G02X+0Y+50I-150J+0D01*
G37*
''')

    def test_bendGerberClockWise(self):
        self.path.append(Bend(length=numpy.pi*20./2, bendRadius=-20.))
        self.path.draw(self.gerberFile)
        self.assertEqual(str(self.gerberFile[2]), \
'''%LPD*%
G36*
G75*
G01X+0Y-50D02*
G02X+150Y-200I+0J-150D01*
G01X+250Y-200D01*
G03X+0Y+50I-250J+0D01*
G37*
''')

if __name__ == '__main__':
    import nose
    nose.run(argv=['-w','../test','-v'])
    nose.run(defaultTest=__name__)
#     suite = unittest.defaultTestLoader.loadTestsFromTestCase(Coplanar_test)
#     unittest.TextTestRunner(verbosity=2).run(suite)