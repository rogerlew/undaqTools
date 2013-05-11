Example 02: stat, logstream, and Daq.etc
------------------------------------------
Demonstrates how to use the stat function, logstream.find_epoch function,
and Daq.etc dict of undaqTools

::

    import os
    import glob
    import time

    import numpy as np

    import undaqTools
    from   undaqTools import Daq
    from   undaqTools.logstream import find_epochs

    # in this particular example participants drove through ten passing zones. The
    # order of the passing zones was counterbalanced according to this latin square.
    # we want to attach this and other experiment relevant metadata to the hd5 files
    # so we don't have to keep looking it up.
    latin_square = \
        [[0, 1, 9, 2, 8, 3, 7, 4, 6, 5],
         [1, 2, 0, 3, 9, 4, 8, 5, 7, 6],
         [2, 3, 1, 4, 0, 5, 9, 6, 8, 7],
         [3, 4, 2, 5, 1, 6, 0, 7, 9, 8],
         [4, 5, 3, 6, 2, 7, 1, 8, 0, 9],
         [5, 6, 4, 7, 3, 8, 2, 9, 1, 0],
         [6, 7, 5, 8, 4, 9, 3, 0, 2, 1],
         [7, 8, 6, 9, 5, 0, 4, 1, 3, 2],
         [8, 9, 7, 0, 6, 1, 5, 2, 4, 3],
         [9, 0, 8, 1, 7, 2, 6, 3, 5, 4]]

    # through the 1-mile 2-lane sections of the passing zones the wind speeds were
    # manipulated using this ordering. Each was split into 1/10 mile sections
    # Each zone is represented as a row. The speeds are in mph.
    wind_speeds = \
        [[0, 50, -100, -50, 100, 100, -50, -100, 50, 0],
         [50, -50, 0, 100, -100, -100, 100, 0, -50, 50],
         [-50, 100, 50, -100, 0, 0, -100, 50, 100, -50],
         [100, -100, -50, 0, 50, 50, 0, -50, -100, 100],
         [-100, 0, 100, 50, -50, -50, 50, 100, 0, -100],
         [0, 50, -100, -50, 100, 100, -50, -100, 50, 0],
         [50, -50, 0, 100, -100, -100, 100, 0, -50, 50],
         [-50, 100, 50, -100, 0, 0, -100, 50, 100, -50],
         [100, -100, -50, 0, 50, 50, 0, -50, -100, 100],
         [-100, 0, 100, 50, -50, -50, 50, 100, 0, -100]]


    def attach_metadata(hd5_file):
        """
        The Daq files have an 'etc' dict attribute inteaded for users to
        store analysis relevant metadata. The etc dict can be exported to hdf5
        and reloaded from hdf5. We want to go through and build these dicts so
        that the information is at our fingertips when we need it.
        """
        
        global latin_square, wind_speeds

        t0 = time.time()

        tmp_file = hd5_file + '.tmp'

        # load hd5
        daq = Daq()
        daq.read_hd5(hd5_file)
        
        etc = {} # fill and pack in daq
        
        # find the real participant id (pid) from the file path
        etc['pid'] = int(hd5_file.split('\\')[0][4:])
        etc['scen_order'] = latin_square[(etc['pid']-1)%10]
        etc['wind_speeds'] = wind_speeds

        # now to find the epochs
        # epochs is a dictionary. The keys are the enumerated states and the
        # values are FrameSlice objects. The FrameSlice objects can be used
        # to slice the Elements in Daq instances.
        etc['epochs'] = find_epochs(daq['SCC_LogStreams'][0,:])

        daq.etc = etc # doing it this way ensures we know what is in there

        # write to temporary file.
        # once that completes, delete original hd5, and rename temporary file.
        # This protects you from yourself. If you get impatient and kill the
        # kernel there is way less risk of corrupting your hd5.
        daq.write_hd5(tmp_file)
        os.remove(hd5_file)
        os.rename(tmp_file, hd5_file)
        
        del daq

        return time.time() - t0

    if __name__ == '__main__':  
        
        # data is on a local SSD drive. This is very important for performance.
        data_dir = 'C:\\LocalData\\Left Lane\\'
        
        # change the directory of the kernel
        print("Changing wd to '%s'"%data_dir)    
        os.chdir(data_dir)

        # undaqTools.stat
        #
        # Here we are going to verify that the subject IDs on the directories
        # match the subject IDs that were specified in the MiniSim. This can be
        # accomplished in to ways. The first is to use undaqTools.stat to read
        # the .daq files directly. This method will return namedTuple with the
        # info information packed into the fields. This method is nice because
        # it works with the raw data files. If your files are already converted
        # you can just look at Daq.info.subject. In this case our files have
        # already been converted, but for example purposes...
        
        t0 = time.time()
        daq_files = tuple(glob.glob('*/*.daq'))
        matches = []

        print('\nfrom file   from Daq     Match')
        print('--------------------------------------')
        for daq_file in daq_files:
            # figure out subject ID from the filename path
            from_fname = daq_file.split('\\')[0]

            # get an undaqTools.Info instance for daq_file
            info = undaqTools.stat(daq_file)

            # do they match?
            matches.append(from_fname == info.subject)

            # some feedback
            print('{0:<11}'.format(from_fname),
                  '{0.subject}'.format(info).ljust(14,' '),
                  str(matches[-1]))

        if not all(matches):
            print('\nWarning: Not all subject names match!')

        print('\nstat-ing daqs took %.3f s'%(time.time()-t0))

        #
        # undaqTools.logstream.find_epochs
        #
        # The next thing we want to do is find the epochs or time segments of
        # interest from each drive. With this particular dataset participants
        # drove through ten 2-lane passing zones. The passing zones are enumerated
        # in the logstream and we want to identify the frames where they start
        # and end. We can do this using undaqTools.logstream.find_epochs
        
        print('\nBuilding etc dicts...')
        t0 = time.time()
        hd5_files = tuple(glob.glob('*/*.hdf5'))

        # this is so IO dependent that parallelizing
        # the code doesn't make it any faster
        for hd5_file in hd5_files:
            elapsed = attach_metadata(hd5_file)
            print("  processed '%s' in %.1f s"%(hd5_file, elapsed))
            
        print('\nDone.\n\nbuilding etc dicts took %.1f s'%(time.time()-t0))        

Example Output::

    Changing wd to 'C:\LocalData\Left Lane\'

    from file   from Daq     Match
    --------------------------------------
    Part01      Part01         True
    Part02      Part02         True
    Part03      Part03         True
    Part04      Part04         True
    Part05      Part05         True
    Part06      Part06         True
    Part07      Part07         True
    Part08      Part08         True
    Part08      Part08         True
    Part09      Part200        False
    Part10      Part200        False
    Part11      Part11         True
    Part111     Part111        True
    Part12      Part12         True
    Part13      Part13         True
    Part14      Part14         True
    Part15      Part15         True
    Part16      test           False
    Part170     Part177        False
    Part18      Part18         True
    Part18      Part18_reset   False
    Part19      Part19         True

    Warning: Not all subject names match!

    stat-ing daqs took 0.1 s

    Building etc dicts...
      processed Part01\Left_01_20130424102744.hdf5 in 7.0 s
      processed Part02\Left_02_20130425084730.hdf5 in 7.2 s
      processed Part03\Left_03_20130425102301.hdf5 in 6.7 s
      processed Part04\Left_04_20130425142804.hdf5 in 6.2 s
      processed Part05\Left_05_20130425161122.hdf5 in 7.6 s
      processed Part06\Left_06_20130426111502.hdf5 in 6.2 s
      processed Part07\Left_07_20130426143846.hdf5 in 6.8 s
      processed Part08\Left_08_20130426164114.hdf5 in 0.2 s
      processed Part08\Left_08_20130426164301.hdf5 in 6.8 s
      processed Part09\Left09_20130423155149.hdf5 in 6.2 s
      processed Part10\Left10_20130423155149.hdf5 in 6.2 s
      processed Part111\Left_11_20130430081052.hdf5 in 7.4 s
      processed Part12\Left_12_20130429163745.hdf5 in 7.2 s
      processed Part13\Left_13_20130429182923.hdf5 in 7.8 s
      processed Part14\Left_14_20130430102504.hdf5 in 7.3 s
      processed Part15\Left_15_20130430171947.hdf5 in 7.8 s
      processed Part16\Left_16_20130501103917.hdf5 in 12.5 s
      processed Part170\Left_17_20130501163745.hdf5 in 13.0 s
      processed Part18\Left_18_20130502084422.hdf5 in 4.4 s
      processed Part18\Left_18_reset_20130502090909.hdf5 in 9.8 s
      processed Part19\Left_19_20130502153547.hdf5 in 12.6 s

    Done.

    building etc dicts took 157.2 s