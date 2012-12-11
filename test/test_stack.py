import unittest
import nose
import numpy

from pypcb import *

class Eurocircuits_test(unittest.TestCase):
    def setUp(self):
        self.classification = EuroCircuits6C()
    def test_normalise(self):
        '''http://www.eurocircuits.nl/images/stories/ec09/ec-design-guidelines-dutch-1-2010-v3.pdf'''
        self.assertAlmostEqual(self.classification.normaliseProductionHoleDiameter(mil(31)),0.80)
        self.assertAlmostEqual(self.classification.normaliseProductionHoleDiameter(mil(32)),0.80)
        self.assertAlmostEqual(self.classification.normaliseProductionHoleDiameter(mil(33)),0.85)

if __name__ == '__main__':
    import nose
    nose.run(argv=['-w','../test','-v'])
#     nose.run(defaultTest=__name__)
#     suite = unittest.defaultTestLoader.loadTestsFromTestCase(Bend_test)
#     unittest.TextTestRunner(verbosity=2).run(suite)