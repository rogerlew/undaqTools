Example 03: Collaborate timeseries measures
--------------------------------------------
Walks through directory structure and collaborates timeseries 
based on metadata in the etc dictionaries and writes the 
aggregated data to a csv file.

By using a multiprocessing pool and specifying an elemlist
to read_hd5 the datafiles can be quickly traversed.


::

    from __future__ import print_function

    # Copyright (c) 2013, Roger Lew
    # All rights reserved.

    """
    Example timeseries reduction
    """

    from collections import OrderedDict
    import glob
    import os
    import multiprocessing
    import time

    import numpy as np

    from pyvttbl import DataFrame

    from undaqTools import Daq

    # dependent variables and indices that we want to analyze
    dvs = [('CFS_Accelerator_Pedal_Position', 0),
           ('CFS_Brake_Pedal_Force', 0),
           ('CFS_Steering_Wheel_Angle', 0),
           ('SCC_Lane_Deviation', 1),
           ('VDS_Veh_Speed', 0)]

    elemlist = [elem for elem,indx in dvs]

    def collaborate_timeseries(hd5_file):
        global dvs, elemlist
        
        # load hd5
        daq = Daq()
        daq.read_hd5(hd5_file, elemlist=elemlist)

        results_list = []
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

            results_list.append(row)

        return results_list


    if __name__ == '__main__':
        
        # data is on a local SSD drive.
        data_dir = 'C:\\LocalData\\Left Lane\\'
        
        # change the directory of the kernel
        print("Changing wd to '%s'"%data_dir)    
        os.chdir(data_dir)

        print('\nCollaborating timeseries measures...')
        t0 = time.time()
        hd5_files = tuple(glob.glob('*/*.hdf5'))

        # parallel worker pool
        hd5_files = tuple(glob.glob('*/*.hdf5'))
        numcpus = 8
        pool = multiprocessing.Pool(numcpus)
        list_of_results_lists = pool.imap(collaborate_timeseries, hd5_files)

        # pyvttbl is in pypi
        # container to hold the collaborated results
        df = DataFrame()
        for i, result_list in enumerate(list_of_results_lists):
            print('%s analyzed.'%hd5_files[i])
            for row in result_list:
                df.insert(row)

        df.write(fname='collaborated_ts.csv')
        
        print('\nDone.\n\ncollaborating timeseries measures took %.1f s'%(time.time()-t0))        
     

Example Output::

    Changing wd to 'C:\LocalData\Left Lane\'

    Collaborating timeseries measures...
    Part01\Left_01_20130424102744.hdf5 analyzed.
    Part02\Left_02_20130425084730.hdf5 analyzed.
    Part03\Left_03_20130425102301.hdf5 analyzed.
    Part04\Left_04_20130425142804.hdf5 analyzed.
    Part05\Left_05_20130425161122.hdf5 analyzed.
    Part06\Left_06_20130426111502.hdf5 analyzed.
    Part07\Left_07_20130426143846.hdf5 analyzed.
    Part08\Left_08_20130426164114.hdf5 analyzed.
    Part08\Left_08_20130426164301.hdf5 analyzed.
    Part09\Left09_20130423155149.hdf5 analyzed.
    Part10\Left10_20130423155149.hdf5 analyzed.
    Part111\Left_11_20130430081052.hdf5 analyzed.
    Part12\Left_12_20130429163745.hdf5 analyzed.
    Part13\Left_13_20130429182923.hdf5 analyzed.
    Part14\Left_14_20130430102504.hdf5 analyzed.
    Part15\Left_15_20130430171947.hdf5 analyzed.
    Part16\Left_16_20130501103917.hdf5 analyzed.
    Part170\Left_17_20130501163745.hdf5 analyzed.
    Part18\Left_18_20130502084422.hdf5 analyzed.
    Part18\Left_18_reset_20130502090909.hdf5 analyzed.
    Part19\Left_19_20130502153547.hdf5 analyzed.
    Part200\Left_20_20130509094509.hdf5 analyzed.

    Done.

    collaborating timeseries measures took 18.0 s
    
Traversing 30 GB of data in 18 seconds with 100 lines of code 
is a pretty impressive feat if you ask me.