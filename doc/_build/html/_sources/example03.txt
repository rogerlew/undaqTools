Example 03: Collaborate timeseries measures
--------------------------------------------
Walks through directory structure and collaborates timeseries 
based on metadata in the etc dictionaries and writes the 
aggregated data to a csv file

::

from __future__ import print_function

from collections import OrderedDict
import os
import glob
import time

import numpy as np

from pyvttbl import DataFrame

from   undaqTools import Daq

# dependent variables and indices that we want to analyze
dvs = [('CFS_Accelerator_Pedal_Position', 0),
       ('CFS_Brake_Pedal_Force', 0),
       ('CFS_Steering_Wheel_Angle', 0),
       ('SCC_Lane_Deviation', 1),
       ('VDS_Veh_Speed', 0)]

if __name__ == '__main__':
    
    # data is on a local SSD drive. This is very important for performance.
    data_dir = 'C:\\LocalData\\Left Lane\\'
    
    # change the directory of the kernel
    print("Changing wd to '%s'"%data_dir)    
    os.chdir(data_dir)

    # pyvttbl is in pypi
    # container to hold the collaborated results
    df = DataFrame()
    
    print('\nCollaborating timeseries measures...')
    t0 = time.time()
    hd5_files = tuple(glob.glob('*/*.hdf5'))

    for hd5_file in hd5_files:
        print("  analyzing '%s'..."%hd5_file)
        
        # load hd5
        daq = Daq()
        daq.read_hd5(hd5_file)

        # daq.etc was configured in Example02_*
        for (epoch, fslice) in daq.etc['epochs'].items():
            
            # figure out pid and independent variable conditions
            pid = daq.etc['pid']
            trial = epoch / 10
            scenario = daq.etc['scen_order'][trial]
            section = epoch % 10 

            # pack pid and IV conditions into OrderedDict
            row = OrderedDict([('pid', pid),
                               ('trial', trial),
                               ('scenario', scenario),
                               ('section', section)])
            
            for (dv, indx) in dvs:
                vec = daq[dv][indx,fslice].flatten()

                row['%s_mean'%dv] = np.mean(vec)
                row['%s_min'%dv] = np.min(vec)
                row['%s_max'%dv] = np.max(vec)
                row['%s_range'%dv] = row['%s_max'%dv] - row['%s_min'%dv]
                row['%s_amean'%dv] = np.mean(np.abs(vec))
                row['%s_sd'%dv] = np.std(vec)
                row['%s_rms'%dv] = np.linalg.norm(vec)/np.sqrt(len(vec))

            # insert the row into the dataframe
            df.insert(row)

    df.write(fname='collaborated_ts.csv')
    
    print('\nDone.\n\ncollaborating timeseries measureas took %.1f s'%(time.time()-t0))        

Example Output::

    Changing wd to 'C:\LocalData\Left Lane\'

    Collaborating timeseries measures...
      analyzing 'Part01\Left_01_20130424102744.hdf5'...
      analyzing 'Part02\Left_02_20130425084730.hdf5'...
      analyzing 'Part03\Left_03_20130425102301.hdf5'...
      analyzing 'Part04\Left_04_20130425142804.hdf5'...
      analyzing 'Part05\Left_05_20130425161122.hdf5'...
      analyzing 'Part06\Left_06_20130426111502.hdf5'...
      analyzing 'Part07\Left_07_20130426143846.hdf5'...
      analyzing 'Part08\Left_08_20130426164114.hdf5'...
      analyzing 'Part08\Left_08_20130426164301.hdf5'...
      analyzing 'Part09\Left09_20130423155149.hdf5'...
      analyzing 'Part10\Left10_20130423155149.hdf5'...
      analyzing 'Part111\Left_11_20130430081052.hdf5'...
      analyzing 'Part12\Left_12_20130429163745.hdf5'...
      analyzing 'Part13\Left_13_20130429182923.hdf5'...
      analyzing 'Part14\Left_14_20130430102504.hdf5'...
      analyzing 'Part15\Left_15_20130430171947.hdf5'...
      analyzing 'Part16\Left_16_20130501103917.hdf5'...
      analyzing 'Part170\Left_17_20130501163745.hdf5'...
      analyzing 'Part18\Left_18_20130502084422.hdf5'...
      analyzing 'Part18\Left_18_reset_20130502090909.hdf5'...
      analyzing 'Part19\Left_19_20130502153547.hdf5'...
      analyzing 'Part200\Left_20_20130509094509.hdf5'...

    Done.

    collaborating timeseries measureas took 182.5 s
