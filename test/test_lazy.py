import unittest
from pypcb import *
import numpy

class ALineTest(unittest.TestCase):
    def test_coordinateToYIntercept(self):
        line = ALine(Vector([-2,+2,+2]))
        line.yIntercept().assertAlmostEqual(Vector([+1,-1]))
        line.xIntercept().assertAlmostEqual(Vector([+1,+1]))
    
    def test_yToXIntercept(self):
        line = ALine(yIntercept=Vector([2,0]))
        line.xIntercept().assertAlmostEqual(Vector([0.5,0]))




if __name__ == '__main__':
#     import nose
#     nose.run(argv=['-w','../test','-v'])
#     nose.run(defaultTest=__name__)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ALineTest)
    unittest.TextTestRunner(verbosity=2).run(suite)