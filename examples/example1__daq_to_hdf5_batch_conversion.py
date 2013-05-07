from __future__ import print_function

# Copyright (c) 2013, Roger Lew
# All rights reserved.

"""
Batch convert daq files to HDF5 in parallel using the multiprocessing module

Example Output:
Changing wd to 'C:\\LocalData\\Left Lane\\'

Glob Summary
--------------------------------------------------------------------
daq                                            size (KB) hdf5 exists
--------------------------------------------------------------------
Part01\Left_01_20130424102744.daq              1,535,587        True
Part02\Left_02_20130425084730.daq              1,543,370        True
Part03\Left_03_20130425102301.daq              1,518,779        True
Part04\Left_04_20130425142804.daq              1,387,550        True
Part05\Left_05_20130425161122.daq              1,609,689        True
Part06\Left_06_20130426111502.daq              1,364,879        True
Part07\Left_07_20130426143846.daq              1,509,513        True
Part08\Left_08_20130426164114.daq                  4,565        True
Part08\Left_08_20130426164301.daq              1,426,507        True
Part09\Left09_20130423155149.daq               1,339,437        True
Part10\Left10_20130423155149.daq               1,339,437        True
Part11\Left_11_20130429102407.daq                410,624       False
Part111\Left_11_20130430081052.daq             1,463,012       False
Part12\Left_12_20130429163745.daq              1,431,765       False
Part13\Left_13_20130429182923.daq              1,507,542       False
Part14\Left_14_20130430102504.daq              1,502,793       False
Part15\Left_15_20130430171947.daq              1,669,443       False
Part16\Left_16_20130501103917.daq              1,341,214       False
Part170\Left_17_20130501163745.daq             1,552,098       False
Part18\Left_18_20130502084422.daq                416,873       False
Part18\Left_18_reset_20130502090909.daq        1,128,833       False
Part19\Left_19_20130502153547.daq              1,526,510       False

Starting conversions (this may take awhile)...
    Part11\Left_11_20130429102407.daq          19.2 s
    Part111\Left_11_20130430081052.daq         416.4 s
    Part12\Left_12_20130429163745.daq          426.5 s
    Part13\Left_13_20130429182923.daq          424.2 s
    Part14\Left_14_20130430102504.daq          390.2 s
    Part15\Left_15_20130430171947.daq          467.8 s
    Part16\Left_16_20130501103917.daq          391.8 s
    Part170\Left_17_20130501163745.daq         325.6 s
    Part18\Left_18_20130502084422.daq          104.0 s
    Part18\Left_18_reset_20130502090909.daq    295.0 s
    Part19\Left_19_20130502153547.daq          307.6 s

Done.
Total elapsed time: 732.384001 s
Data converted: 13,624 MB
Data throughput: 18.601913 MB/s
"""

import os
import glob
import time
import multiprocessing

import undaqTools
    
# define a function to convert a daq to hdf5
def convert_daq(daq_file):
    """
    converts a daqfile to hdf5
    
    Parameters
    ----------
    daq_file : string
        relative path to daq_file
        
    Returns
    -------
    elapsed_time : float
        returns the time it took to complete converting daq or -1 if the
        conversion fails.
        
    """
    t0 = time.time()  
    
    # both multiprocessing and ipython cluster mask Exceptions
    # This way we can at least identify what file fails and the batch 
    # processing continues
    # 
    # Discovered this is needed the hard way. During an experimental trial
    # our MiniSim ran out of harddrive space and the resulting Daq failed to
    # load.
    try:
        daq = undaqTools.Daq()
        daq.read(daq_file)
        daq.write_hd5(daq_file.replace('.daq', '.hdf5'))
        del daq
        return time.time()-t0
    except:
        return -1
        
if __name__ == '__main__':  
    
    # data is on a local SSD drive. This is very important for performance.
    data_dir = 'C:\\LocalData\\Left Lane\\'
    
    # change the directory of the kernel
    print("Changing wd to '%s"%data_dir)    
    os.chdir(data_dir)
    
    # specifies whether to convert all the daqs or only the ones that haven't
    # been created. Unless you muck with the Daq or DynObj classes there it
    # should be fine to leave this False
    rebuild_all = False
    
    # The clients may be RAM limited. In this example the machine has 8 cores
    # but we are only using 6 to convert the daq files (with this particular 
    # dataset) (Machine has 32GB of memory and daqfiles are ~ 1.5 GB each, 
    # memory peaks at about 29 GB with no other applications.)
    numcpus = 6

    # parallel worker pool
    pool = multiprocessing.Pool(numcpus)
    
    # find all hdf5 files and all the daq files
    # we don't want to convert the daq files unless we have to
    #
    # data is organized such that every participant has his or her
    # own folder. Casting as tuples isn't strictly necessary. But this way
    # this ensures they are immutable.
    hd5_files = tuple(glob.glob('*/*.hdf5'))
    daq_files = tuple(glob.glob('*/*.daq'))
    
    # print a a summary table of what we have found
    print('\nGlob Summary')
    print('-'*(43+13+12))
    print('{:<43}{:>13}{:>12}'.format('daq', 'size (KB)', 'hdf5 exists'))
    print('-'*(43+13+12))
    for daq in daq_files:
        size = os.stat(daq).st_size/1024
        hd5_exists = str(daq.replace('daq','hdf5') in hd5_files)
        print('{:<43}{:>13,.0f}{:>12}'.format(daq, size, hd5_exists))

    # need to build list of daq_files to convert to pass to convert_daq
    if rebuild_all:
        daqs2convert = daq_files
    else:
        daqs2convert = \
            [daq for daq in daq_files if daq[:-3]+'hdf5' not in hd5_files]
    
    # ready to roll.
    print('\nConverting daqs (this may take awhile)...')    
    t0 = time.time() # start global time clock 

    # this launches the batch processing of the daq files
    times = pool.imap(convert_daq, daqs2convert)

    # this provides feedback as the sets of files complete. Using imap 
    # guarentees that the times are in the same order as daqs2convert but
    # delays receiving feedback
    for i, elapsed_time in enumerate(times):
        print('    {:<43}{:.1f} s'.format(daqs2convert[i], elapsed_time))
        
    elapsed_time = time.time() - t0 + 1e-6 # so throughput calc doesn't bomb
                                           # when daq2convert is empty

    # close multiprocessing pool
    pool.close()
    pool.join() 
    
    # calculate the amount of data that was converted in MB
    total_mb = sum(os.stat(daq).st_size/(1024*1024.) for daq in daqs2convert)
    
    # provide some feedback to the user
    print('\nDone.')
    print('Total elapsed time: %f s'%(elapsed_time))
    print('Data converted: {:,.0f} MB'.format(total_mb))
    print('Data throughput: %f MB/s'%(total_mb/elapsed_time))