from __future__ import print_function

# Copyright (c) 2013, Roger Lew
# All rights reserved.

import unittest
import os
import glob
import time

from numpy.testing import assert_array_almost_equal
import matplotlib.pyplot as plt           
plt.rc('font', family='serif')

from undaqTools import Daq
from undaqTools.dynobj import DynObj

test_file_large = 'Alaska_0_20130301142422.daq'

def assert_dynobjs_equal(self, do, do2):
    self.assertEqual(do.i0, do2.i0)
    self.assertEqual(do.iend, do2.iend)
    self.assertEqual(do.hcsmType, do2.hcsmType)
    self.assertEqual(do.colorIndex, do2.colorIndex)
    self.assertEqual(do.solId, do2.solId)
    self.assertEqual(do.cvedId, do2.cvedId)
    self.assertEqual(do.name, do2.name)
    self.assertEqual(do.interpolated, do2.interpolated)
    self.assertEqual(do.direction, do2.direction)
    self.assertAlmostEqual(do.relative_distance_err,
                           do2.relative_distance_err)
    
    assert_array_almost_equal(do.frames, do2.frames)
    assert_array_almost_equal(do.heading, do2.heading)
    assert_array_almost_equal(do.speed, do2.speed)
    assert_array_almost_equal(do.roll, do2.roll)
    assert_array_almost_equal(do.pitch, do2.pitch)
    assert_array_almost_equal(do.pos, do2.pos)
    assert_array_almost_equal(do.distance, do2.distance)
    assert_array_almost_equal(do.relative_distance, do2.relative_distance, 4)
    
class Test_dynobjs(unittest.TestCase):
    def setUp(self):
        global test_file_large
        hdf5file = test_file_large[:-4]+'.hdf5'
        hdf5file = os.path.join('data', hdf5file)
        
        try:
           with open(hdf5file):
               pass
        except IOError:
           daq = Daq()
           daq.read(os.path.join('data', test_file_large))
           daq.write_hd5(hdf5file)

    def tearDown(self):
        time.sleep(.1)
        tmp_files = glob.glob('./tmp/*')
        for tmp_file in tmp_files:
            os.remove(tmp_file)
        
    def test_process(self):
        global test_file_large
                
        daq = Daq()
        daq.read(os.path.join('data', test_file_large))
        daq.write_hd5('./tmp/dynobj_process_test.hdf5')
        
    def test_readwrite_hd5_file(self):
        global test_file_large
        hdf5file = test_file_large[:-4]+'.hdf5'
                
        daq = Daq()
        daq.read_hd5(os.path.join('data', hdf5file))
        do = daq.dynobjs.values()[0]

        do.write_hd5(filename='./tmp/dynobj_test.hdf5')

        do2 = DynObj()
        do2.read_hd5('./tmp/dynobj_test.hdf5')

        assert_dynobjs_equal(self, do, do2)

    def test_test_readwrite_hd5_reference(self):
        global test_file_large
        hdf5file = test_file_large[:-4]+'.hdf5'
        hdf5file = os.path.join('data', hdf5file)
                
        daq = Daq()
        daq.read_hd5(hdf5file)
        
        daq2 = Daq()
        daq2.read_hd5(hdf5file)
        for name in daq2.dynobjs.keys():
            assert_dynobjs_equal(self,
                                 daq.dynobjs[name],
                                 daq2.dynobjs[name])
        
def suite():
    return unittest.TestSuite((
            unittest.makeSuite(Test_dynobjs)
                              ))

if __name__ == "__main__":
    # run tests
    runner = unittest.TextTestRunner()
    runner.run(suite())
