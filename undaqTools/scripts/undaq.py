from __future__ import print_function

# Copyright (c) 2013, Roger Lew
# All rights reserved.

"""
Parallel batch process .daq files to .hdf5 or .mat

Example Usage
-------------
To convert all .daq files current directory to .hdf5 using 6 CPUs::
    
    data_directory $ undaq.py * -n 6
      
To convert all .daq files current directory to .mat using 6 CPUs::
    
    data_directory $ undaq.py * -n 6 -o mat

To convert all .daq files in subdirectories one level down::
    
    data_directory $ undaq.py */*
    
To convert all .daq files in subdirectories one level down using 6 CPUs and 
force rebuilding of existing hdf5 files::
    
    data_directory $ undaq.py */* -n 6 -r
"""

import argparse
import os
import glob
import time
import multiprocessing

import undaqTools
    
# define a function to convert a daq to hdf5
def convert_daq(tupledArgs):
    """
    converts a daq file to hdf5 or mat file
    
    arguments passed as tuple to make it work with multiprocessin pool
    
    Parameters
    ----------
    tupledArgs : tuple
        daq_file : string
            path to the daq_file
        ext : string
            output file extension {'mat', 'hdf5'}
        elemfile : string or None
            path to elemlist file
        
    Returns
    -------
    elapsed_time : float or -1
        returns the time it took to complete converting daq 
        or -1 if the conversion fails.
        
    """
    
    (daq_file, ext, elemfile) = tupledArgs
    t0 = time.time()  
    
    try:
        daq = undaqTools.Daq()        
        if elemfile is not None:
            daq.load_elemlist_fromfile(elemfile)
            
        if ext == 'mat':
            daq.read(daq_file, process_dynobjs=False)
            daq.write_mat(daq_file.replace('.daq', '.mat'))
        else:
            daq.read(daq_file) 
            daq.write_hd5(daq_file.replace('.daq', '.hdf5'))
            
        del daq
        return time.time()-t0
    except:
        return -1
        
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str,   
                        help='Path for glob             ("*")')
    parser.add_argument('-n', '--numcpu',   type=int, 
                        help='Number of cpus in pool    (1)')
    parser.add_argument('-o', '--outtype',   
                        help='Output type               ([hd5], mat)')
    parser.add_argument('-e', '--elemfile', 
                        help='path to elemlist file     ("")')
    parser.add_argument('-r', '--rebuild',  
                        help='Overwrite existing files', action='store_true')    
    args = parser.parse_args()

    path = args.path
    numcpu = (args.numcpu, 1)[args.numcpu is None]
    ext = (args.outtype, 'hdf5')[args.outtype is None]
    ext = ext.strip().replace('.','').replace('hd5','hdf5')
    elemfile = args.elemfile
    rebuild = args.rebuild

    # parallel worker pool
    pool = multiprocessing.Pool(numcpu)
    
    # find all output files and all the daq files
    # we don't want to convert the daq files unless we have to
    #
    # data is organized such that every participant has his or her
    # own folder. Casting as tuples isn't strictly necessary. But this way
    # this ensures they are immutable.
    out_files = tuple(glob.glob('%s.%s'%(path, ext)))
    daq_files = tuple(glob.glob('%s.daq'%(path)))
    
    # print a a summary table of what we have found
    print('\nGlob Summary')
    print('-'*(43+13+12))
    print('{:<43}{:>13}{:>12}'.format('daq', 'size (KB)', '%s exists'%ext))
    print('-'*(43+13+12))
    for daq in daq_files:
        size = os.stat(daq).st_size/1024
        hd5_exists = str(daq.replace('daq', ext) in out_files)
        print('{:<43}{:>13,.0f}{:>12}'.format(daq, size, hd5_exists))    
    print('-'*(43+13+12))

    # need to build list of daq_files to convert to pass to convert_daq
    if rebuild:
        daqs2convert = [(daq, ext, elemfile) for daq in daq_files]
    else:
        daqs2convert = \
            [(daq, ext, elemfile) for daq in daq_files \
             if daq[:-3]+ext not in out_files]
    
    # ready to roll.
    print('\n\nConverting daqs (this may take awhile)...')    
    t0 = time.time() # start global time clock 

    # this launches the batch processing of the daq files
    times = pool.imap(convert_daq, daqs2convert)

    # this provides feedback as the sets of files complete. Using imap 
    # guarentees that the times are in the same order as daqs2convert but
    # delays receiving feedback
    for i, elapsed_time in enumerate(times):
        last = ('(%.1f s)'%elapsed_time, 'Failed')[elapsed_time == -1]
        print('  %s -> .%s %s'%(daqs2convert[i][0], ext, last))
              
    elapsed_time = time.time() - t0 + 1e-6 # so throughput calc doesn't bomb
                                           # when daq2convert is empty
                                           
    # close multiprocessing pool
    pool.close()
    pool.join() 
    
    # calculate the amount of data that was converted in MB
    tot_mb = sum(os.stat(daq[0]).st_size/(1024*1024.) for daq in daqs2convert)
    
    # provide some feedback to the user
    print('\nDone.\n')
    print('-'*(43+13+12))
    print('Conversion Summary')
    print('-'*(43+13+12))
    print('Total elapsed time: %.1f s'%(elapsed_time))
    print('Data converted: {:,.3f} MB'.format(tot_mb))
    print('Data throughput: %.1f MB/s'%(tot_mb/elapsed_time))
    print('-'*(43+13+12))