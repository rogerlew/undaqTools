from __future__ import print_function

# Copyright (c) 2013, Roger Lew
# All rights reserved.

"""
Example timeseries reduction
"""

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
