from __future__ import print_function

# Copyright (c) 2013, Roger Lew
# All rights reserved.

import os
import glob
import time
from collections import OrderedDict
import operator
from operator import attrgetter

from matplotlib import rcParams
rcParams['font.family'] = 'serif'
import matplotlib.pyplot as plt

import numpy as np

import undaqTools
from undaqTools import Daq, logstream, frame_range

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
        
        daq = undaqTools.Daq()
        daq.read_hd5(hdf5_file)
        pid = daq.etc['pid']

        # figure out row number
        rnum = pids.index(pid)

        # find the relevant dynamic objects to plot
        same_lane_ados = [do for do in daq.dynobjs.values() if 'Ado' in do.name]
        same_lane_ados = sorted(same_lane_ados, key=operator.attrgetter('name'))

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

            # build new FrameSlice instance
            fslice = frame_range(f0, fend)

            # get axis handle
            ax1 = plt.subplot(8, 10, rnum*10 + scenario + 1)

            distance = daq['VDS_Veh_Dist'][0, fslice].flatten()
            distance -= distance[0]
            speed = daq['VDS_Veh_Speed'][0, fslice].flatten()
            
            ax1.plot(distance, speed, 'b')
            ax2 = ax1.twinx()
            
            # we need to figure out when the Ados enter the passing lane
            # and exit the passing lane. To do this we need to know where
            # the passing lane starts and ends
            pos0 = daq['VDS_Chassis_CG_Position'].state_at_frame(f0)
            posend = daq['VDS_Chassis_CG_Position'].state_at_frame(fend)

            # loop through and plot ados
            for j, do in enumerate(same_lane_ados):

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
                    distance = do.distance[0, imin0:iminend]
                    distance -= distance[0]
                    rel_distance = do.relative_distance[0, imin0:iminend]
                    ax2.plot(distance, rel_distance, color='g', alpha=0.4)

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
                ax1.set_xticklabels(['%i'%x for x in xticks], rotation='vertical')
            else:
                ax1.set_xticklabels(['' for x in xticks])

            if not scenario:
                ax1.text(660,35,'Participant: %03i =>'%pids[rnum], size='small')

    img_name = 'do_passing_behavior__PAGE%i.png'%page
    fig.savefig(img_name, dpi=300)
    plt.close()
                
if __name__ == '__main__':
     
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

    n = 8 # number of pids per page

    # data is on a local SSD drive. This is very important for performance.
    data_dir = 'C:\\LocalData\\Left Lane\\'
    
    # change the directory of the kernel
    print("Changing wd to '%s'"%data_dir)    
    os.chdir(data_dir)

    get_pid = lambda  fname : int(fname.split('\\')[0][4:])
    hdf5_files = glob.glob('*/*.hdf5')
    pids = sorted(list(set([get_pid(hf) for hf in hdf5_files])))

    for i in xrange(len(pids)/n + 1):
        mult_ado_by_pid_plot(pids[i*n:i*n+n], i+1)
        
    print('\nDone.\n\nMaking multipanel plot took %.1f s'%(time.time()-t0))   
