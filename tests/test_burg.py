import unittest
import numpy as np
from numpy.testing import assert_array_almost_equal

from undaqTools.misc.burg import arburg

test_data = './data/4compsintest1000points'

class Test_burg(unittest.TestCase):
    
    def test0(self):
        d = np.array([1.00000e-00,
                      -3.2581e-01,
                       3.4571e-04,
                       3.3790e-02,
                       9.8853e-02])
        r = arburg([1,2,3,4,5,6,7,-8], 4)
        np.testing.assert_array_almost_equal(r, d, decimal=5)

    def test1(self):

        r = [None,
             np.array([ 1. , -0.94200795]) ,
             np.array([ 1. , -1.82697124,  0.93944355]) ,
             np.array([ 1. , -2.7532477 ,  2.74080825, -0.98598416]) ,
             np.array([ 1. , -3.73744923,  5.47666121, -3.73425407,  0.99819203]) ,
             np.array([ 1. , -4.73317429,  9.2016863 , -9.19738005,  4.72640438, -0.99752856]) ,
             np.array([ 1. , -5.51461918,  12.90426156, -16.40243257, 11.93483034,  -4.70540723,   0.78338097]) ,
             np.array([ 1. , -5.39214752,  12.16863091, -14.53657345,  9.37051837,  -2.68798986,  -0.07875969,   0.1563373 ]) ,
             np.array([ 1. , -5.4893526 ,  12.21760094, -12.86527508,  3.54425679,   6.35034463,  -7.64479007,   3.5089866 ,  -0.62176513])]

        data = map(float, open(test_data).read().split())
        for order in xrange(1,9):
            assert_array_almost_equal(arburg(data, order),r[order])
 
def suite():
    return unittest.TestSuite((
            unittest.makeSuite(Test_burg)
                              ))

if __name__ == "__main__":
    # run tests
    runner = unittest.TextTestRunner()
    runner.run(suite())
    
