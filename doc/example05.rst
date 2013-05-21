Example 05: Ado headway distance visualization
----------------------------------------------
Example multiple subplot ensemble figure of equidistantly interpolated speed.
In this example each subplot represents the level of independent conditions.

**The Script**::

    from __future__ import print_function

    # Copyright (c) 2013, Roger Lew
    # All rights reserved.

    import os
    import glob
    from operator import attrgetter
    import time

    from matplotlib import rcParams
    rcParams['font.family'] = 'serif'
    import matplotlib.pyplot as plt

    import numpy as np

    from undaqTools import Daq, fslice, findex

    def mult_ado_by_pid_plot(pids, page):
        global hdf5_files, scenario_names, latin_square, get_pid

        # initialize plot
        fig = plt.figure(figsize=(11*1.75, 8.5*1.75))
        fig.subplots_adjust(left=.04, right=.96,
                            bottom=.05, top=.97,
                            wspace=.04, hspace=.04)

        # plot will have 2 axis. One is for Vehicle Speed, the other is
        # for relative distance of the DynObjs
        xticks = np.linspace(660,5280*1.25,10)
        xlim = [0, 5280*1.25]

        # speed in MPH
        yticks1 = np.linspace(35,75,5)
        ylim1 = [30,80]

        # relative distance in Feet
        yticks2 = np.linspace(-1500,1500,7)
        ylim2 = [-1750,1750]

        # loop through the hdf5_files that contain
        # data for the requested participants
        for hdf5_file in [hd for hd in hdf5_files if get_pid(hd) in pids]:
        
            print('analyzing "%s"'%hdf5_file)
            
            daq = Daq()
            daq.read_hd5(hdf5_file)
            pid = daq.etc['pid']

            # figure out row number
            rnum = pids.index(pid)

            # find the relevant dynamic objects to plot
            platoon = [do for do in daq.dynobjs.values() if 'Ado' in do.name]
            platoon = sorted(platoon, key=attrgetter('name'))

            # for each trial...
            for i in xrange(10):
                
                if not ( i*10+1 in daq.etc['epochs'] and \
                         i*10+3 in daq.etc['epochs']):

                    # encountered partial trial
                    continue
                    
                scenario = daq.etc['scen_order'][i]
                scenario_name = scenario_names[scenario]
                
                print('  PID: %03i, Passing zone: %i (%s)'%(pid, i, scenario_name))
                
                # unpack the start frame of the 1-to-2 lane addition transition
                # and the stop frame of the 2-to-1 lane reduction transition
                f0 = daq.etc['epochs'][i*10+1].start
                fend = daq.etc['epochs'][i*10+3].stop

                # get axis handle
                ax1 = plt.subplot(8, 10, rnum*10 + scenario + 1)

                distance = daq['VDS_Veh_Dist'][0, fslice(f0, fend)].flatten()
                distance -= distance[0]
                
                speed = daq['VDS_Veh_Speed'][0, fslice(f0, fend)].flatten()
                
                ax1.plot(distance, speed, 'b')
                ax2 = ax1.twinx()
                
                # we need to figure out when the Ados enter the passing lane
                # and exit the passing lane. To do this we need to know where
                # the passing lane starts and ends
                pos0 = daq['VDS_Chassis_CG_Position'][:,findex(f0)]
                posend = daq['VDS_Chassis_CG_Position'][:,findex(fend)]

                # loop through and plot ados
                for j, do in enumerate(platoon):

                    # each passing zone has its own set of Ados. This
                    # sorts out which are actually defined (should be 
                    # defined) for this trial.
                    if i*10 <= int(do.name[-2:]) < (i+1)*10:                    
                        # figure out when the ado enters the 
                        d0 = np.sum((do.pos - pos0)**2., axis=0)**.5
                        dend = np.sum((do.pos - posend)**2., axis=0)**.5
                        
                        # indexes relative to do arrays
                        imin0 = d0.argmin() 
                        iminend = dend.argmin()

                        # now we can plot the Ados relative distance to the
                        # vehicle as a function of distance over the passing
                        # lane
                        
                        # with this dataset the thrid vehicle in the platoon
                        # was systematically manipulate
                        if 'L' in do.name:
                            color = 'm'
                            alpha = 1.
                        elif 'S' in do.name:
                            color = 'g'
                            alpha = 1.
                        else:
                            color = 'g'
                            alpha = .4

                        if iminend-imin0 > 0:
                            distance = do.distance[0, imin0:iminend]
                            distance -= distance[0]
                            rel_distance = do.relative_distance[0, imin0:iminend]
                            ax2.plot(distance, rel_distance, color=color, alpha=alpha)
                        else:
                            print('    %s did not drive '
                                  'through passing zone'%do.name)


                # make things pretty
                ax1.set_ylim(ylim1)
                ax1.set_yticks(yticks1)
                if scenario:
                    ax1.set_yticklabels(['' for y in yticks1])
                else:
                    ax1.set_yticklabels(yticks1, color='b')
                
                ax2.axhline(0, color='k', linestyle=':')
                ax2.set_ylim(ylim2)
                ax2.set_yticks(yticks2)
                if scenario != 9:
                    ax2.set_yticklabels(['' for y in yticks2])
                else:
                    ax2.set_yticklabels(yticks2, color='g')
                    
                ax2.set_xlim(xlim)
                ax2.set_xticks(xticks)

                if rnum == 0:
                    ax1.set_title(scenario_names[scenario])
                    
                if rnum == len(pids)-1:
                    ax1.set_xticklabels(['%i'%x for x in xticks], 
                                        rotation='vertical')
                else:
                    ax1.set_xticklabels(['' for x in xticks])

                if not scenario:
                    ax1.text(660,35,'Participant: %03i =>'%pids[rnum], 
                             size='small')

        img_name = 'do_passing_behavior__PAGE%i.png'%page
        fig.savefig(img_name, dpi=300)
        plt.close()
                    
    if __name__ == '__main__':
        t0 = time.time()
        scenario_names = ['Baseline', 
                          'Advisory', 
                          'Reg', 
                          'Reg + Adv', 
                          'Chevrons', 
                          'Lines', 
                          'Narrowing', 
                          'Parallax', 
                          'Force Rh', 
                          'Lines w/ mid']

        n = 7 # number of pids per page

        # data is on a local SSD drive. This is very important for performance.
        data_dir = 'C:\\LocalData\\Left Lane\\'
        
        # change the directory of the kernel
        print("Changing wd to '%s'"%data_dir)    
        os.chdir(data_dir)

        get_pid = lambda  fname : int(fname.split('\\')[0][4:])
        hdf5_files = glob.glob('*/*.hdf5')
        pids = sorted(list(set([get_pid(hf) for hf in hdf5_files])))

        print(pids)

        for i in xrange(len(pids)/n+1):
            mult_ado_by_pid_plot(pids[i*n:i*n+n], i+1)
            
        print('\nDone.\n\nMaking multipanel plot took %.1f s'%(time.time()-t0))   



**The plots**

Download 
[:download:`hi-res <_static/do_passing_behavior__PAGE1.png>`]

.. image:: _static/do_passing_behavior__PAGE1.png 
    :width: 750px
    :align: center
    :alt: do_passing_behavior__PAGE1.png
 
Download 
[:download:`hi-res <_static/do_passing_behavior__PAGE2.png>`]

.. image:: _static/do_passing_behavior__PAGE2.png 
    :width: 750px
    :align: center
    :alt: do_passing_behavior__PAGE2.png
    
Download 
[:download:`hi-res <_static/do_passing_behavior__PAGE3.png>`]

.. image:: _static/do_passing_behavior__PAGE3.png 
    :width: 750px
    :align: center
    :alt: do_passing_behavior__PAGE3.png
    
**Example Output**::

    Changing wd to 'C:\LocalData\Left Lane\'
    analyzing "Part01\Left_01_20130424102744.hdf5"
      PID: 001, Passing zone: 0 (Baseline)
      PID: 001, Passing zone: 1 (Advisory)
      PID: 001, Passing zone: 2 (Lines w/ mid)
        Ado28 did not drive through passing zone
      PID: 001, Passing zone: 3 (Reg)
      PID: 001, Passing zone: 4 (Force Rh)
      PID: 001, Passing zone: 5 (Reg + Adv)
      PID: 001, Passing zone: 6 (Parallax)
      PID: 001, Passing zone: 7 (Chevrons)
      PID: 001, Passing zone: 8 (Narrowing)
      PID: 001, Passing zone: 9 (Lines)
    analyzing "Part02\Left_02_20130425084730.hdf5"
      PID: 002, Passing zone: 0 (Advisory)
      PID: 002, Passing zone: 1 (Reg)
      PID: 002, Passing zone: 2 (Baseline)
      PID: 002, Passing zone: 3 (Reg + Adv)
      PID: 002, Passing zone: 4 (Lines w/ mid)
      PID: 002, Passing zone: 5 (Chevrons)
      PID: 002, Passing zone: 6 (Force Rh)
      PID: 002, Passing zone: 7 (Lines)
      PID: 002, Passing zone: 8 (Parallax)
      PID: 002, Passing zone: 9 (Narrowing)
    analyzing "Part03\Left_03_20130425102301.hdf5"
      PID: 003, Passing zone: 0 (Reg)
      PID: 003, Passing zone: 1 (Reg + Adv)
      PID: 003, Passing zone: 2 (Advisory)
      PID: 003, Passing zone: 3 (Chevrons)
      PID: 003, Passing zone: 4 (Baseline)
      PID: 003, Passing zone: 5 (Lines)
      PID: 003, Passing zone: 6 (Lines w/ mid)
      PID: 003, Passing zone: 7 (Narrowing)
      PID: 003, Passing zone: 8 (Force Rh)
      PID: 003, Passing zone: 9 (Parallax)
    analyzing "Part04\Left_04_20130425142804.hdf5"
      PID: 004, Passing zone: 0 (Reg + Adv)
      PID: 004, Passing zone: 1 (Chevrons)
      PID: 004, Passing zone: 2 (Reg)
      PID: 004, Passing zone: 3 (Lines)
      PID: 004, Passing zone: 4 (Advisory)
      PID: 004, Passing zone: 5 (Narrowing)
      PID: 004, Passing zone: 6 (Baseline)
      PID: 004, Passing zone: 7 (Parallax)
      PID: 004, Passing zone: 8 (Lines w/ mid)
      PID: 004, Passing zone: 9 (Force Rh)
    analyzing "Part05\Left_05_20130425161122.hdf5"
      PID: 005, Passing zone: 0 (Chevrons)
      PID: 005, Passing zone: 1 (Lines)
      PID: 005, Passing zone: 2 (Reg + Adv)
      PID: 005, Passing zone: 3 (Narrowing)
      PID: 005, Passing zone: 4 (Reg)
      PID: 005, Passing zone: 5 (Parallax)
      PID: 005, Passing zone: 6 (Advisory)
      PID: 005, Passing zone: 7 (Force Rh)
      PID: 005, Passing zone: 8 (Baseline)
      PID: 005, Passing zone: 9 (Lines w/ mid)
    analyzing "Part06\Left_06_20130426111502.hdf5"
      PID: 006, Passing zone: 0 (Lines)
      PID: 006, Passing zone: 1 (Narrowing)
      PID: 006, Passing zone: 2 (Chevrons)
      PID: 006, Passing zone: 3 (Parallax)
      PID: 006, Passing zone: 4 (Reg + Adv)
      PID: 006, Passing zone: 5 (Force Rh)
      PID: 006, Passing zone: 6 (Reg)
      PID: 006, Passing zone: 7 (Lines w/ mid)
      PID: 006, Passing zone: 8 (Advisory)
      PID: 006, Passing zone: 9 (Baseline)
    analyzing "Part07\Left_07_20130426143846.hdf5"
      PID: 007, Passing zone: 0 (Narrowing)
      PID: 007, Passing zone: 1 (Parallax)
      PID: 007, Passing zone: 2 (Lines)
      PID: 007, Passing zone: 3 (Force Rh)
      PID: 007, Passing zone: 4 (Chevrons)
      PID: 007, Passing zone: 5 (Lines w/ mid)
      PID: 007, Passing zone: 6 (Reg + Adv)
      PID: 007, Passing zone: 7 (Baseline)
      PID: 007, Passing zone: 8 (Reg)
        Ado82 did not drive through passing zone
      PID: 007, Passing zone: 9 (Advisory)
    analyzing "Part08\Left_08_20130426164114.hdf5"
    analyzing "Part08\Left_08_20130426164301.hdf5"
      PID: 008, Passing zone: 0 (Parallax)
      PID: 008, Passing zone: 1 (Force Rh)
      PID: 008, Passing zone: 2 (Narrowing)
      PID: 008, Passing zone: 3 (Lines w/ mid)
      PID: 008, Passing zone: 4 (Lines)
      PID: 008, Passing zone: 5 (Baseline)
      PID: 008, Passing zone: 6 (Chevrons)
      PID: 008, Passing zone: 7 (Advisory)
      PID: 008, Passing zone: 8 (Reg + Adv)
      PID: 008, Passing zone: 9 (Reg)
    analyzing "Part09\Left09_20130423155149.hdf5"
      PID: 009, Passing zone: 0 (Force Rh)
      PID: 009, Passing zone: 1 (Lines w/ mid)
      PID: 009, Passing zone: 2 (Parallax)
      PID: 009, Passing zone: 3 (Baseline)
      PID: 009, Passing zone: 4 (Narrowing)
      PID: 009, Passing zone: 5 (Advisory)
      PID: 009, Passing zone: 6 (Lines)
      PID: 009, Passing zone: 7 (Reg)
      PID: 009, Passing zone: 8 (Chevrons)
      PID: 009, Passing zone: 9 (Reg + Adv)
    analyzing "Part10\Left10_20130423155149.hdf5"
      PID: 010, Passing zone: 0 (Lines w/ mid)
      PID: 010, Passing zone: 1 (Baseline)
      PID: 010, Passing zone: 2 (Force Rh)
      PID: 010, Passing zone: 3 (Advisory)
      PID: 010, Passing zone: 4 (Parallax)
      PID: 010, Passing zone: 5 (Reg)
      PID: 010, Passing zone: 6 (Narrowing)
      PID: 010, Passing zone: 7 (Reg + Adv)
      PID: 010, Passing zone: 8 (Lines)
      PID: 010, Passing zone: 9 (Chevrons)
    analyzing "Part12\Left_12_20130429163745.hdf5"
      PID: 012, Passing zone: 0 (Advisory)
      PID: 012, Passing zone: 1 (Reg)
      PID: 012, Passing zone: 2 (Baseline)
      PID: 012, Passing zone: 3 (Reg + Adv)
      PID: 012, Passing zone: 4 (Lines w/ mid)
      PID: 012, Passing zone: 5 (Chevrons)
      PID: 012, Passing zone: 6 (Force Rh)
      PID: 012, Passing zone: 7 (Lines)
      PID: 012, Passing zone: 8 (Parallax)
      PID: 012, Passing zone: 9 (Narrowing)
    analyzing "Part13\Left_13_20130429182923.hdf5"
      PID: 013, Passing zone: 0 (Reg)
      PID: 013, Passing zone: 1 (Reg + Adv)
      PID: 013, Passing zone: 2 (Advisory)
      PID: 013, Passing zone: 3 (Chevrons)
      PID: 013, Passing zone: 4 (Baseline)
      PID: 013, Passing zone: 5 (Lines)
      PID: 013, Passing zone: 6 (Lines w/ mid)
      PID: 013, Passing zone: 7 (Narrowing)
      PID: 013, Passing zone: 8 (Force Rh)
      PID: 013, Passing zone: 9 (Parallax)
    analyzing "Part14\Left_14_20130430102504.hdf5"
      PID: 014, Passing zone: 0 (Reg + Adv)
      PID: 014, Passing zone: 1 (Chevrons)
      PID: 014, Passing zone: 2 (Reg)
      PID: 014, Passing zone: 3 (Lines)
      PID: 014, Passing zone: 4 (Advisory)
      PID: 014, Passing zone: 5 (Narrowing)
      PID: 014, Passing zone: 6 (Baseline)
      PID: 014, Passing zone: 7 (Parallax)
      PID: 014, Passing zone: 8 (Lines w/ mid)
      PID: 014, Passing zone: 9 (Force Rh)
    analyzing "Part15\Left_15_20130430171947.hdf5"
      PID: 015, Passing zone: 0 (Chevrons)
      PID: 015, Passing zone: 1 (Lines)
      PID: 015, Passing zone: 2 (Reg + Adv)
      PID: 015, Passing zone: 3 (Narrowing)
      PID: 015, Passing zone: 4 (Reg)
      PID: 015, Passing zone: 5 (Parallax)
      PID: 015, Passing zone: 6 (Advisory)
      PID: 015, Passing zone: 7 (Force Rh)
      PID: 015, Passing zone: 8 (Baseline)
      PID: 015, Passing zone: 9 (Lines w/ mid)
    analyzing "Part16\Left_16_20130501103917.hdf5"
      PID: 016, Passing zone: 0 (Lines)
      PID: 016, Passing zone: 1 (Narrowing)
      PID: 016, Passing zone: 2 (Chevrons)
      PID: 016, Passing zone: 3 (Parallax)
      PID: 016, Passing zone: 4 (Reg + Adv)
      PID: 016, Passing zone: 5 (Force Rh)
      PID: 016, Passing zone: 6 (Reg)
      PID: 016, Passing zone: 7 (Lines w/ mid)
      PID: 016, Passing zone: 8 (Advisory)
      PID: 016, Passing zone: 9 (Baseline)
    analyzing "Part18\Left_18_20130502084422.hdf5"
      PID: 018, Passing zone: 0 (Parallax)
      PID: 018, Passing zone: 1 (Force Rh)
      PID: 018, Passing zone: 2 (Narrowing)
    analyzing "Part18\Left_18_reset_20130502090909.hdf5"
      PID: 018, Passing zone: 3 (Lines w/ mid)
      PID: 018, Passing zone: 4 (Lines)
      PID: 018, Passing zone: 5 (Baseline)
      PID: 018, Passing zone: 6 (Chevrons)
      PID: 018, Passing zone: 7 (Advisory)
      PID: 018, Passing zone: 8 (Reg + Adv)
      PID: 018, Passing zone: 9 (Reg)
    analyzing "Part111\Left_11_20130430081052.hdf5"
      PID: 111, Passing zone: 0 (Baseline)
      PID: 111, Passing zone: 1 (Advisory)
      PID: 111, Passing zone: 2 (Lines w/ mid)
      PID: 111, Passing zone: 3 (Reg)
      PID: 111, Passing zone: 4 (Force Rh)
      PID: 111, Passing zone: 5 (Reg + Adv)
      PID: 111, Passing zone: 6 (Parallax)
      PID: 111, Passing zone: 7 (Chevrons)
      PID: 111, Passing zone: 8 (Narrowing)
      PID: 111, Passing zone: 9 (Lines)
    analyzing "Part170\Left_17_20130501163745.hdf5"
      PID: 170, Passing zone: 0 (Lines w/ mid)
      PID: 170, Passing zone: 1 (Baseline)
      PID: 170, Passing zone: 2 (Force Rh)
      PID: 170, Passing zone: 3 (Advisory)
      PID: 170, Passing zone: 4 (Parallax)
      PID: 170, Passing zone: 5 (Reg)
      PID: 170, Passing zone: 6 (Narrowing)
      PID: 170, Passing zone: 7 (Reg + Adv)
      PID: 170, Passing zone: 8 (Lines)
      PID: 170, Passing zone: 9 (Chevrons)
    analyzing "Part19\Left_19_20130502153547.hdf5"
      PID: 019, Passing zone: 0 (Force Rh)
      PID: 019, Passing zone: 1 (Lines w/ mid)
      PID: 019, Passing zone: 2 (Parallax)
      PID: 019, Passing zone: 3 (Baseline)
      PID: 019, Passing zone: 4 (Narrowing)
      PID: 019, Passing zone: 5 (Advisory)
      PID: 019, Passing zone: 6 (Lines)
      PID: 019, Passing zone: 7 (Reg)
      PID: 019, Passing zone: 8 (Chevrons)
      PID: 019, Passing zone: 9 (Reg + Adv)
    analyzing "Part200\Left_20_20130509094509.hdf5"
      PID: 200, Passing zone: 0 (Lines w/ mid)
      PID: 200, Passing zone: 1 (Baseline)
      PID: 200, Passing zone: 2 (Force Rh)
      PID: 200, Passing zone: 3 (Advisory)
      PID: 200, Passing zone: 4 (Parallax)
      PID: 200, Passing zone: 5 (Reg)
      PID: 200, Passing zone: 6 (Narrowing)
      PID: 200, Passing zone: 7 (Reg + Adv)
      PID: 200, Passing zone: 8 (Lines)
      PID: 200, Passing zone: 9 (Chevrons)

    Done.

    Making multipanel plot took 205.4 s
    
