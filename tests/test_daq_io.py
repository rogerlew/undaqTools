from __future__ import print_function

# Copyright (c) 2013, Roger Lew
# All rights reserved.

import glob
import os
import time
import unittest

import numpy as np
from numpy.testing import assert_array_equal, \
                          assert_array_almost_equal
from scipy import io as sio

from undaqTools import Daq
from undaqTools.deprecated import old_convert_daq
from undaqTools.misc.base import _flatten

test_file = 'data reduction_20130204125617.daq'

def assert_Daqs_equal(testCase, daq, daq2):

    # attributes
    testCase.assertEqual(daq.f0,     daq2.f0)
    testCase.assertEqual(daq.fend,   daq2.fend)
    testCase.assertEqual(daq.cursor, daq2.cursor)

    if daq.elemlist is None:
        testCase.assertTrue(daq2.elemlist is None)
    else:
        assert_array_equal(daq.elemlist, daq2.elemlist)
    
    # info dict
    testCase.assertEqual(daq.info.run,        daq2.info.run)
    testCase.assertEqual(daq.info.runinst,    daq2.info.runinst)
    testCase.assertEqual(daq.info.numentries, daq2.info.numentries)
    testCase.assertEqual(daq.info.frequency,  daq2.info.frequency)
    testCase.assertEqual(daq.info.date,       daq2.info.date)
    testCase.assertEqual(daq.info.magic,      daq2.info.magic)
    testCase.assertEqual(daq.info.subject,    daq2.info.subject)

    # frame dict
    assert_array_almost_equal(daq.frame.code,  daq2.frame.code)
    assert_array_almost_equal(daq.frame.frame, daq2.frame.frame)
    assert_array_almost_equal(daq.frame.count, daq2.frame.count)
            
    # data dict
    for k in daq2:
        testCase.assertTrue(k in daq)

    for k in daq:
        if daq[k].type == 'c':
            assert_array_equal(daq[k], daq2[k])
        else:
            assert_array_almost_equal(daq[k], daq2[k])
        
class Test_load(unittest.TestCase):
    """
    Validate that the data is read the same as the old convert_daq module
    """
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

    def tearDown(self):
        time.sleep(.1)
        tmp_files = glob.glob('./tmp/*')
        for tmp_file in tmp_files:
            os.remove(tmp_file)

    def test_load(self):
        global test_file
        
        daq = Daq()
        daq.read(os.path.join('data', test_file))

        old_daq = old_convert_daq.read_file(os.path.join('data', test_file))
        self.__assert_old_daq_equals_daq(old_daq, daq)

    def test_load_with_elemlist(self):
        global test_file
        
        daq = Daq()
        daq.load_elemlist_fromfile('elemList2.txt')
        daq.read(os.path.join('data', test_file))
        
        old_daq = old_convert_daq.read_file(os.path.join('data', test_file), 
                                            elemfile='elemList2.txt')

        self.__assert_old_daq_equals_daq(old_daq, daq)
        
    def __assert_old_daq_equals_daq(self, old_daq, daq):

        # info
        for k,v in old_daq['daqInfo'].items():
            self.assertEqual(v, getattr(daq.info, k))

        # header
        # new daq doesn't have header dict. It attaches meta data to the 
        # Element objects. Here we want to make sure that the meta data for 
        # each Element matches the old header dict.
        #
        # When an elemlist is defined the rebuilt header list only contains 
        # the Elements in that are loaded into the daq. The old daq contains 
        # the superset of all the elements that were written to the Daq
        _header = daq._rebuild_header()
        old_daq_elemid_lookup = dict(zip(old_daq['elemInfo']['name'],
                                         old_daq['elemInfo']['id']))

        for name, numvalues, units, rate, type, varrateflag in \
            zip(_header.name, _header.numvalues, _header.units,
                _header.rate, _header.type, _header.varrateflag):
                    
            if name == 'SCC_Spline_Lane_Deviation_Fixed':
                continue
            
            indx = old_daq_elemid_lookup[name]
            self.assertEqual(name, 
                             old_daq['elemInfo']['name'][indx])
            self.assertEqual(numvalues, 
                             old_daq['elemInfo']['numvalues'][indx])
            self.assertEqual(units, 
                             old_daq['elemInfo']['units'][indx])
            self.assertEqual(rate, 
                             old_daq['elemInfo']['rate'][indx])
            self.assertEqual((type,'s')[type=='h'], 
                             old_daq['elemInfo']['type'][indx])
            self.assertEqual(varrateflag, 
                             old_daq['elemInfo']['varrateflag'][indx])          

        # frame
        assert_array_almost_equal(daq.frame.frame, 
                                  old_daq['elemFrames']['frame'])
        assert_array_almost_equal(daq.frame.count, 
                                  old_daq['elemFrames']['count'])
        assert_array_almost_equal(daq.frame.code,  
                                  old_daq['elemFrames']['code'])
        
        # data
        for k in daq:
                
            if k == 'SCC_Spline_Lane_Deviation_Fixed':
                continue
            
            self.assertTrue(k in old_daq['elemData'])
            
        for k in old_daq['elemData']:
            if k == 'Frames':
                old_array = np.array(old_daq['elemData'][k])
                assert_array_almost_equal(daq.frame.frame, old_array)

            elif k.endswith('_Frames'):
                kk = k.replace('_Frames', '')

                old_array = np.array(old_daq['elemData'][k])
                assert_array_almost_equal(daq[kk].frames, old_array)

            else:
                old_array = np.array(old_daq['elemData'][k], ndmin=2)
                if daq[k].type == 'c':
                    assert_array_equal(daq[k], old_array)
                else:
                    assert_array_almost_equal(daq[k], old_array)

class Test_mat(unittest.TestCase):
    """
    Validate that the data is read the same as the old convert_daq module
    """
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

    def tearDown(self):
        time.sleep(.1)
        tmp_files = glob.glob('./tmp/*')
        for tmp_file in tmp_files:
            os.remove(tmp_file)

    def test_load(self):
        global test_file
        matfile = os.path.join('tmp', test_file[:-4]+'1.mat')
        matfile2 = os.path.join('tmp', test_file[:-4]+'2.mat')
        
        daq = Daq()
        daq.read(os.path.join('data', test_file))
        daq.write_mat(matfile)
        del daq
        daqmat = sio.loadmat(matfile)

        old_convert_daq.convert_daq(os.path.join('data', test_file),
                                    '',matfile2)
        old_daqmat = sio.loadmat(matfile2)
        self.__assert_daqmats_equal(old_daqmat, daqmat)

    def test_load_with_elemlist(self):
        global test_file
        matfile = os.path.join('tmp', test_file[:-4]+'11.mat')
        matfile2 = os.path.join('tmp', test_file[:-4]+'22.mat')
        
        daq = Daq()
        daq.load_elemlist_fromfile('elemList2.txt')
        daq.read(os.path.join('data', test_file))
        daq.write_mat(matfile)
        del daq
        daqmat = sio.loadmat(matfile)

        old_convert_daq.convert_daq(os.path.join('data', test_file),
                                    'elemList2.txt',matfile2)
        old_daqmat = sio.loadmat(matfile2)
        self.__assert_daqmats_equal(old_daqmat, daqmat)

    def __assert_daqmats_equal(self, old_daq, new_daq):

        # whoever came up with the sio.loadmat representation
        # obviously wasn't breastfeed as an infant. This made
        # them a deeply sadistic and antisocial individual.
        # The combination of those deep seeded personality flaws
        # eventually lead them to develope this terribly
        # obfuscated datastructure. 
        
        # info
        x1 = dict(zip(old_daq['daqInfo'].dtype.names,
                      list(_flatten(old_daq['daqInfo']))))
        x2 = dict(zip(new_daq['daqInfo'].dtype.names,
                      list(_flatten(new_daq['daqInfo']))))
        for key in x1:
            self.assertEqual(x1[key], x2[key])
        
        # frames
        for name in old_daq['elemFrames'].dtype.names:
            x1 = np.array(list(_flatten(old_daq['elemFrames'][name])))
            x2 = np.array(list(_flatten(new_daq['elemFrames'][name])))
            assert_array_equal(x1, x2)

        # data
        for name in old_daq['elemData'].dtype.names:
            x1 = np.array(list(_flatten(old_daq['elemData'][name])))    
            x2 = np.array(list(_flatten(new_daq['elemData'][name])))

            try:
                is_string = isinstance(x1[0], basestring)
            except:
                is_string = None

            if is_string is not None:
                if is_string:
                    assert_array_equal(x1, x2)
                else:
                    assert_array_almost_equal(x1, x2)
                    
                    
class Test_hd5(unittest.TestCase):
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

    def tearDown(self):
        time.sleep(.1)
        tmp_files = glob.glob('./tmp/*')
        for tmp_file in tmp_files:
            os.remove(tmp_file)
    
    def test_readwrite(self):
        global test_file
        hdf5file = os.path.join('tmp', test_file[:-4]+'_1.hdf5')
                
        daq = Daq()
        daq.read(os.path.join('data', test_file))
        daq.write_hd5(hdf5file)

        daq2 = Daq()
        daq2.read_hd5(hdf5file)

        assert_Daqs_equal(self, daq, daq2)
        
    def test_readwrite_with_elemlist(self):
        global test_file
        hdf5file = os.path.join('tmp', test_file[:-4]+'_2.hdf5')
        
        daq = Daq()
        daq.load_elemlist_fromfile('elemList2.txt')
        daq.read(os.path.join('data', test_file))
        daq.write_hd5(hdf5file)

        daq2 = Daq()
        daq2.read_hd5(hdf5file)

        assert_Daqs_equal(self, daq, daq2)

    def test_readwrite_with_elemlist_f0(self):
        global test_file
        hdf5file = os.path.join('tmp', test_file[:-4]+'_3.hdf5')
                
        daq = Daq()
        daq.load_elemlist_fromfile('elemList2.txt')
        daq.read(os.path.join('data', test_file))
        daq.write_hd5(hdf5file)

        daq2 = Daq()
        daq2.read_hd5(hdf5file, f0=4000)

        self.assertEqual(daq2.frame.frame[0], 4000)
        
    def test_readwrite_with_elemlist_f0fend(self):
        global test_file
        hdf5file = os.path.join('tmp', test_file[:-4]+'_4.hdf5')
        
        daq = Daq()
        daq.load_elemlist_fromfile('elemList2.txt')
        daq.read(os.path.join('data', test_file))
        daq.write_hd5(hdf5file)

        daq2 = Daq()
        daq2.read_hd5(hdf5file, fend=8000)

        self.assertEqual(daq2.frame.frame[-1], 8000)
        
    def test_readwrite_no_data(self):
        global test_file
        hdf5file = os.path.join('tmp', test_file[:-4]+'_5.hdf5')
        
        daq = Daq()
        daq.read(os.path.join('data', test_file))
        daq.write_hd5(hdf5file)

        daq2 = Daq()
        daq2.read_hd5(hdf5file)

        assert_Daqs_equal(self, daq, daq2)

def suite():
    return unittest.TestSuite((
            unittest.makeSuite(Test_load),
##            unittest.makeSuite(Test_mat),
##            unittest.makeSuite(Test_hd5)
                              ))

if __name__ == "__main__":
    # run tests
    runner = unittest.TextTestRunner()
    runner.run(suite())
