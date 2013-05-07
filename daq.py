from __future__ import print_function

# Copyright (c) 2013, Roger Lew
# All rights reserved.
#
# Credits: read_daq, and _loaddata are optimized version of Chris
#          Schwarz's convert_daq.py scipy in ndaqTools

import os
import warnings

from array import array
from collections import OrderedDict, namedtuple
from fnmatch import fnmatch
from operator import attrgetter
from random import uniform
from struct import unpack

import h5py
import matplotlib.pyplot as plt           
plt.rc('font', family='serif')  
import numpy as np

from numpy import fromfile
from scipy import io as sio

from undaqTools.misc.base import  _size_lookup, _nptype_lookup
from undaqTools.element import Element, FrameSlice
from undaqTools.dynobj import DynObj
from undaqTools.misc.recordtype import recordtype

def _searchsorted(a, v):
    """
    like numpy.searchsorted but returns len(a)-1 if v > a[-1]
    and v must be an scalar
    """
    if a.flatten()[-1] <= v:
        return len(a)-1
    else:
        return np.searchsorted(a.flatten(), v)

Info = namedtuple('Info', ['run','runinst','title','numentries',
                           'frequency','date','magic','subject',
                           'filename'])

Frame = recordtype('Frame', ['code', 'frame', 'count'])

Header = recordtype('Header', ['id','numvalues', 'name', 'units',
                               'bytes', 'rate', 'type', 'nptype',
                               'varrateflag'])

def stat(filename):
    """
    returns an Info namedtuple instance without loading data
    so the meta information can be interogatted without having
    to read the whole file

    Parameters
    ----------
    filename : string
       .daq file to investigate

    Returns
    -------
    daq : Daq instance

    Example
    -------
    >>> from pydaqTools import stat
    >>> print(stat('drive01.daq'))
    DAQ INFO
    **************************************************
    magic       7f4e3d2c
    frequency   59
    run         data reduction
    title       Nads MiniSim
    date        Mon Feb 04 12:56:17 2013
    runinst     20130204125617
    numentries  245
    subject     part12
    """
    fid = open(filename,'rb')
    read = fid.read # dots make things slow...

    # read info
    magic = read(4).encode('hex')
    title = read(120).split('\x00')[0]
    date = read(27).split('\x00')[0]
    subject = read(128).split('\x00')[0]
    run = read(128).split('\x00')[0]
    runinst = read(129).split('\x00')[0]
    numentries = unpack('i',read(4))[0]
    frequency = unpack('i',read(4))[0]
    filename = filename

    fid.close()

    return \
        Info(run=run, 
             runinst=runinst, 
             title=title, 
             numentries=numentries, 
             frequency=frequency, 
             date=date,  
             magic=magic, 
             subject= subject,
             filename=filename)
        
class Daq(dict):
    def __init__(self):

        # namedtuple containing drive relevant metadata
        self.info = Info(run='', 
                         runinst='', 
                         title='', 
                         numentries=0, 
                         frequency=0, 
                         date='',  
                         magic='', 
                         subject='',
                         filename='')
                         
        
        # recordtype of frame information
        self.frame = Frame(code=array('i'),
                           frame=array('i'),
                           count=array('i'))

        # recordtype of element header infomation
        self._header = None

        # other attributes
        self.data = {}               # dictionary to store elements
        self.elemlist = None         # specifies elements to load
        self.f0 = None               # first Frame in Daq. Probably not 0
        self.fend = None             # last Frame in Daq
        self.cursor = 0              # byte where the data frames begin in daq
        self.dynobjs = OrderedDict() # object to hold dynamic objects
        self.etc = {}

        dict.__init__(self)

    def load_elemlist_fromfile(self, filename):
        with open(filename,'r') as f:
            self.elemlist = [s.rstrip() for s in f.readlines()]

    def read_daq(self, filename, elemlist=None,
                 loaddata=True, process_dynobjs=True):
        """
        Reads a .daq file into object

        Parameters
        ----------
        filename : string
            path to .daq file

        elemlist : None or list_like
             None -> load all elements
             list_like -> load names that match list

        loaddata : bool
             True -> load data
             False -> don't load data
             
        process_dynobjs : bool
             True -> process dynobjs and put them in self.dynobjs
             False -> don't load dynobjs

        Returns
        -------
        None
        
        """        
        
        _header = \
            Header(id=None,
                   numvalues=array('i'),
                   name=[],
                   units=[],
                   rate=array('i'),
                   type=array('c'),
                   nptype=[],
                   varrateflag=array('i'),
                   bytes=array('i'))
        
        if elemlist is not None:
            self.elemlist = elemlist    

        fid = open(filename,'rb')
        read = fid.read # dots make things slow...

        # read info
        magic = read(4).encode('hex')
        title = read(120).split('\x00')[0]
        date = read(27).split('\x00')[0]
        subject = read(128).split('\x00')[0]
        run = read(128).split('\x00')[0]
        runinst = read(129).split('\x00')[0]
        numentries = unpack('i',read(4))[0]
        frequency = unpack('i',read(4))[0]
        filename = filename

        self.info = \
            Info(run=run, 
                 runinst=runinst, 
                 title=title, 
                 numentries=numentries, 
                 frequency=frequency, 
                 date=date,  
                 magic=magic, 
                 subject= subject,
                 filename=filename)

        # read header
        _header.id = range(self.info.numentries)
        
        for i in _header.id:
            # this use to be append_header
            # function call overhead is kind of high with
            # python so it is moved here for performance

            _header.numvalues.append(unpack('i',read(4))[0])
            _header.name.append(read(36).split('\x00')[0])
            _header.units.append(read(16).split('\x00')[0])
        
            _header.rate.append(unpack('h', read(2))[0])
            read(2) # seek is slow...
            _header.type.append(chr(unpack('i', read(4))[0]))
            if _header.type[-1] == 's':
                _header.type[-1] = 'h'
            _header.varrateflag.append(unpack('B', read(1))[0])
            read(3) # seek is slow...

        _header.bytes = [_size_lookup[t] for t in _header.type]
        _header.nptype = [_nptype_lookup[t] for t in _header.type]

        # remember where we are so we know where to start
        # reading in the data
        self.cursor = fid.tell()
        self._header = _header

        fid.close()
        
        if loaddata:
            self._loaddata()
            self._unwrap_lane_deviation()

        if loaddata and process_dynobjs:
            self._process_dynobjs()
            


    # create alias read for read_daq
    read = read_daq
                
    def _loaddata(self):
        """
        loads data from .daq file
        """
        _header = self._header
        elemlist = self.elemlist
        frame = self.frame
##        data = self.data
        
        def _issue_frame_read_warning(frame, name):
            msg = 'On Frame: %i, error unpacking %s'%(frame, name)
            warnings.warn(msg, RuntimeWarning)

        def nans(numitems):
            return [np.nan for i in xrange(numitems)]

        _elemid_lookup = dict(zip(_header.name, _header.id))
        
        # Data gets unpacked to a temporary dict tmpdata before building
        # Element objects
        # 
        # We will unpack 1d elements to an array object and then
        # change them to 2d ndarrays after the data is loaded.
        #
        # Elements with more than 1 dimension will get unpacked
        # as lists of arrays and transformed to ndarrays after
        # the data is loaded
        #
        # The array.array objects are typed unlike regular lists.
        # This improves memory usage. The array.array objects also
        # have highly efficient appending unlike ndarrays
        
        # initialize temporary dict
        tmpdata = {}        
        for name, _type, varrate, numvalues in \
            zip(_header.name, _header.type, 
                _header.varrateflag, _header.numvalues):
            if self.elemlist is None or \
               any(fnmatch(name, wc) for wc in self.elemlist):
                if not varrate and numvalues == 1:
                    tmpdata[name] = array(_type)
                else:
                    tmpdata[name] = []

        # Intialize Frame arrays for CSSDC measures
        for name in tmpdata.keys():
            if _header.rate[_elemid_lookup[name]] != 1:
                tmpdata[name+'_Frames'] = array('i')

        fid = open(self.info.filename,'rb')
        read = fid.read # dots make things slow...
        read(self.cursor) # move to where the data begins

        # The daq files have a frame for every sample. Each frame
        # contains the variables states at the time the frame was
        # saved. 
        #
        # we want to create arrays that can be indexed to decide
        # whether the variable needs stored. This way we don't
        # have to look through the elemlist for every variable on
        # every frame
        if elemlist is None: # elemlist empty                    
            go_nogo = [True for i in xrange(len(_header.name))]
        else: 
            go_nogo = [name in elemlist for name in _header.name]

        # Python quirk no. 372837462: while 1 is faster than while True
        while 1:
            try:
                frame.code.append(unpack('i',read(4))[0])
            except:
                raise Exception('error unpacking frame code')
                break
            
            if frame.code[-1] == -2:
                break
            
            frame.frame.append(unpack('i', read(4))[0])
            frame.count.append(unpack('i', read(4))[0])

            # xrange (2.7, range in 3) is faster than range
            for j in xrange(frame.count[-1]):

                # stuff performed in this loop use to be appendtmpdata
                # function call overhead is kind of high with python so
                # it is moved here for performance
                #
                # this code use to be under one try/except
                # Now only the unpacking is protected. If it fails NAN 
                # should be filled and a warning provided
                # Warnings could be supressed with the warnings module
                i = unpack('i', read(4))[0]

                if _header.varrateflag[i]:
                    numitems = unpack('i', read(4))[0]
                else:
                    numitems = _header.numvalues[i]
                            
                size = _header.bytes[i]
                    
##                    if 'ET_filtered_gaze_object_name' in name:
##                        pdb.set_trace()
                
                if go_nogo[i]:
                    name = _header.name[i]
                    
                    if numitems == 1:
                        _type = _header.type[i]
                        try:
                            tmpdata[name].append(unpack(_type, read(size))[0])
                        except:
                            _issue_frame_read_warning(frame.frame[-1], name)
                            tmpdata[name].append(np.nan)
                            
                    else: # numitems > 1
                        _type = _header.nptype[i]
                        try:
                            tmpdata[name].append(fromfile(fid, _type, numitems))
                        except:
                            _issue_frame_read_warning(frame.frame[-1], name)                             
                            tmpdata[name].append(nans(numitems))
                        
                    if _header.rate[i] != 1:
                        tmpdata[name+'_Frames'].append(frame.frame[-1])
                        
                else: # we don't need to read this element
                    read(numitems*size) # seek is slow...
                                        # reduce calls to read

        fid.close()

        # We made it through the daq file.
        # Now it is time to do some bookkeeping.
        frame.frame = np.array(frame.frame)
        self.f0 = frame.frame[0]
        self.fend = frame.frame[-1]
        
        # cast as Element objects
        # 'varrateflag' variables remain lists of lists
        #
        # There are obvious more compact ways to write this but I'm
        # paranoid about reference counting and garbage collection not
        # functioning properly
        for name, i, rate in zip(_header.name, _header.id, _header.rate):
            if elemlist is not None and name not in elemlist:
                continue
            
            # transpose Element with more than 1 row                
            if _header.numvalues[i] > 1:
                tmpdata[name] = np.array(tmpdata[name]).transpose()
            
            if rate != 1:
                self[name] = \
                    Element(tmpdata[name],
                            tmpdata[name+'_Frames'],
                            rate=_header.rate[i],
                            name=_header.name[i],
                            dtype=_header.type[i],
                            varrateflag=_header.varrateflag[i],
                            elemid=_header.id[i],
                            units=_header.units[i])
                
                del tmpdata[name+'_Frames']
            else:
                self[name] = \
                    Element(tmpdata[name],
                            frame.frame[:],
                            rate=_header.rate[i],
                            name=_header.name[i],
                            dtype=_header.type[i],
                            varrateflag=_header.varrateflag[i],
                            elemid=_header.id[i],
                            units=_header.units[i])

                # delete tmpdata arrays as we go to save memory
                del tmpdata[name]


        del _header, self._header
        self._header = None

        if self.fend - self.f0 > len(frame.frame):
            msg = "'%s' contains missing frames"%self.info.filename
            warnings.warn(msg, RuntimeWarning)
            
        # todo: interpolate if frames are missing after building Elements

    def _process_dynobjs(self):
        """
        figure out what rows and frames relate to particular
        dynamic objects so that they can be unpacked by
        DynObj.process
        """

        if 'SCC_DynObj_CvedId'not in self:
            msg = "Need 'SCC_DynObj*' to build dynobjs"
            warnings.warn(msg, RuntimeWarning)
            return None

        frame = self.frame
        cvedid_array = self['SCC_DynObj_CvedId']
        
        # identify the cars in the datafile and
        # identify what frames they are defined
        frame_indiceses = OrderedDict()
        row_indiceses = OrderedDict()

        # loop through frames, skipping first frame
        for i in xrange(1, len(frame.frame)):          
            
            cveds_in_frame = cvedid_array[:,i].flatten()

            for j, cved in enumerate(cveds_in_frame):
                if cved != 0:
                    try:
                        frame_indiceses[cved].append(i)
                        row_indiceses[cved].append(j)
                    except:
                        frame_indiceses[cved] = array('i', [i])
                        row_indiceses[cved] = array('i', [j])

        self.dynobjs = OrderedDict()
        for cvedId in frame_indiceses.keys():
            do = DynObj()
            do.process(cvedId,
                       np.array(frame_indiceses[cvedId]),
                       np.array(row_indiceses[cvedId]),
                       self)
            self.dynobjs[do.name] = do
            
        del frame_indiceses
        del row_indiceses
        
        
    def __setitem__(self, name, elem):
        if not isinstance(elem, Element):
            raise(TypeError, 'Value must be Element')
            
        if name is None and elem.name is not None:
            name = elem.name
            
        if elem.name is None and name is not None:
            elem.name = name
            
        if name != elem.name:
            msg = "key:'%s' does not equal elem.name'%s'\nCannot set value."
            raise(KeyError, msg%(name, elem.name))
            
        if name is None:
            msg = "name cannot be None"
            raise(KeyError, msg)
        
        dict.__setitem__(self, name, elem)
        
    def _unwrap_lane_deviation(self):

        if 'SCC_Spline_Lane_Deviation'not in self:
            msg = "Need 'SCC_Spline_Lane_Deviation' to fix lane deviation"
            warnings.warn(msg, RuntimeWarning)
            return None
            
        lane_dev = self['SCC_Spline_Lane_Deviation'][1,:]
        fixed_lane_dev =  np.unwrap(lane_dev*(np.pi/6.))*(6./np.pi)

        self['SCC_Spline_Lane_Deviation_Fixed'] = \
            Element(fixed_lane_dev,
                    self.frame.frame[:],
                    name=lane_dev.name+'_Fixed',
                    elemid=lane_dev.id,
                    rate=lane_dev.rate,
                    varrateflag=lane_dev.varrateflag,
                    units=lane_dev.units,
                    dtype=lane_dev.type)
                         
                    
    def _rebuild_header(self):
        """
        To write the .mat files and .hd5 files we need the header arrays.
        But inside the Daq object it is much simplier to access the element
        meta data through the Element objects. The HDF5 files could have
        a format that more closely approximates how the Daq is organized but
        it would not be as efficient storage-wise because every element would
        require have a frames array.

        If users manually add an Element to the data dict the header would
        also need to track those changes and that introduces a host of possible
        errors. It seems much simplier to just rebuild the header arrays when
        they are needed.
        """
        global _nptype_lookup, _size_lookup
        _header = \
            Header(id=array('i'),
                   numvalues=array('i'),
                   name=[],
                   units=[],
                   rate=array('i'),
                   type=array('c'),
                   nptype=[],
                   varrateflag=array('i'),
                   bytes=array('i'))

        i = 0
        for elem in sorted(self.values(), key=attrgetter('name')):
            _header.id.append(i)
            _header.numvalues.append(elem.numvalues)
            _header.name.append(elem.name)
            _header.units.append(elem.units)
            _header.rate.append(elem.rate)
            _header.type.append(elem.type)
            _header.nptype.append(elem.nptype)
            _header.varrateflag.append(elem.varrateflag)
            _header.bytes.append(elem.bytes)
            i += 1

        return _header


    def read_hd5(self, filename, f0=None, fend=None):
        """
        writes Daq object to HDF5 container

        f0 and fend specify frame range to read.
        Will export daq.dynobjs to HDF5 container
        
        Parameters
        ----------
        filename : string
            file to read
        
        f0 : None or int
            None -> read from beginning of file
            int -> read from this frame

        fend : None or int
            None -> read to end of file
            int -> read to this frame

        Return
        ------
        None
        """
        root = h5py.File(filename, 'r')

        # info
        self.info = \
            Info(run=root['info'].attrs['run'], 
                 runinst=root['info'].attrs['runinst'], 
                 title=root['info'].attrs['title'], 
                 numentries=root['info'].attrs['numentries'], 
                 frequency=root['info'].attrs['frequency'], 
                 date=root['info'].attrs['date'],  
                 magic=root['info'].attrs['magic'], 
                 subject=root['info'].attrs['subject'],
                 filename=root['info'].attrs['filename'])

        # header
        # The [:] unpacks the data from a h5py.dataset.Dataset
        # object to a numpy.ndarray object
        try:
            _header = \
                Header(id=root['header/id'][:],
                       numvalues=root['header/numvalues'][:],
                       name=root['header/name'][:],
                       units=root['header/units'][:],
                       rate=root['header/rate'][:],
                       type=root['header/type'][:],
                       nptype=root['header/nptype'][:],
                       varrateflag=root['header/varrateflag'][:],
                       bytes=root['header/bytes'][:])
        except:
            _header = \
                Header(id=array('i'),
                       numvalues=array('i'),
                       name=[],
                       units=[],
                       rate=array('i'),
                       type=array('c'),
                       nptype=[],
                       varrateflag=array('i'),
                       bytes=array('i'))
        
        # Find the indices cooresponding to the first and last
        # frames requested. We can use these indices to
        # slice out all the non-CSSDC elements.
        #
        # For the CSSDC elements we will have to find the
        # appropriate indices as we go.
        i0, iend = None, None
    
        try:
            all_frames = root['frame/frame'][:]
        except:
            all_frames = None

        if all_frames is not None:
            if f0 is not None or fend is not None:
                if f0 is not None:
                    i0 = _searchsorted(all_frames, f0)
                if fend is not None:
                    iend = _searchsorted(all_frames, fend)
                    if iend < len(all_frames):
                        iend += 1
                    
        indx = slice(i0,iend)

        # frame
        try:
            self.frame = \
                Frame(code=root['frame/code'][indx],
                      frame=root['frame/frame'][indx],
                      count=root['frame/count'][indx])
        except:
            self.frame = \
                Frame(code=array('i'),
                      frame=array('i'),
                      count=array('i'))

        # elemlist
        try:
            # Fails if slice is zero-length
            self.elemlist = root['elemlist'][:] 
        except:
            self.elemlist = None
            
        # data
        # Procedure is similar to read_daq. Data is unpacked
        # to tmpdata dict and then the Elements are instantiated.
        _elemid_lookup = dict(zip(_header.name, _header.id))
        
        tmpdata = {}
        for k, v in root['data'].iteritems():
            
            if self.elemlist is not None:
               if not any(fnmatch(k, wc) for wc in self.elemlist):
                   continue
                
            i = _elemid_lookup[k.replace('_Frames','')]
            
            if _header.rate[i] == 1:
                tmpdata[k] = v[:,i0:iend]
                
            else: #CSSDC measure
                if len(v.shape) == 1:
                    v = np.array(v, ndmin=2) # _Frames
                    
                # Need to find indices
                _i0 = 0
                _iend= v.shape[1]

                if f0 is not None or fend is not None:
                    _name = k.replace('_Frames','')
                    _all_frames = root['data/%s_Frames'%_name][:].flatten()

                    if f0 is not None:
                        _i0 = _searchsorted(_all_frames, f0)
                    if fend is not None:
                        _iend = _searchsorted(_all_frames, fend)
                        if _iend < len(_all_frames):
                            _iend += 1

                # Now we can slice the data
                tmpdata[k] = v[:,_i0:_iend]

        # hdf5 doesn't have a None type (or atleast, I don't know how
        # to use it) so None is stored as an empty string in the hdf5 file
        self.f0 = (root.attrs['f0'], None)[root.attrs['f0'] == '']
        self.fend = (root.attrs['fend'], None)[root.attrs['fend'] == '']
        self.cursor = root.attrs['cursor']

        # read dynobjs
        self.dynobjs = OrderedDict()  
        for (name, dynobj) in root['dynobjs'].iteritems():
            do = DynObj()
            do.read_hd5(root=dynobj)
            self.dynobjs[name] = do
                    
        # read etc dict
        self.etc = {}  
        for (name, obj) in root['etc'].attrs.iteritems():
            self.etc[name] = eval(obj)
            
        root.close()

        # cast as Element objects
        # 'varrateflag' variables remain lists of lists
        #
        # There are obvious more compact ways to write this but I'm
        # paranoid about reference counting and garbage collection not
        # functioning properly
        for name, i, rate in zip(_header.name, _header.id, _header.rate):
            if rate != 1:
                self[name] = \
                    Element(tmpdata[name],
                            tmpdata[name+'_Frames'].flatten(),
                            rate=_header.rate[i],
                            name=_header.name[i],
                            dtype=_header.type[i],
                            varrateflag=_header.varrateflag[i],
                            elemid=_header.id[i],
                            units=_header.units[i])
                
                del tmpdata[name+'_Frames']
            else:
                self[name] = \
                    Element(tmpdata[name],
                            self.frame.frame[:],
                            rate=_header.rate[i],
                            name=_header.name[i],
                            dtype=_header.type[i],
                            varrateflag=_header.varrateflag[i],
                            elemid=_header.id[i],
                            units=_header.units[i])
                            
                # delete tmpdata arrays as we go to save memory
                del tmpdata[name]
                
        del _header
        

    def write_hd5(self, filename=None):
        """
        writes Daq object to HDF5 container

        Parameters
        ----------
        filename : None or string (optional)
            None : file written to daq.filename.replace('.daq', '.hdf5')
            string : specify output file (will overwrite)

        Return
        ------
        None
        """
        info = self.info
        frame = self.frame
        _header = self._rebuild_header()
        str_type = h5py.new_vlen(str)
        
        if filename is None:
            filename = info.filename[:-4] + '.hdf5'

        if filename.endswith('.daq'):
            # yes, I did this accidently
            msg = 'Writing Daq in HDF5 with a .daq extension is not allowed'
            raise ValueError(msg)
        
        root = h5py.File(filename, 'w')

        # info
        root.create_group('info')
        root['info'].attrs['run'] = info.run
        root['info'].attrs['runinst'] = info.runinst
        root['info'].attrs['title'] = info.title
        root['info'].attrs['numentries'] = info.numentries
        root['info'].attrs['frequency'] = info.frequency
        root['info'].attrs['date'] = info.date
        root['info'].attrs['magic'] = info.magic
        root['info'].attrs['subject'] = info.subject
        root['info'].attrs['filename'] = info.filename

        # frame
        root.create_group('frame')
        root['frame'].create_dataset('frame', data=frame.frame)
        root['frame'].create_dataset('count', data=frame.count)
        root['frame'].create_dataset('code', data=frame.code)

        # header
        root.create_group('header')        
        root['header'].create_dataset('id', data=_header.id)
        root['header'].create_dataset('numvalues', data=_header.numvalues)
        root['header'].create_dataset('name', data=_header.name)
        root['header'].create_dataset('units', data=_header.units)
        root['header'].create_dataset('rate', data=_header.rate)
        root['header'].create_dataset('type', data=_header.type)
        root['header'].create_dataset('varrateflag', data=_header.varrateflag)
        root['header'].create_dataset('bytes', data=_header.bytes)

        nptype_asstr = np.array(_header.nptype, dtype=str_type)
        root['header'].create_dataset('nptype', data=nptype_asstr)

        # data
        root.create_group('data')
        for name, elem in self.items():
            root['data'].create_dataset(name, data=elem.toarray())

            if elem.isCSSDC():
                root['data'].create_dataset(name+'_Frames',
                                            data=elem.frames)
        # misc
        root.create_dataset('elemlist',
                            data=np.array(self.elemlist, dtype=str_type))
        root.attrs['f0'] = (self.f0, '')[self.f0 is None]
        root.attrs['fend'] = (self.fend, '')[self.fend is None]
        root.attrs['cursor'] = self.cursor

        # dynobjects
        root.create_group('dynobjs')
        for (name, do) in self.dynobjs.items():
            root.create_group('dynobjs/%s'%name)
            do.write_hd5(root=root['dynobjs/%s'%name])
            
        # etc
        root.create_group('etc')
        for (name, value) in self.etc.items():
            root['etc'].attrs[name] = repr(value)
            
        root.close()


    def write_mat(self, filename=None, outpath=None):
        """
        writes Daq object to .mat file using scipy.io.savmat

        daq.dynobjs is not exported

        This is intended to make convert_daq backwards compatible.
        pydaqTools users should use write_hdf5. The .mat files cannot
        be used to instantiate Daq objects.

        Parameters
        ----------
        filename : None or string (optional)
            None : file written to daq.filename.replace('.daq', '.hdf5')
            string : specify output file (will overwrite)

        outpath : None or string (optional)
            string : directory to path
            
        Return
        ------
        None


        """
        
        if filename is None:
            filename = os.path.splitext(self.info.filename)[0]+'.mat'
            
        if outpath is not None:
            filename = os.path.join(outpath,filename)

        # data
        data = {}        
        for name in self:
            data[name] = np.array(self[name], order='F').transpose()

            if self[name].isCSSDC():
                data[name+'_Frames'] = np.array(self[name].frames, order='F')
                data[name+'_Frames'] = data[name+'_Frames'].transpose()
                
        data['Frames'] = np.array(self.frame.frame, ndmin=2, order='F')
        data['Frames'] = data['Frames'].transpose()

        # header
        header = self._rebuild_header()._asdict()
        del header['nptype']
        header['type'] = [(t,'s')[t=='h'] for t in header['type']]
        
        sio.savemat(filename,
                    {'daqInfo':dict(self.info._asdict()),
                     'elemInfo':header,
                     'elemData':data,
                     'elemFrames':dict(self.frame._asdict())},
                    long_field_names=True, oned_as='column')
        
        del data
        del header

    def plot_ts(self, elem_pars, xindx=None):
        """
        Returns a time series figure containing elements specified by
        elem_pars

        CSSDC measures yield step plots.

        Parameters
        ----------
        elem_pars : list of tuples
            each tuple should contain
                name : str
                    element to plot
                yindx : None, int, or slice object
                    specifies the values of element to plot
                    None -> slice(None, None, None)

        xindx : None, slice object, FrameSlice object
            specifies the frame range to plot
            None -> slice(None, None, None)

        Returns
        -------
        pyplot figure object
        """
        # initialize variables and figure

        fs = float(self.info.frequency)
        num_subplots = len(elem_pars)
        fig, axs = plt.figure(figsize=(16, 2*len(elem_pars))), []
        fig.subplots_adjust(left=.07, right=.98, bottom=.03,
                            top=.97, hspace=.25)
                            
        if xindx is None:
            xindx = slice(None)

        # loop through requested elements and plot
        for i, (name, yindx) in enumerate(elem_pars):
                
            # make subplot
            axs.append(fig.add_subplot(num_subplots, 1, i+1))

            if yindx is None:
                yindx = slice(None)
                
            # figure out data
            elem = self[name]
            y = elem[yindx, xindx]
            x = y.frames.flatten()/fs
            
            if len(y.shape) == 1:
                if elem.isCSSDC():
                    axs[-1].step(x, y, where='pre')
                else:
                    axs[-1].plot(x, y)
            else:
                for j in xrange(y.shape[0]):
                    if elem.isCSSDC():
                        axs[-1].step(x, y[j,:], where='pre')
                    else:
                        axs[-1].plot(x, y[j,:])

            # set xlim
            axs[-1].set_xlim([x[0], x[-1]])

            # put a title on the subplot
            def indx_frmttr(slice_obj):
                if slice_obj == slice(None):
                    return ':'
                
                return str(slice_obj).replace('FrameSlice(', '') \
                                     .replace('slice(', '') \
                                     .replace('start=None', '') \
                                     .replace('stop=None', '') \
                                     .replace('step=', '') \
                                     .replace('start=', 'f') \
                                     .replace('stop=', 'f') \
                                     .replace(', None)', '') \
                                     .replace(', ', ':') \
                                     .replace(')', '')
            
            axs[-1].set_title('%s[%s, %s]'%(name,
                                            indx_frmttr(yindx),
                                            indx_frmttr(xindx)))

        # remove xticklabels from all but the last subplot
        for i in xrange(num_subplots-1):
            axs[i].set_xticklabels([])

        return fig

    def plot_dynobjs(self, dynobj_wc='*'):
        """
        make top-down plot of dynamic object paths

        """
  
        # make top down plot
        fig = plt.figure(figsize=(12, 12))
        fig.subplots_adjust(left=.02, right=.98, bottom=.02, top=.98)
        ax = fig.add_subplot(111)
        ax.axis('equal')

        colors = 'bgrcm'
        line_styles = ['-','-.',':']
        ados = [do for do in self.dynobjs.values() \
                if fnmatch(do.name, dynobj_wc)]        
        for i, do in enumerate(ados):
            ax.plot(do.pos[0,:] + uniform(-600,600),
                    do.pos[1,:] + uniform(-600,600),
                    label=do.name, alpha=1.,
                    c=colors[i%5],
                    ls=line_styles[i%3])
            
        # plot the external driver
        ax.plot(self['VDS_Chassis_CG_Position'][0,:],
                self['VDS_Chassis_CG_Position'][1,:],
                c='k', label=self.info.subject)

##        xlim=pylab.xlim()
##        pylab.xlim([xlim[0], xlim[1]*1.9])
##        pylab.legend(ncol=2)
        
        return fig
        
    def match_keys(self, wc):
        """
        Returns a list of keys (element names) that match 
        the Unix-style wildcard.

        Patterns are Unix shell style:
            *       matches everything
            ?       matches any single character
            [seq]   matches any character in seq
            [!seq]  matches any char not in seq

        keys and wc both case normalized
        
        Parameters
        ----------
        wc : string
            wildcard apply to each match
            
        Returns
        -------
        list of names (keys to daq)
        
        
        """
        return [name for name in self if fnmatch(name, wc)]