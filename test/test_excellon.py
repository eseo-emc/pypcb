import unittest

from pypcb import *

class Test_Excellon(unittest.TestCase):
    def setUp(self):
        self.file = Excellon('testDrillFile',plated=True)
        
    def test_excellon(self):
        self.file.addHole(Location(1.5,-1),0.5)
        self.file.addHole(Location(1.,0.),1.)
        self.file.addHole(Location(-10.5,-10.),1.)
        
        self.assertEqual(str(self.file), \
'''M48
METRIC,TZ
VER,1
FMAT,2
;FILE_FORMAT=3:3
;TYPE=PLATED
T1C0.500
T2C1.000
%
T01
X+1.500Y-1.000
T02
X+1.000Y+0.000
X-10.500Y-10.000
M30
''')

if __name__ == '__main__':
#     import nose
#     nose.run(argv=['-w','../test','-v'])
#     nose.run(defaultTest=__name__)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Test_Excellon)
    unittest.TextTestRunner(verbosity=2).run(suite)