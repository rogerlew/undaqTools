from __future__ import print_function

# Copyright (c) 2013, Roger Lew
# All rights reserved.

import numpy as np

from undaqTools.misc.base import _size_lookup, \
                                 _nptype_lookup, \
                                 _type_lookup, \
                                 _namedtuple_factory
    
FrameSlice = _namedtuple_factory('FrameSlice', ['start', 'stop', 'step'], 
                                 docstring= \
    """
    Create a FrameSlice object for slicing Element instances
    
    Parameters
    ----------
    start : int or None
        starting frame
        
    stop : int
        endng frame
        
    step : int or None
    
    """)

def frame_range(*args):
    """
    slice([start,] stop[, step])
    """
    start, stop, step = None, None, None
        
    if len(args) == 1:
        start, stop, step = None, args[0], None
    
    elif len(args) == 2:
        start, stop, step = args[0], args[1], None
        
    else:
        start, stop, step = args[:3]
        
    return FrameSlice(start, stop, step)

class Element(np.ndarray, object):
    def __new__(cls, data, frames, 
                rate=None, name=None, 
                dtype=None, varrateflag=0, 
                elemid=None, units='', order=None):
        """
       Creates a new Element from scratch.

        Developer Notes
        ---------------
        |   subclassing Numpy objects are a little different from subclassing 
        |   other objects.
        |   see: http://docs.scipy.org/doc/numpy/user/basics.subclassing.html
        """
        # array can handle the letter dtypes, as well as None and the np.type
        # objects
        obj = np.array(data, ndmin=2, dtype=dtype, order=order).view(cls)
        obj.frames  = np.array(frames, dtype=np.uint32)
        
        if obj.shape[1] != obj.frames.shape[0]:
            raise ValueError('data and frames are not aligned')
        
        # set or find other attributes
        obj.numvalues = obj.shape[0]
        obj.name = name
        obj.id = elemid   
        obj.units = units
        obj.varrateflag = varrateflag
        
        obj.type, obj.nptype == None, None 
        if dtype is None:
            obj.nptype = obj.dtype
            obj.type = _type_lookup[obj.nptype]
        elif dtype in _nptype_lookup:
            obj.type = dtype
            obj.nptype = _nptype_lookup[obj.type]
        elif dtype in _type_lookup:
            obj.nptype = dtype
            obj.type = _type_lookup[obj.nptype]
            
        if obj.type is None or obj.nptype is None:
            raise Exception('Could not find identify type for Element')
        
        obj.bytes = _size_lookup[obj.type]
        
        if rate is None:
            if obj.frames[-1] - obj.frames[0] > len(obj.frames):
                # missing frames
                obj.rate = -1
            else:
                obj.rate = 1
        else:
            obj.rate = rate
                    
        return obj

    def __array_finalize__(self, obj):

        self.name = getattr(obj, 'name', None)
        self.id = getattr(obj, 'id', None)
        self.rate = getattr(obj, 'rate', None)
        self.varrateflag = getattr(obj, 'varrateflag', None)
        self.numvalues = getattr(obj, 'numvalues', None)
        self.units = getattr(obj, 'units', None)
        self.nptype = getattr(obj, 'nptype', None)
        self.type = getattr(obj, 'type', None)
        self.bytes = getattr(obj, 'bytes', None)
        self.frames = getattr(obj, 'frames', None)

    __array_finalize__.__doc__ = np.ndarray.__array_finalize__.__doc__

    def __getitem__(self, indx):
        """
        Return the item described by indx, as an Element

           args:
              indx: index to array
                    can be int, tuple(int, int), tuple(slice, int),
                    tuple(int, slice) or tuple(slice, slice)

                    x[int] <==> x[int,:]

           returns:
              indexed Element

        |   x.__getitem__(indx) <==> x[indx]
        """
        # if a tuple is specified we need to check the second index to see
        # if it is a FrameSlice object. If it is, we need to figure out the
        # correct indices.
        #
        # We only need to check if a tuple is specified because the first
        # index can't be a FrameSlice. Frames are only aligned to the
        # the second index
        if isinstance(indx, tuple):
            if isinstance(indx[1], FrameSlice):
                f0, fend, step = indx[1].start, indx[1].stop, indx[1].step
                
                if f0 is not None:    
                    if (self.frames[0] > f0 > self.frames[-1] - 1):
                        raise IndexError('start FrameSlice is out of bounds')

                if fend is not None:    
                    if (self.frames[0] > fend > self.frames[-1] - 1):
                        raise IndexError('stop FrameSlice is out of bounds')
                    
                i0 = f0
                if f0 is not None:
                    i0 = np.searchsorted(self.frames, f0)
        
                iend = fend
                if fend is not None:
                    iend = np.searchsorted(self.frames, fend)
                    
                indx = (indx[0], slice(i0, iend, step))
                  
        obj = super(Element, self).__getitem__(indx)

        # we want to also index the times and frames arrays so that 
        # they stay consistent with the data
        #
        # The tricky thing is that __getitem__ operates recursively
        # we have to catch obj when it is an Element
        if isinstance(obj, Element) and  isinstance(indx, tuple):
            if obj.frames is not None:
                obj.frames = obj.frames[indx[-1]]
            
        return obj

    def state_at_frame(self, frame, rowindx=None):
        """
        returns state (state array) of a CSSDC measure at supplied frame

        If frame is not defined it returns the last defined state.
        If shape of the state is (1,1) the state is returned as a scalar.
        If frame < elem.frames[0] then nan is returned.

        Parameters
        ----------
        frame : int
            if None then the state of elem is referenced to time

        rowindx : None, slice object, int
            specifiies the row index to return
        """
            
        indx1 = np.searchsorted(self.frames, frame)-1
        indx2 = np.searchsorted(self.frames-1, frame)-1
        indx = max(indx1, indx2)

        # before first frame        
        if indx < 0:
            return np.nan
            
        if rowindx is None:
            rowindx = slice(None)
        val = np.array(self.__getitem__((rowindx, indx)), ndmin=2).transpose()
        
        if len(val) == 1:
            return val[0]
        else:
            return val

    def toarray(self, ndmin=1, order=None):
        """
        cast data to plain old numpy array
        """
        return np.array(self, ndmin=ndmin, order=order)

    def __str__(self):
        datas = super(Element, self) \
                    .__str__() \
                    .replace('\n', '\n'+' '*15)

        framess = str(self.frames).replace('\n', '\n'+' '*15)

        ratedesc = (',', ' (CSSDC),')[self.rate<0]
        
        slist = ["Element(data = %s,"%datas,
                 "      frames = %s,"%framess,
                 "        name = '%s',"%self.name,
                 "   numvalues = %i,"%self.numvalues,
                 "        rate = %i%s"%(self.rate, ratedesc),
                 " varrateflag = %s,"%bool(self.varrateflag),
                 "      nptype = %s)"%str(self.nptype)]
        
        return '\n'.join(slist)
                                
    def transpose(self):
        msg = 'transposing data would un-align data and frames.'
        raise NotImplementedError(msg)
        
    T = property(fget=lambda self:self.transpose())
    
    def __repr__(self):
        slist = [super(Element, self).__repr__()[:-1],
                 repr(self.name),
                 repr(self.id),
                 repr(self.rate),
                 repr(self.varrateflag),
                 repr(self.numvalues),
                 repr(self.units),
                 repr(self.nptype),
                 repr(self.type),
                 repr(self.bytes),
                 repr(self.frames) + ')']

        return ',\n        '.join(slist)\
                            .replace('np.array', 'array')\
                            .replace('array', 'np.array')

    def isCSSDC(self):
        return self.rate != 1
