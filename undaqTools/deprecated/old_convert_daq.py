from __future__ import with_statement

# (C) Copyright 2010 by National Advanced Driving Simulator and
# Simulation Center, the University of Iowa and The University of Iowa.
# All rights reserved.
#
# Version: 3.10
# Authors: Created by Chris Schwarz and others at the NADS
#


import struct
import copy
import numpy as np
from scipy import io as sio
import os

def daq_meta(fid):
    daq={}
    daq['magic'] = fid.read(4).encode('hex')
    daq['title'] = fid.read(120).split('\x00')[0]
    daq['date'] = fid.read(27).split('\x00')[0]
    daq['subject'] = fid.read(128).split('\x00')[0]
    daq['run'] = fid.read(128).split('\x00')[0]
    daq['runinst'] = fid.read(129).split('\x00')[0]
    daq['numentries'] = struct.unpack('i',fid.read(4))[0]
    daq['frequency'] = struct.unpack('i',fid.read(4))[0]
    return daq

def init_header():
    header={}
    header['id']=[]
    header['numvalues']=[]
    header['name']=[]
    header['units']=[]
    header['rate']=[]
    header['type']=[]
    header['varrateflag']=[]
    header['bytes']=[]
    return header
    
def init_frame():
    frame={}
    frame['code']=[]
    frame['frame']=[]
    frame['count']=[]
    return frame
    
def init_data(header, elemlist = []):
    data={}
    if elemlist:
        for name in header['name']:
            if name in elemlist:
                data[name]=[]
    else:
        for name in header['name']:
            data[name]=[]
    return data
    
def append_header(fid, header):
    if not header['id']:
        header['id']=[0]
    else:
        header['id'].append(header['id'][-1]+1)
    numvalues=struct.unpack('i',fid.read(4))[0]
    header['numvalues'].append(numvalues)
    header['name'].append(fid.read(36).split('\x00')[0])
    header['units'].append(fid.read(16).split('\x00')[0])
    rate=struct.unpack('h',fid.read(2))[0]
    if rate == 65535:
        rate=-1
    header['rate'].append(rate)
    dummy=fid.read(2)
    type=chr(struct.unpack('i', fid.read(4))[0])
    header['type'].append(type)
    header['varrateflag'].append(struct.unpack('B', fid.read(1))[0])
    post1=fid.read(3)
    
def append_data(fid, header, frame, data, elemlist = []):
    id = struct.unpack('i', fid.read(4))[0]
    if header['varrateflag'][id]==1:
        numitems = struct.unpack('i', fid.read(4))[0]
    else:
        numitems = header['numvalues'][id]
    type = header['type'][id]
    if type == 'i' or type == 'f':
        size = 4
    elif type == 's':
        type = 'h'
        size = 2
    elif type == 'c':
        size = 1
    elif type == 'd':
        size = 8
    #bytes = numitems*size
    name = header['name'][id]
    dataframe=[struct.unpack(type, fid.read(size))[0] for i in range(numitems)]
#    if 'ET_filtered_gaze_object_name' in name:
#        pdb.set_trace()
    if not elemlist or name in elemlist:
        if not data[name]:
            data[name]=map(copy.copy, [[]]*numitems)
        for i in range(numitems):
            data[name][i].append(dataframe[i])
        if header['rate'][id]==-1:
            try:
                data[name+'_Frames'].append(frame['frame'][-1])
            except:
                data[name+'_Frames']=[frame['frame'][-1]]
    
def read_file(filename, elemfile = ''):
    if elemfile:
        elemlist = read_elemlist(elemfile)
    else:
        elemlist = []
    with open(filename,'rb') as f:
        daqdata={}
        daq=daq_meta(f)
        header = init_header()
        for i in range(daq['numentries']):
            append_header(f,header)
        frame = init_frame()
        data = init_data(header, elemlist)
        while True:
            try:
                frame['code'].append(struct.unpack('i',f.read(4))[0])
            except Exception, err:
                break;
            if frame['code'][-1]==-2:
                break
            frame['frame'].append(struct.unpack('i',f.read(4))[0])
            frame['count'].append(struct.unpack('i',f.read(4))[0])
            for j in range(frame['count'][-1]):
                try:
                    append_data(f, header, frame, data, elemlist)
                except Exception, err:
                    break;
        data['Frames'] = frame['frame']
        daqdata['daqInfo']=daq
        daqdata['elemInfo']=header
        daqdata['elemFrames']=frame
        daqdata['elemData']=data
        return daqdata
    
def convert_file(daqdata, filename):
    for cell in daqdata['elemData']:
        daqdata['elemData'][cell]=np.array(daqdata['elemData'][cell],order='F').transpose()
    sio.savemat(filename,daqdata,long_field_names=True,oned_as='column')
    
def read_elemlist(filename):
    with open(filename,'r') as f:
        elems = f.read().split('\n')
    elems = [elem.rstrip() for elem in elems]
    return elems
    
def convert_daq(filename, elemfile='', outname='', outpath=''):
    print "reading " + filename
    daqdata=read_file(filename,elemfile)
    if not outname:
        outname = os.path.splitext(filename)[0]+'.mat'
    if outpath:
        outname = os.path.join(outpath,outname)
    convert_file(daqdata,outname)
    print "file saved as " + outname
    return daqdata

    
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", \
        help="The name of the daq file")
    parser.add_argument("-e", "--elements", \
        help="The name of a txt file with a sublist of elements")
    parser.add_argument("-o","--outname", \
        help="The desired name of the output file")
    parser.add_argument("-p","--outpath", \
        help="The path in which to save the output file")
    args = parser.parse_args()
    filename = '20120601154617.daq' # default test file
    elemfile = ''
    outname = ''
    outpath = ''
    if args.file:
        filename = args.file
    if args.elements:
        elemfile = args.elements
    if args.outname:
        outname = args.outname
    if args.outpath:
        outpath = args.outpath
    d = convert_daq(filename,elemfile,outname,outpath)
    #from timeit import Timer
    #t = Timer("convert_daq('20120212145024')","from __main__ import test")
    #print t.timeit(1)
    #import cProfile
    #cProfile.run("test('20120212145024')")
    #d=convert_daq('HFCV_DriveB_main_20120611140939','elemListJoel.txt')
