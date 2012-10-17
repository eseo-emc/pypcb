import unittest
import nose
import numpy

from geometry import *

class Location_test(unittest.TestCase):
    def test_subtraction(self):
        a = Location(1.,2.)
        b = Location(3.,-1.5)
        self.assertEqual(type(a-b),Vector)
        (a-b).assertAlmostEqual(Vector(-2.,3.5))

class UnitVector_test(unittest.TestCase):
    def setUp(self):
        self.UnitVector = UnitVector(-3.,3.)
    def test_UnitVector(self):
        self.UnitVector.assertAlmostEqual(numpy.array([-1/numpy.sqrt(2),+1/numpy.sqrt(2)]))

class Arrow_test(unittest.TestCase):
    def setUp(self):
        self.arrow = Arrow(Location(0.,1.),UnitVector(-1.,1.))
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

class Line_test(unittest.TestCase):
    def setUp(self):
        self.line = Line(startArrow=Arrow(Location(0.0,1.0),UnitVector(1.,1.)),length=3*numpy.sqrt(2.))
    def test_lineEnd(self):
        self.line.endArrow.assertAlmostEqual(Arrow(Location(3.,4.),UnitVector(1.,1.)))

class Trace_test(unittest.TestCase):
    def setUp(self):
        self.trace = Trace(Arrow(Location(0.,0.),UnitVector(1.,0.)))
        self.trace.append(Bend(numpy.pi/2,1.))
        self.trace.append(Line(1.))
        self.trace.append(Bend(numpy.pi/2,-1.))
    def test_end(self):
        endArrow = self.trace.endArrow
        endArrow.assertAlmostEqual(Arrow(Location(2.,3.),UnitVector(1.,0.)))
    def test_along(self):
        alongArrow = self.trace.alongArrow(numpy.pi/2)
        alongArrow.assertAlmostEqual(Arrow(Location(1.,1.),UnitVector(0.,1.)))
    def test_along2(self):
        alongArrow = self.trace.alongArrow(numpy.pi/2+1+numpy.pi/4)
        alongArrow.assertAlmostEqual(Arrow(Location(2.-1./numpy.sqrt(2),2.+1./numpy.sqrt(2)),UnitVector(1.,1.)))
    def test_insert(self):
        trace = Trace(Arrow(Location(2.,0.),UnitVector(0.,-1.)))
        trace.append(Line(1.))
        
        trace.insert(0,Bend(numpy.pi/2,-1))
        trace.startArrow.assertAlmostEqual(Arrow(Location(1.,1.),UnitVector(1.,0.)))
        trace.insert(0,Line(1.))
        trace.startArrow.assertAlmostEqual(Arrow(Location(0.,1.),UnitVector(1.,0.)))
    def test_insert2(self):
        trace = Trace(Arrow(Location(2.,0.),UnitVector(0.,-1)))
        trace.append(Line(0.5))
        trace.append(Bend(numpy.pi/2,1.))
        trace.append(Line(1.0))
        trace.endArrow.assertAlmostEqual(Arrow(Location(4.0,-1.5),UnitVector(1.,0.)))
        
        trace.insert(2,Bend(numpy.pi/2,-1.))
        trace.startArrow.assertAlmostEqual(Arrow(Location(0.5,-3.5),UnitVector(1.,0.)))
        trace.insert(2,Line(1.))
        trace.startArrow.assertAlmostEqual(Arrow(Location(0.5,-4.5),UnitVector(1.,0.)))
        


class Bend_test(unittest.TestCase):
    def setUp(self):
        self.bend = Bend(startArrow=Arrow(Location(0.,0.),UnitVector(1.,0.)), length=numpy.pi*20./2, bendRadius=20.)
    
    def test_origin(self):
        self.bend.absoluteOrigin().assertAlmostEqual(Location(0.,20.))
        
    def test_endBow(self):
        theEnd = self.bend.endArrow
        theEnd.assertAlmostEqual(Arrow(Location(20.,20.),UnitVector(0.,1.)))
        
    def test_endBowClockWise(self):
        bend = Bend(startArrow=Arrow(Location(0.,0.),UnitVector(1.,0.)), length=numpy.pi*20./2, bendRadius=-20.)
        theEnd = bend.endArrow
        theEnd.assertAlmostEqual(Arrow(Location(20.,-20.),UnitVector(0.,-1.)))

    def test_endBowLeft(self):
        bend = Bend(startArrow=Arrow(Location(0.,0.),UnitVector(-1.,0.)), length=numpy.pi*20./2, bendRadius=20.)
        theEnd = bend.endArrow
        theEnd.assertAlmostEqual(Arrow(Location(-20.,-20.),UnitVector(0.,-1.)))

if __name__ == '__main__':
    import nose
    nose.run(argv=['-w','../test','-v'])
#     nose.run(defaultTest=__name__)
#     suite = unittest.defaultTestLoader.loadTestsFromTestCase(Bend_test)
#     unittest.TextTestRunner(verbosity=2).run(suite)