from __future__ import print_function

# Copyright (c) 2013, Roger Lew
# All rights reserved.

# undaq.py in the scripts folder is more fully featured version of this
# example. This code is a bit easier to follow though.
"""
Batch convert daq files to HDF5 in parallel using the multiprocessing module
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
    data_dir = './'
    
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

