from __future__ import print_function

import glob
import os
import time
import unittest

from undaqTools import Daq, frame_range

# Python 2 to 3 workarounds
import sys
if sys.version_info[0] == 2:
    _strobj = basestring
    _xrange = xrange
elif sys.version_info[0] == 3:
    _strobj = str
    _xrange = range
    
test_file = 'data reduction_20130204125617.daq'
##test_file_large = 'Alaska_0_20130301142422.daq'

class Test_plot(unittest.TestCase):
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
        time.sleep(.5)
        tmp_files = glob.glob('./tmp/*')
        for tmp_file in tmp_files:
            os.remove(tmp_file)
            
    def test0(self):
        global test_file
        hdf5file = test_file[:-4]+'.hdf5'
    
        elems_indxs = [('CFS_Accelerator_Pedal_Position', 0),
                       ('SCC_Spline_Lane_Deviation', 1),
                       ('SCC_Spline_Lane_Deviation_Fixed', 0),
                       ('SCC_Spline_Lane_Deviation', 3),
                       ('VDS_Tire_Weight_On_Wheels', slice(0,4))]
                     
        daq = Daq()
        daq.read_hd5(os.path.join('data', hdf5file))
        fig = daq.plot_ts(elems_indxs)
        fig.savefig('./output/daq_plots_test.png')

    def test1(self):
        global test_file
        hdf5file = test_file[:-4]+'.hdf5'
    
        elems_indxs = [('CFS_Accelerator_Pedal_Position', 0),
                       ('SCC_Spline_Lane_Deviation', 1),
                       ('SCC_Spline_Lane_Deviation', 3),
                       ('VDS_Tire_Weight_On_Wheels', slice(0,4))]
                     
        daq = Daq()
        daq.read_hd5(os.path.join('data', hdf5file))
#        print(daq['VDS_Tire_Weight_On_Wheels'].frames.shape)
        fig = daq.plot_ts(elems_indxs, frame_range(6000, None))
        fig.savefig('./output/daq_plots_test.png')

def suite():
    return unittest.TestSuite((
            unittest.makeSuite(Test_plot)
                              ))

if __name__ == "__main__":
    # run tests
    runner = unittest.TextTestRunner()
    runner.run(suite())
