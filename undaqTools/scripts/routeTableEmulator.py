from __future__ import print_function

# Copyright 2013 University of Idaho
#
# Author: Roger Lew (rogerlew@gmail.com)
# Date: 11/17/2013

import socket
import struct
import sys
import time

from warnings import warn

import numpy as np

from undaqTools import Daq
from undaqTools.routetable import RouteTable

if __name__ == "__main__":
    try:
        rt_fname = sys.argv[1]
        daq_fname = sys.argv[2]
    except:
        print('Expecting routetable file name '
              'and route id as command line args')
        sys.exit()

    # specify broadcast rate in Hz
    try:
        broadcast_rate = int(sys.argv[3])
    except:
        broadcast_rate = 60

    # open datafile to broadcast
    daq = Daq()
    daq.read(daq_fname)
    numframes = len(daq.frame.frame)

    # read the routetable
    rt = RouteTable()
    rt.read(rt_fname)

    # prebuild the device arrays
    vecs = {}
    for route in rt.routes.values():
        for devid in route.devices:
            device = rt.devices[devid]

            if device.id in vecs:
                continue
            
            if device.name == 'n':
                if device.value == 'FrameNum':
                    vecs[device.id] = np.array(daq.frame.frame, ndmin=2)
                else:
                    vecs[device.id] = np.array(daq[device.value])
            else:
                eval_str = device.value
                for var in rt.vars:
                    eval_str = eval_str.replace(var, 'np.array(daq["%s"])'%var)

                try:
                    vecs[device.id] = eval(eval_str)
                except:
                    vecs[device.id] = np.empty((1,numframes))
                    vecs[device.id][:] = np.NAN
                    warn('Failed to evaluate "%s"'%eval_str)


    # initialize socket instance
    sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP

    # send the data
    for i in xrange(numframes):
        for route in rt.routes.values():
            vals = [vecs[devid][0,i] for devid in route.devices]
            sock.sendto(route.pack(vals), (route.ipaddress, route.inport))

        time.sleep(1./broadcast_rate)
