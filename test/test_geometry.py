import unittest
import nose
import numpy

from pypcb import *

class Location_test(unittest.TestCase):
    def test_subtraction(self):
        a = Location(1.,2.)
        b = Location(3.,-1.5)
        self.assertEqual(type(a-b),PlaneVector)
        (a-b).assertAlmostEqual(PlaneVector(-2.,3.5))

class UnitVector_test(unittest.TestCase):
    def setUp(self):
        self.direction = Direction(-3.,3.)
    def test_UnitVector(self):
        self.direction.assertAlmostEqual(numpy.array([-1/numpy.sqrt(2),+1/numpy.sqrt(2)]))
        
class Direction_test(unittest.TestCase):
    def test_parallel(self):
        self.assertTrue(NE.parallelWith(NE))
        self.assertTrue(NE.parallelWith(SW))
        self.assertFalse(NE.parallelWith(N))

class Arrow_test(unittest.TestCase):
    def setUp(self):
        self.arrow = Arrow(Location(0.,1.),Direction(-1.,1.))
    def test_angle(self):
        self.assertAlmostEqual(self.arrow.angle(),0.75*numpy.pi)
    def test_along(self):
        alongLocation = self.arrow.along(numpy.sqrt(8.))
        alongLocation.assertAlmostEqual(Location(-2.,3.))
        self.assertEqual(type(alongLocation),Location)
    def test_rotated(self):
        rotatedUnitVector = self.arrow.rotated(0.75*numpy.pi)
        rotatedUnitVector.along(1.).assertAlmostEqual(Location(0.,0.))
    def test_rotateAround(self):
        rotatedArrow = self.arrow.rotatedAround(Location(1.,1.),-0.25*numpy.pi)
        rotatedArrow.origin.assertAlmostEqual(Location(1.-1./numpy.sqrt(2.),1.+1./numpy.sqrt(2.)))
        self.assertAlmostEqual(rotatedArrow.angle(),0.5*numpy.pi)
    def test_leftRight(self):
        leftRight = self.arrow.leftRight(numpy.sqrt(2.))
        leftRight[0].assertAlmostEqual(Location(-1.,0.))
        leftRight[1].assertAlmostEqual(Location(1.,2.))

class ALine_test(unittest.TestCase):
    def test_horizontalLinesDontIntersect(self):
        topLine = ALine(arrow=Arrow(Location(0,1),E))
        bottomLine = ALine(arrow=Arrow(Location(0,42),E))
        self.assertIsNone(topLine.intersection(bottomLine))
    def test_almostHorizontalLinesDontIntersect(self):
        lineAtYOne = ALine(Vector([ -1.22464680e-16,  -1.00000000e+00,   1.00000000e+00]))
        lineAtYZero = ALine(Vector([ 0., -1.,  0.]))
        self.assertIsNone(lineAtYOne.intersection(lineAtYZero))
    def test_nonEquality(self):
        topLine = ALine(arrow=Arrow(Location(0,1),E))
        bottomLine = ALine(arrow=Arrow(Location(0,42),E))
        self.assertNotEquals(topLine,bottomLine)        
    def test_equality(self):
        topLine = ALine(arrow=Arrow(Location(1,1),NE))
        bottomLine = ALine(arrow=Arrow(Location(4,4),SW))
        self.assertEquals(topLine,bottomLine)    


class LineSegment_test(unittest.TestCase):
    def test_lineEnd(self):
        self.line = LineSegment(startArrow=Arrow(Location(0.0,1.0),Direction(1.,1.)),length=3*numpy.sqrt(2.))
        self.line.endArrow.assertAlmostEqual(Arrow(Location(3.,4.),Direction(1.,1.)))

    def test_pointOnSegment(self):
        self.line = LineSegment(2.,Arrow(Location(1,2),E))
        self.assertFalse(self.line.pointOnSegment(Location(0,2)))
        self.assertTrue(self.line.pointOnSegment(Location(1,2)))
        self.assertTrue(self.line.pointOnSegment(Location(2,2)))
        self.assertTrue(self.line.pointOnSegment(Location(3,2)))    
        self.assertFalse(self.line.pointOnSegment(Location(4,2)))

    def test_intersection(self):
        horizontalSegment = LineSegment(2.,Arrow(Location(0,1),E))
        diagonalSegment = LineSegment(3.,Arrow(Location(0,0),NE))
        diagonalSegment.intersection(horizontalSegment).assertAlmostEqual(Location(1,1))
        horizontalSegment.intersection(diagonalSegment).assertAlmostEqual(Location(1,1))
    def test_nointersection(self):
        horizontalSegment = LineSegment(2.,Arrow(Location(0,1),E))
        diagonalSegment = LineSegment(1.,Arrow(Location(0,0),NE))
        self.assertIsNone(diagonalSegment.intersection(horizontalSegment))
        self.assertIsNone(horizontalSegment.intersection(diagonalSegment))
    def test_overlap(self):
        horizontalOne = LineSegment(3.,Arrow(Location(1,1),E))
        horizontalTwo = LineSegment(5.,Arrow(Location(8,1),W))
        horizontalOne.intersection(horizontalTwo).assertAlmostEqual(LineSegment(1.,Arrow(Location(3,1),E)))
        horizontalTwo.intersection(horizontalOne).assertAlmostEqual(LineSegment(1.,Arrow(Location(4,1),W)))


class LineList_test(unittest.TestCase):
    def setUp(self):
        self.rectangleLines = Rectangle(Arrow(Location(1,1),S),2,2).outline().lines()
    def test_firstIntersectionRight(self):
        self.cuttingLineSegment = LineSegment(4,Arrow(Location(4,0),W))
        intersection = self.rectangleLines.firstIntersection(self.cuttingLineSegment)
        intersection[0].assertAlmostEqual(Location(3,0))
        self.assertEqual(intersection[1],2)
    def test_firstIntersectionLeft(self):
        self.cuttingLineSegment = LineSegment(4,Arrow(Location(4,0),W))
        intersection = self.rectangleLines.firstIntersection(self.cuttingLineSegment.reversed())
        intersection[0].assertAlmostEqual(Location(1,0))
        self.assertEqual(intersection[1],0)
    def test_firstIntersectionNone(self):
        self.cuttingLineSegment = LineSegment(4,Arrow(Location(4,0),E))
        self.assertIsNone(self.rectangleLines.firstIntersection(self.cuttingLineSegment))
    def test_firstIntersectionLeftInside(self):
        self.cuttingLineSegment = LineSegment(4,Arrow(Location(2.5,0),W))
        intersection = self.rectangleLines.firstIntersection(self.cuttingLineSegment)
        intersection[0].assertAlmostEqual(Location(1,0))         
        self.assertEqual(intersection[1],0)

        
class Trace_test(unittest.TestCase):
    def setUp(self):
        self.trace = Trace(Arrow(Location(0.,0.),Direction(1.,0.)))
        self.trace.append(Bend(numpy.pi/2,1.))
        self.trace.append(LineSegment(1.))
        self.trace.append(Bend(numpy.pi/2,-1.))
    def test_end(self):
        endArrow = self.trace.endArrow
        endArrow.assertAlmostEqual(Arrow(Location(2.,3.),Direction(1.,0.)))
    def test_along(self):
        alongArrow = self.trace.alongArrow(numpy.pi/2)
        alongArrow.assertAlmostEqual(Arrow(Location(1.,1.),Direction(0.,1.)))
    def test_along2(self):
        alongArrow = self.trace.alongArrow(numpy.pi/2+1+numpy.pi/4)
        alongArrow.assertAlmostEqual(Arrow(Location(2.-1./numpy.sqrt(2),2.+1./numpy.sqrt(2)),Direction(1.,1.)))
    def test_insert(self):
        trace = Trace(Arrow(Location(2.,0.),Direction(0.,-1.)))
        trace.append(LineSegment(1.))
        
        trace.insert(0,Bend(numpy.pi/2,-1))
        trace.startArrow.assertAlmostEqual(Arrow(Location(1.,1.),Direction(1.,0.)))
        trace.insert(0,LineSegment(1.))
        trace.startArrow.assertAlmostEqual(Arrow(Location(0.,1.),Direction(1.,0.)))
    def test_insert2(self):
        trace = Trace(Arrow(Location(2.,0.),Direction(0.,-1)))
        trace.append(LineSegment(0.5))
        trace.append(Bend(numpy.pi/2,1.))
        trace.append(LineSegment(1.0))
        trace.endArrow.assertAlmostEqual(Arrow(Location(4.0,-1.5),Direction(1.,0.)))
        
        trace.insert(2,Bend(numpy.pi/2,-1.))
        trace.startArrow.assertAlmostEqual(Arrow(Location(0.5,-3.5),Direction(1.,0.)))
        trace.insert(2,LineSegment(1.))
        trace.startArrow.assertAlmostEqual(Arrow(Location(0.5,-4.5),Direction(1.,0.)))
        


class Bend_test(unittest.TestCase):
    def setUp(self):
        self.bend = Bend(startArrow=Arrow(Location(0.,0.),Direction(1.,0.)), length=numpy.pi*20./2, bendRadius=20.)
    
    def test_origin(self):
        self.bend.absoluteOrigin().assertAlmostEqual(Location(0.,20.))
        
    def test_endBow(self):
        theEnd = self.bend.endArrow
        theEnd.assertAlmostEqual(Arrow(Location(20.,20.),Direction(0.,1.)))
        
    def test_endBowClockWise(self):
        bend = Bend(startArrow=Arrow(Location(0.,0.),Direction(1.,0.)), length=numpy.pi*20./2, bendRadius=-20.)
        theEnd = bend.endArrow
        theEnd.assertAlmostEqual(Arrow(Location(20.,-20.),Direction(0.,-1.)))

    def test_endBowLeft(self):
        bend = Bend(startArrow=Arrow(Location(0.,0.),Direction(-1.,0.)), length=numpy.pi*20./2, bendRadius=20.)
        theEnd = bend.endArrow
        theEnd.assertAlmostEqual(Arrow(Location(-20.,-20.),Direction(0.,-1.)))

class Rectangle_test(unittest.TestCase):
    def setUp(self):
        self.rectangle = Rectangle(bottomLeft=Location(1,3),topRight=Location(4,5))
    def test_loopThrough(self):
        self.rectangle.bottomLeft.assertAlmostEqual(Location(1,3))
        self.rectangle.topRight.assertAlmostEqual(Location(4,5))

class DrawGroup_test(unittest.TestCase):
    def setUp(self):
        stack = Stack(numberOfFaces=4)        
        class MyGroup(DrawGroup):
            def __init__(self):
                self.append(Rectangle(startArrow=Arrow(Location(0,0),E),width=1,height=3,gerberLayer=stack[0].copper[0]))
                self.append(Rectangle(startArrow=Arrow(Location(3,0),E),width=1,height=3,gerberLayer=stack[0].copper[0]))
        self.group = MyGroup()
    def test_cornerGetter(self):
        self.group.topRight.assertAlmostEqual(Location(4,3))
    def test_cornerSetter(self):
        self.group.topRight = Location(2,2)
        self.group.bottomLeft.assertAlmostEqual(Location(-2,-1))

class Outline_test(unittest.TestCase):
    def test_sort(self):
        rectangleOutline = Rectangle(Arrow(Location(0,0),W),4,4).outline()
        rectangleOutline.bottomLeftmostFirst().assertAlmostEqual(ClosedStrokeContour(
           [Location(-4,-4),
            Location(0,-4),
            Location(0,0),
            Location(-4,0)]))
    def test_encapsulated(self):
        largeOutline = Rectangle(Arrow(Location(0,0),E),4,4).outline()
        smallOutline = Rectangle(Arrow(Location(1,1),E),2,2).outline()
        join = largeOutline + smallOutline
        join.assertAlmostEqual(largeOutline)
#    def test_innerTouching(self):
#        largeOutline = Rectangle(Arrow(Location(0,0),E),4,4).outline()
#        smallOutline = Rectangle(Arrow(Location(2,2),E),2,2).outline()
#        join = smallOutline + largeOutline
#        join.assertAlmostEqual(largeOutline)   
    def test_crossEdge(self):
        largeOutline = Rectangle(Arrow(Location(0,0),E),4,4).outline()
        smallOutline = Rectangle(Arrow(Location(1,3),E),2,2).outline()
        join = smallOutline + largeOutline
        join.assertAlmostEqual(ClosedStrokeContour([Location(0,0),
                                                    Location(4,0),
                                                    Location(4,4),
                                                    Location(3,4),
                                                    Location(3,5),
                                                    Location(1,5),
                                                    Location(1,4),
                                                    Location(0,4)]))
    def test_crossCorner(self):
        largeOutline = Rectangle(Arrow(Location(0,0),E),4,4).outline()
        smallOutline = Rectangle(Arrow(Location(2,0),S),2,2).outline()
        join = smallOutline + largeOutline
        print join
        join.assertAlmostEqual(ClosedStrokeContour([Location(2,-2),
                                                    Location(4,-2),
                                                    Location(4,4),
                                                    Location(0,4),
                                                    Location(0,0),
                                                    Location(2,0) ]))                                                    

if __name__ == '__main__':
    import nose
    nose.run(argv=['-w','../test','-v'])
#     nose.run(defaultTest=__name__)
#     suite = unittest.defaultTestLoader.loadTestsFromTestCase(Bend_test)
#     unittest.TextTestRunner(verbosity=2).run(suite)