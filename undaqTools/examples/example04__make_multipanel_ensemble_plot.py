from __future__ import print_function

# Copyright (c) 2013, Roger Lew
# All rights reserved.

"""
Example multiple subplot ensemble figure of equidistantly interpolated speed.

In this example each subplot represents the level of independent conditions.
"""

from collections import OrderedDict
import os
import glob
import time

import numpy as np
from scipy import stats

from matplotlib import rcParams
rcParams['font.family'] = 'serif'
import matplotlib.pyplot as plt

from undaqTools import Daq, fslice

if __name__ == '__main__':
    
    # data is on a local SSD drive. This is very important for performance.
    data_dir = 'C:\\LocalData\\Left Lane\\'
    
    # change the directory of the kernel
    print("Changing wd to '%s'"%data_dir)    
    os.chdir(data_dir)

    print('\nStep 1. Find speeds interpolated by distance...')
    t0 = time.time()
    hd5_files = tuple(glob.glob('*/*.hdf5'))

    # define an linearly spaced distance vector to interpolate to
    veh_dist_ip = np.arange(0, 6604, 8)

    # goal of step 1 is to fill this list of lists structure
    interp_spds_by_scenario = [[] for i in xrange(10)]

    for hd5_file in hd5_files:
        print("  interpolating '%s'..."%hd5_file)
        
        # load hd5
        daq = Daq()
        daq.read_hd5(hd5_file)

        # for each trial...
        for i in xrange(10):
            
            if not ( i*10+1 in daq.etc['epochs'] and \
                     i*10+3 in daq.etc['epochs']):

                # encountered partial trial
                continue
            
            scenario = daq.etc['scen_order'][i]
            
            # unpack the start frame of the 1-to-2 lane addition transition
            # and the stop frame of the 2-to-1 lane reduction transition
            f0 = daq.etc['epochs'][i*10+1].start
            fend = daq.etc['epochs'][i*10+3].stop

            print("    on scenario %i [f%i:f%i]..."%(scenario, f0, fend))
            
            # next we need to linearly interpolate speed by distance
            veh_dist = daq['VDS_Veh_Dist'][0, fslice(f0, fend)].flatten()
            veh_dist -= veh_dist[0]
            
            veh_spd = daq['VDS_Veh_Speed'][0, fslice(f0, fend)].flatten()
            veh_spd_ip = np.interp(veh_dist_ip, veh_dist, veh_spd)

            # store interpolated speed so we can plot it
            interp_spds_by_scenario[scenario].append(veh_spd_ip)

    print('\nStep 2. Plot speeds...')

    # names of scenarios
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

    # intialize plot
    plt.figure(figsize=(9,14))
    plt.subplots_adjust(left=.05, right=.95,
                        bottom=.05, top=.95,
                        hspace=.27)
    xticks = np.linspace(0,5280*1.25,11)
    yticks = np.linspace(30,100,8)

    for scenario in xrange(10):
        print("  plotting scenario '%s'..."%scenario_names[scenario])
        plt.subplot(10 ,1, scenario+1)

        # figure out ensemble mean and confidence interval for scenario
        means = np.mean(interp_spds_by_scenario[scenario], 0)
        ci = stats.sem(interp_spds_by_scenario[scenario], 0)*1.96

        ci_upper = np.add(means, ci)
        ci_lower = np.subtract(means, ci)

        # plot ci fill first. The z-order makes it look better if this
        # is done first
        plt.fill(np.concatenate((veh_dist_ip, veh_dist_ip[::-1])),
                   np.concatenate((ci_upper, ci_lower[::-1])),
                   linewidth=0, facecolor='r', alpha=.4)
        
        plt.plot(veh_dist_ip, means, color='r')
    
        # plot individual trends
        for veh_spd_ip in interp_spds_by_scenario[scenario]:
            plt.plot(veh_dist_ip, veh_spd_ip, color='b', alpha=.4)

        # make things pretty
        plt.xlim([xticks[0], xticks[-1]])
        if scenario < 9:
            plt.xticks(xticks, ['' for t in xticks])
        else:
            plt.xticks(xticks)
            
        plt.ylim([yticks[0], yticks[-1]])
        plt.yticks(yticks)
        plt.grid()
        plt.axhline(65, color='k', ls='-')

        # put title on subplot
        plt.title(scenario_names[scenario])

    # save figure
    plt.savefig('ensemble_spd_plot.png', dpi=300)
    plt.close('all')
            
    print('\nDone.\n\nMaking ensemble plot took %.1f s'%(time.time()-t0))        
