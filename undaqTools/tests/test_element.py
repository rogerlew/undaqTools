from __future__ import print_function

# Copyright (c) 2013, Roger Lew
# All rights reserved.

import os
import unittest

import numpy as np
from scipy.signal import detrend
from numpy.testing import assert_array_equal

from undaqTools import Daq, Element, fslice, findex

test_file = 'data reduction_20130204125617.daq'

class Test_element(unittest.TestCase):   
    def setUp(self):
        self.x = Element([24,245,6325,2435,245,1234,14,234,548],
                         range(3000, 3009))
    def test0(self):
        x = self.x
                               
        self.assertTrue(isinstance(x, Element))
        
    def test1(self):
        x = self.x
                               
        self.assertRaises(NotImplementedError, x.transpose)
        
        
    def test2(self):
        x = self.x
                                   
        self.assertRaises(NotImplementedError, lambda x : x.T, x)
        
# daq['TPR_Tire_Surf_Type'] = \
#Element(data = [[11  1  1 11 11 11  1  1 11 11  3  3  3  3  3  3 11 11  1  1 11 11  1  1]
#                [11  1  1 11 11 11  1  1 11 11 11 11  3  3 11 11 11 11  1  1 11 11  1  1]
#                [11 11  1  1  1 11 11  1  1 11 11  3  3  3  3  3  3 11 11  1  1 11 11  1]
#                [11 11  1  1 11 11 11  1  1 11 11 11 11  3  3 11 11 11 11  1  1 11 11  1]
#                [ 0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0]
#                [ 0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0]
#                [ 0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0]
#                [ 0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0]
#                [ 0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0]
#                [ 0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0]],
#      frames = [ 2716  5519  5523  5841  5844  5845  7970  7973  8279  8284  8785  8791
#                 8818  8824  9127  9132  9166  9171 10270 10274 10597 10600 12655 12659],
#        name = 'TPR_Tire_Surf_Type',
#   numvalues = 10,
#        rate = -1 (CSSDC),
# varrateflag = False,
#      nptype = int16)

class Test_getitem(unittest.TestCase):    
    def setUp(self):
        self.x = Element([24,245,6325,2435,245,1234,14,234,548],
                         range(3000, 3009))
                         
    def test0(self):
        x = self.x
        
        assert_array_equal([[24,245,6325]], x[:, :3])
        assert_array_equal([3000,3001,3002], x[:, :3].frames)
                               
    def test1(self):
        x = self.x
        
        assert_array_equal([24,245,6325], x[0, :3])
        assert_array_equal([3000,3001,3002], x[0, :3].frames)
                                       
class Test_setitem(unittest.TestCase):    
    def setUp(self):
        self.x = Element([24,245,6325,2435,245,1234,14,234,548],
                         range(3000, 3009))
                         
    def test0(self):
        x = self.x

        x[0,2] = 99
        assert_array_equal([[24,245,99,2435,245,1234,14,234,548]], x)
        assert_array_equal(range(3000, 3009), x.frames)

    def test1(self):
        x = self.x
        
        x[:,:3] = [[99,99,99]]
        assert_array_equal([[99,99,99,2435,245,1234,14,234,548]], x)
        assert_array_equal(range(3000, 3009), x.frames)
        
    def test2(self):
        x = self.x
                    
        rs = [[-2016.,-1599.,4677.,983.,-1011.,174.,-850.,-434.,76.]]
        
        x[:,:] = detrend(x)
        assert_array_equal(rs, x)
        assert_array_equal(range(3000, 3009), x.frames)
        
class Test_state_at_frame(unittest.TestCase):    
    def test0(self):
        """frame between values"""
        global testfile
        hdf5file = test_file[:-4]+'.hdf5'
        daq = Daq()
        daq.read_hd5(os.path.join('data', hdf5file))
        
        rs= np.array( [[11],[11],[11],[11],[ 0],[ 0],[ 0],[ 0],[ 0],[ 0]], 
                      dtype=np.int16)
    
        ds = daq['TPR_Tire_Surf_Type'][:, findex(7000)]
        
        assert_array_equal(rs, ds)
                               
        self.assertFalse(isinstance(ds, Element))

    def test1(self):
        """frame less than element.frames[0]"""
        global testfile
        hdf5file = test_file[:-4]+'.hdf5'
        daq = Daq()
        daq.read_hd5(os.path.join('data', hdf5file))
    
        ds = daq['TPR_Tire_Surf_Type'][:,findex(0)]
        
        self.assertTrue(np.isnan(ds))
                               
    def test2(self):
        """frame > element.frames[-1]"""
        global testfile
        hdf5file = test_file[:-4]+'.hdf5'
        daq = Daq()
        daq.read_hd5(os.path.join('data', hdf5file))
                
        rs= np.array( [[ 1],[ 1],[ 1],[ 1],[ 0],[ 0],[ 0],[ 0],[ 0],[ 0]], 
                      dtype=np.int16)
                      
        ds = daq['TPR_Tire_Surf_Type'][:, findex(13000)]
        assert_array_equal(rs, ds)
        self.assertFalse(isinstance(ds, Element))
   
    def test3(self):
        """on defined frame"""
        global testfile
        hdf5file = test_file[:-4]+'.hdf5'
        daq = Daq()
        daq.read_hd5(os.path.join('data', hdf5file))
        
        rs= np.array( [[11],[11],[ 1],[ 1],[ 0],[ 0],[ 0],[ 0],[ 0],[ 0]], 
                      dtype=np.int16)
        
        ds = daq['TPR_Tire_Surf_Type'][:,findex(5841)]
        assert_array_equal(rs[:,0], ds[:,0])
        self.assertFalse(isinstance(ds, Element))

    def test4(self):
        """just after defined frame"""
        global testfile
        hdf5file = test_file[:-4]+'.hdf5'
        daq = Daq()
        daq.read_hd5(os.path.join('data', hdf5file))
        
        rs= np.array( [[11],[11],[ 1],[ 1],[ 0],[ 0],[ 0],[ 0],[ 0],[ 0]], 
                      dtype=np.int16)
                     
        ds = daq['TPR_Tire_Surf_Type'][:,findex(5842)]
        assert_array_equal(rs[:,0], ds[:,0])
        self.assertFalse(isinstance(ds, Element))
        
    def test5(self):
        """just before defined frame"""
        global testfile
        hdf5file = test_file[:-4]+'.hdf5'
        daq = Daq()
        daq.read_hd5(os.path.join('data', hdf5file))
        
        rs= np.array( [[1],[1],[ 1],[ 1],[ 0],[ 0],[ 0],[ 0],[ 0],[ 0]], 
                      dtype=np.int16)
        
        ds = daq['TPR_Tire_Surf_Type'][:,findex(5840)]
        assert_array_equal(rs[:,0], ds[:,0])
        self.assertFalse(isinstance(ds, Element))
        
    def test6(self):
        """row indx slice"""
        global testfile
        hdf5file = test_file[:-4]+'.hdf5'
        daq = Daq()
        daq.read_hd5(os.path.join('data', hdf5file))
        
        rs= np.array( [[1],[1],[ 1],[ 1]], 
                      dtype=np.int16)
        
        ds = daq['TPR_Tire_Surf_Type'][:4, findex(5840)]
        assert_array_equal(rs[:,0], ds[:,0])
        self.assertFalse(isinstance(ds, Element))
        
    def test7(self):
        """row indx int"""
        global testfile
        hdf5file = test_file[:-4]+'.hdf5'
        daq = Daq()
        daq.read_hd5(os.path.join('data', hdf5file))
        
        ds = daq['TPR_Tire_Surf_Type'][3, findex(5840)]
        self.assertEqual(1, ds)
        
    def test8(self):
        """row indx int"""
        global testfile
        hdf5file = test_file[:-4]+'.hdf5'
        daq = Daq()
        daq.read_hd5(os.path.join('data', hdf5file))
        
        ds = daq['TPR_Tire_Surf_Type'][4, findex(5840)]
        self.assertEqual(0, ds)
        
class Test_frame_slice(unittest.TestCase):      
    def setUp(self):
        self.x = Element([[24,245,6325,2435,245,1234,14,234,548]],
                         range(3000, 3009))
                               
    def test0(self):
        x = self.x
        rs = np.array([[   24.,   245.,  6325.,  2435.]])
        
        assert_array_equal(x[:, fslice(3004)], rs)
        
    def test00(self):
        x = self.x
        rs = np.array([3000, 3001, 3002, 3003])
        assert_array_equal(x[:, fslice(3004)].frames, rs)
        
    def test1(self):
        x = self.x
        rs = np.array([[   245.,  6325.,  2435.]])
        assert_array_equal(x[:, fslice(3001, 3004)], rs)
        
    def test2(self):
        x = self.x
        rs = np.array([[24,6325,245,14,548]])
        assert_array_equal(x[:, fslice(None, None, 2)], rs)
                
    def test3(self):
        x = self.x
        rs = np.array([[24,245,6325,2435,245,1234,14,234,548]])
        ds = x[:, fslice(3000, 3009)]
        assert_array_equal(ds, rs)

class Test_isCSSDC(unittest.TestCase):      
    def setUp(self):
        global test_file
        hdf5file = test_file[:-4]+'.hdf5'
        hdf5file = os.path.join('data', hdf5file)
        
        try:
           with open(hdf5file):
               pass
        except IOError:
           daq = Daq()
           daq.read(os.path.join('data', test_file))
           daq.write_hd5(hdf5file)
           
    def test0(self):
        global test_file
        hdf5file = test_file[:-4]+'.hdf5'
        daq = Daq()
        daq.read_hd5(os.path.join('data', hdf5file))
        
        self.assertFalse(daq['VDS_Veh_Speed'].isCSSDC())
    
    def test1(self):
        global testfile
        hdf5file = test_file[:-4]+'.hdf5'
        daq = Daq()
        daq.read_hd5(os.path.join('data', hdf5file))
        
        self.assertTrue(daq['TPR_Tire_Surf_Type'].isCSSDC())

class Test_toarray(unittest.TestCase):    
    def setUp(self):
        global test_file
        hdf5file = test_file[:-4]+'.hdf5'
        hdf5file = os.path.join('data', hdf5file)
        
        try:
           with open(hdf5file):
               pass
        except IOError:
           daq = Daq()
           daq.read(os.path.join('data', test_file))
           daq.write_hd5(hdf5file)
           
    def test0(self):
        global testfile
        hdf5file = test_file[:-4]+'.hdf5'
        daq = Daq()
        daq.read_hd5(os.path.join('data', hdf5file))
        
        ds =daq['VDS_Veh_Speed'].toarray()
        self.assertFalse(isinstance(ds, Element))
        self.assertEqual(ds.shape, (1L, 10658L))
        
def suite():
    return unittest.TestSuite((
            unittest.makeSuite(Test_element),
            unittest.makeSuite(Test_getitem),
            unittest.makeSuite(Test_setitem),
            unittest.makeSuite(Test_state_at_frame),
            unittest.makeSuite(Test_frame_slice),
            unittest.makeSuite(Test_isCSSDC),
            unittest.makeSuite(Test_toarray)
                              ))

if __name__ == "__main__":
    # run tests
    runner = unittest.TextTestRunner()
    runner.run(suite())
   
