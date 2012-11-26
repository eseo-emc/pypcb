import unittest
from pypcb import *
import numpy

class ArrowTest(unittest.TestCase):
    def test_toline1(self):
        arrow = Arrow(Location(2,1),NE)
        ALine(arrow=arrow).yIntercept().assertAlmostEqual(Vector([1,-1]))
    
    def test_tolineVertical(self):
        arrow = Arrow(Location(4,42),S)
        ALine(arrow=arrow).xIntercept().assertAlmostEqual(Vector([0,4]))
        
    def test_tolineHorizontal(self):
        arrow = Arrow(Location(48,-3),E)
        ALine(arrow=arrow).yIntercept().assertAlmostEqual(Vector([0,-3]))
    
    def test_crossing1(self):
        arrow1 = Arrow(Location(0,0),E)
        arrow2 = Arrow(Location(1,1),NW)       
        
        arrow1.crossing(arrow2).assertAlmostEqual(Location(2,0))
        

class ContourTest(unittest.TestCase):
    def setUp(self):
        self.testOutline = ClosedContour([Stroke(Location(5,1)),
                                       Stroke(Location(5,3)),
                                       Stroke(Location(4,4)),
                                       Stroke(Location(1,4)),
                                       Stroke(Location(1,1))])
    def test_lines(self):
        self.testOutline.lines().assertAlmostEqual(LineList(
            [LineSegment(2.,Arrow(Location(5,1),Direction(0,1))),
             LineSegment(numpy.sqrt(2),Arrow(Location(5,3),Direction(-1,1))),
             LineSegment(3.,Arrow(Location(4,4),Direction(-1,0))),
             LineSegment(3.,Arrow(Location(1,4),Direction(0,-1))),
             LineSegment(4.,Arrow(Location(1,1),Direction(1,0))) ]))




    def test_outset(self):
        self.testOutline.outset(1.).assertAlmostEqual(ClosedContour(
            [Stroke(Location(6,0)),
             Stroke(Location(6,3+numpy.sqrt(2)-1)),
             Stroke(Location(4+numpy.sqrt(2)-1,5)),
             Stroke(Location(0,5)),
             Stroke(Location(0,0))]) )
             
    def test_inset(self):
        self.testOutline.outset(-0.5).assertAlmostEqual(ClosedContour(
            [Stroke(Location(4.5,1.5)),
             Stroke(Location(4.5,3+0.5-numpy.sqrt(2)/2)),
             Stroke(Location(4+0.5-numpy.sqrt(2)/2,3.5)),
             Stroke(Location(1.5,3.5)),
             Stroke(Location(1.5,1.5))]) )

#TODO: make this test work
#    def test_inset_simplify(self):
#        self.testOutline.outset(-1).assertAlmostEqual(ClosedContour(
#            [Stroke(Location(4,2)),
#             Stroke(Location(4,3)),
#             Stroke(Location(2,3)),
#             Stroke(Location(2,2))]) )
             
                          
        
if __name__ == '__main__':
#     import nose
#     nose.run(argv=['-w','../test','-v'])
#     nose.run(defaultTest=__name__)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ContourTest)
    unittest.TextTestRunner(verbosity=2).run(suite)