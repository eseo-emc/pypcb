from geometry import *
from rs274x import *
from stroketext import *

import unittest

class StrokeText_test(unittest.TestCase):
    def setUp(self):
        self.testFile = GerberFile('test',decimalPlaces=4)
    def test_testText(self):
        text = StrokeText(Arrow(Location(20.,10.),UnitVector(1.,0.)),'Test',lineWidth=1.0,height=5.0)
        text.draw(self.testFile[0])
        
        self.assertEqual(str(self.testFile), \
'''G04 ===== Begin FILE IDENTIFICATION =====*
G04 File Format:  Gerber RS274X*
G04 ===== End   FILE IDENTIFICATION =====*
%FSLAX54Y54*%
%MOMM*%
%SFA1.0B1.0*%
%OFA0.0B0.0*%
G04 Image metadata*
%INTEST*%
%IPPOS*%
%ADD10C,1.0000*%
%LPD*%
G54D10*
X199999Y149983D02*
X233322D01*
X216660*
Y99999*
X274975D02*
X258313D01*
X249983Y108331*
Y124991*
X258313Y133322*
X274975*
X283305Y124991*
Y116660*
X249983*
X299967Y99999D02*
X324959D01*
X333289Y108331*
X324959Y116660*
X308297*
X299967Y124991*
X308297Y133322*
X333289*
X358281Y141652D02*
Y133322D01*
X349951*
X366612*
X358281*
Y108331*
X366612Y99999*
M02*''')

if __name__ == '__main__':
#     import nose
#     nose.run(argv=['-w','../test','-v'])
#     nose.run(defaultTest=__name__)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(StrokeText_test)
    unittest.TextTestRunner(verbosity=2).run(suite)



