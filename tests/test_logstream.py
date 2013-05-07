from __future__ import print_function

# Copyright (c) 2013, Roger Lew
# All rights reserved.

from collections import OrderedDict
import os
import unittest

from undaqTools import Daq, logstream
from undaqTools.element import FrameSlice

# test file must have step changes in logstream
test_file_large = 'Alaska_0_20130301142422.daq'

class Test_logstream(unittest.TestCase):
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

    def test_find_epochs(self):
        global test_file_large
        hdf5file = test_file_large[:-4]+'.hdf5'
        hdf5file = os.path.join('data', hdf5file)
        daq = Daq()
        daq.read_hd5(hdf5file)
        logstream0 = daq['SCC_LogStreams'][0,:]

        rs = OrderedDict(
                 [(1,  FrameSlice(start=313314, stop=313826, step=None)), 
                  (2,  FrameSlice(start=313826, stop=317218, step=None)), 
                  (3,  FrameSlice(start=317218, stop=317734, step=None)), 
                  (11, FrameSlice(start=336734, stop=337242, step=None)), 
                  (12, FrameSlice(start=337242, stop=340658, step=None)), 
                  (13, FrameSlice(start=340658, stop=341198, step=None)), 
                  (21, FrameSlice(start=357834, stop=358330, step=None)), 
                  (22, FrameSlice(start=358330, stop=361818, step=None)), 
                  (23, FrameSlice(start=361818, stop=362362, step=None)), 
                  (31, FrameSlice(start=381626, stop=382126, step=None)), 
                  (32, FrameSlice(start=382126, stop=385446, step=None)), 
                  (33, FrameSlice(start=385446, stop=385918, step=None)), 
                  (41, FrameSlice(start=407334, stop=407814, step=None)), 
                  (42, FrameSlice(start=407814, stop=411238, step=None)), 
                  (43, FrameSlice(start=411238, stop=411746, step=None))]
                        )
                          
        epochs = logstream.find_epochs(logstream0)
        
        self.assertEqual(epochs, rs)        

def suite():
    return unittest.TestSuite((
            unittest.makeSuite(Test_logstream)
                              ))

if __name__ == "__main__":
    # run tests
    runner = unittest.TextTestRunner()
    runner.run(suite())
