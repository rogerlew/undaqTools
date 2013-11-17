from __future__ import print_function

# Copyright 2013 University of Idaho
#
# Author: Roger Lew (rogerlew@gmail.com)
# Date: 11/17/2013

import itertools
import struct

from collections import OrderedDict, namedtuple
from string import ascii_letters
from warnings import warn

_Var = namedtuple('Var', ['name', 'type', 'size'])

class Var(_Var):
    """
    Each Var object represents a line in the variable section of the RouteTable.txt

    Attributes
    ----------
    name <string>
        the name of the variable
        
    type <string>
        the datatype that the device should be output in

    size <int>
        the array size of the variable???
    """
    pass

_Device = namedtuple('Device', ['id', 'type', 'size', 'name', 'value'])

class Device(_Device):
    """
    Each Device object represents a line in the device section of the RouteTable.txt

    Attributes
    ----------
    id <int>
        the device id

    type <string>
        the datatype that the device should be output in

    size <int>
        the array size of the variable???

    name <string>
        n - value is a cell in the daq file e.g. "VDS_Veh_Speed"
        e - value is an mathematical expression e.g. "VDS_Veh_Speed + 0"

    value <string>
        the name or expression. Should contain variables that are defined in the
        variable section
    """
    pass

_Input = namedtuple('Input', ['id', 'name', 'offset', 'size'])

class Input(_Input):
    """
    Each Input object represents a line in the input section of the RouteTable.txt

    Attributes
    ----------
    id <int>
        the input id should be unique from device ids

    name <string>
        cell in database to write to

    offset <int>
        number of bytes to skip

    size <int>
        number of bytes
    """
    pass
    
_Route = namedtuple('Route', ['id', 'ipaddress', 'inport', 'outport',
                              'packed', 'devices', 'inputs', 'fmt',
                              'pack', 'unpack', 'packinput'])

class Route(_Route):
    """
    Each Route object represents a line in the route section of the RouteTable.txt

    Attributes
    ----------
    routeid <int>
        required id
        
    ipaddress <string>
        ipadress to send data to
        
    inport <int>
        the miniSim sends data to this port
        
    outport <int>
        the miniSim recieves data at this port
        
    packed <int>
        specifies whether data should be sent in packed data format
        should be 1,other format isn't fully tested according to David
        Heitbrink

    devices <list>
        list of device ids, device ids are ints from device section

    inputs <list>
        list of input ids, input ids are ints from input section
        
    fmt <string>
        format string for pack and unpack

    pack(vals) <lambda function>
        function to pack list of values to byte string

    unpack(data) <lambda function>
        function to unpack byte string to list of values
        
    packinput(fmt, vals) <lambda function>
        function to pack list of values to byte string
        fmt string must be supplied because the data types for the input cells
        aren't specified in the route table. They should match the types in the
        cec file.
    """
    pass

class RouteTable:
    """
    Parses and represents the information in NADS MiniSim RouteTable

    Attributes
    ----------
    fname <None or string>
        None if RouteTable has not been read, otherwise filename of RouteTable
    vars <dict>
        keys are the variable names
        values are Var namedtuples
        
    devices <dict>
        keys are the device ids
        alues are Device namedtuples
        
    routes <dict>
        keys are the route ids
        values are Route namedtuples
    """
    def __init__(self, fname=None):
        self.vars = OrderedDict()
        self.devices = OrderedDict()
        self.inputs = OrderedDict()
        self.routes = OrderedDict()
        self.fname = None
        
        if fname is not None:
            self.read(fname)

    def read(self, fname):
        section = None
        
        with open(fname, 'rb') as f:
            for i, line in enumerate(f.readlines()):
                line = line.strip()
                linelower = line.lower()
                
                if linelower[:3] == 'rem':
                    continue
                elif linelower in ['var', 'device', 'input', 'route']:
                    section = linelower
                elif line == 'end':
                    section = None
                elif section is not None:
                    L = line.split()
                    if section == 'var':
                        self._add_var(L)
                    elif section == 'device':
                        self._add_device(L)
                    elif section == 'input':
                        self._add_input(L)
                    elif section == 'route':
                        self._add_route(L)

        # double check that cells in devices are specified as vars
        err_msg = "Var name = %s is not specified as a var"
        for device in self.devices.values():
            for cell in device.value.split():
                if cell[0] not in ascii_letters:
                    continue
                
                if cell not in self.vars:
                    raise Exception(err_msg%cell)

        # double check that device ids in routes are specified as devices
        err_msg = "Device ID = %i is not specified as a device"
        for route in self.routes.values():
            for devid in route.devices:
                if devid not in self.devices:
                    raise Exception(err_msg%devid)
                
        # double check that inputs ids in routes are specified as inputs
        err_msg = "Input ID = %i is not specified as an input"
        for route in self.routes.values():
            for inputid in route.inputs:
                if inputid not in self.inputs:
                    raise Exception(err_msg%inputid)
                
        self.fname = fname

    def _add_var(self, L):
        """
        returns Var namedtuple from list of attributes
        L = [name, type, size]
        """
        self.vars[L[0]] = Var(L[0], L[1], int(L[2]))

    def _add_device(self, L):
        """
        returns Device namedtuple from list of attributes
        L = [id, type, size, name, value]
        """
        _id = int(L[0])
        
        if _id in self.devices:
            raise Exception('%i is already defined as a device'%_id)
        
        if _id in self.inputs:
            raise Exception('%i is already defined as a input'%_id)
        
        self.devices[_id] = Device(_id, L[1], int(L[2]),
                                    L[3], ' '.join(L[4:])[1:-1])

    def _add_input(self, L):
        """
        returns Device namedtuple from list of attributes
        L = [id, name, offset, size]
        """
        _id = int(L[0])
        
        if _id in self.devices:
            raise Exception('%i is already defined as a device'%_id)
        
        if _id in self.inputs:
            raise Exception('%i is already defined as an input'%_id)
        
        self.inputs[_id] = Input(_id, L[1], int(L[2]), int(L[3]))
        
    def _add_route(self, L):
        """
        returns Route namedtuple from list of attributes
        L = [id, ipaddress, inport, outport, packed, devices]
        """
        _id = int(L[0])

        if _id in self.routes:
            Exception('%i is already defined as a route'%_id)
        
        s = ' '.join(L[5:]).split('i')
        
        # this works even if s[0] is an empty string
        devices = [int(v) for v in s[0].split()]
        
        if len(s) > 1:
            inputs = [int(v) for v in s[1].split()]
        else:
            inputs = []

        _fmt = ''.join([self.devices[devid].type for devid in devices])

        pack = lambda vals : struct.pack(_fmt, *vals)
        unpack = lambda data : struct.unpack(_fmt, data)
        offs = [self.inputs[i].offset for i in inputs]
        packinput = lambda fmt, vals : \
            ''.join(['\x00'*o + struct.pack(f,v)
                     for f,v,o in izip(fmt, vals, offs)])

        self.routes[_id] = Route(_id, L[1], int(L[2]),
                                 int(L[3]), int(L[4]),
                                 devices, inputs, _fmt,
                                 pack, unpack, packinput)
                                       
    def __str__(self):
        s = [self.fname, '\n\nvar\n']

        for v in self.vars.values():
            s.append('    {v.name:32} {v.type} {v.size}\n'.format(v=v))
            
        s.append('end\n\ndevice\n')
        
        for v in self.devices.values():
            s.append('    {v.id:<5}{v.type}  {v.size}  '
                     '{v.name}  "{v.value}"\n'.format(v=v))
            
        s.append('end\n\ninput\n')

        for v in self.inputs.values():
            s.append('    {v.id:<5}{v.name:<32} '
                     '{v.offset} {v.size}\n'.format(v=v))
        
        s.append('end\n\nroute\n')

        for v in self.routes.values():
            s.append('    {v.id:<5}{v.ipaddress}  {v.inport}  '
                     '{v.outport}  {v.packed} '.format(v=v))
            s.append(','.join([str(k) for k in v.devices]))
            if len(v.inputs):
                s.append(' i ')
            s.append(','.join([str(k) for k in v.inputs]))
            s.append('  %s\n'%v.fmt)
            
        s.append('\nend\n')
        
        return ''.join(s)

if __name__ == '__main__':
    
    rt = RouteTable('RouteTable.txt')
    print(rt)
