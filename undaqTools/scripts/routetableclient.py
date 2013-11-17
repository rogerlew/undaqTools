from __future__ import print_function

# Copyright 2013 University of Idaho
#
# Author: Roger Lew (rogerlew@gmail.com)
# Date: 11/17/2013

"""
Echo Client to test NADS routeTable functionality
"""

import socket
import sys

from undaqTools.routetable import RouteTable

if __name__ == "__main__":
    try:
        rt_fname = sys.argv[1]
        routeid = int(sys.argv[2])
    except:
        print('Expecting routetable file name '
              'and route id as command line args')
        sys.exit()
        
    rt = RouteTable(rt_fname)

    # route is a routetable.Route object
    route = rt.routes[routeid]

    # variables is a list of the names/expressions from the devices
    # section in the order they are received as speicifed by the device
    # id order for routeid
    variables = [rt.devices[devid].value for devid in route.devices]

    # open socket to receive data
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    sock.bind((route.ipaddress, route.inport))

    print('Listening for route {route.id} on '
          '{route.ipaddress}:{route.inport}'.format(route=route))

    while 1:
        data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes

        # Route.unpack returns a list of values that coorespond to variables
        print(dict(zip(variables, route.unpack(data))))
