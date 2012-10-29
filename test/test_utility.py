import unittest
from pypcb import *

class RotatableList_test(unittest.TestCase):
    def setUp(self):
        self.testList = RotatableList([1,2,3,4,5])
    def test_shiftTwo(self):
        self.assertEqual(self.testList >> 2,RotatableList([4,5,1,2,3]))
    def test_loopback(self):
        self.assertEqual(self.testList >> 2 << 2,self.testList)
        
if __name__ == '__main__':
#     import nose
#     nose.run(argv=['-w','../test','-v'])
#     nose.run(defaultTest=__name__)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RotatableList_test)
    unittest.TextTestRunner(verbosity=2).run(suite)