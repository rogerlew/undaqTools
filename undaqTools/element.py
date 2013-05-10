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
    Immutable FrameSlice object for slicing Element instances
    """)

FrameIndex = _namedtuple_factory('Index', ['frame'], 
                                 docstring= \
    """
    Immutable FrameIndex object for indexing Element instances
    """)
    
def fslice(*args):
    """
    fslice([start,] stop[, step])

    generates an immutable FrameSlice Instance
    
    Parameters
    ----------

    start : int or None, optional
        start frame

    stop : int or None
        stop frame

    step : into or None, optional
        steps between frames

    Returns
    -------
    fs : FrameSlice
    """
    start, stop, step = None, None, None
        
    if len(args) == 1:
        start, stop, step = None, args[0], None
    
    elif len(args) == 2:
        start, stop, step = args[0], args[1], None
        
    else:
        start, stop, step = args[:3]
        
    return FrameSlice(start, stop, step)

def findex(frame):
    """
    findex(frame)

    generates an immutable FrameIndex Instance
    
    Parameters
    ----------

    frame : int
        frame to index

    Returns
    -------
    findx : FrameIndex
    """
    return FrameIndex(frame)


class Element(np.ndarray, object):
    """
    Container to hold NADS DAQ cell data
    """
    def __new__(cls, data, frames, **kwds):
        """
        Element(data, frames[, **kwds])
        
        Create a new Element instance.
        
        Parameters
        ----------
        data : array_like
            shape should be (numvalues X number of samples)
        
        frames : array_like
            shape should be (number of samples,)
            
        rate : int, optional
            specifies whether measure is CSSDC
        
        name : string, optional
            specifies the name of the cell
            
        dtype : string or numpy type, optional
            type of data
            
        varrateflag : int, optional
            specifies whether data is collected at a variable rate
            
        elemid : int, optional
            specifies index in _header dict. Important in the MATLAB
            toolkit ndaqTools. Not so important here.
            
        units : string
             should probably be a list cooresponding 
             to the rows or a string depending on the cell
             
        order : string
            specifies the column order. Needed to write the
            mat files. Shouldn't be important to most end users.
             
        See Also
        --------
        :doc:`fslice` : FrameSlice factory for slicing Element by frames
        :doc:`findex` : FrameIndex factory for indexing Element by a frame
        """
        
        dtype = kwds.get('dtype', None)
        order = kwds.get('order', None)
        
        # array can handle the letter dtypes, as well as None and the np.type
        # objects
        obj = np.array(data, ndmin=2, dtype=dtype, order=order).view(cls)
        obj.frames  = np.array(frames, dtype=np.uint32)
        
        if obj.shape[1] != obj.frames.shape[0]:
            raise ValueError('data and frames are not aligned')
        
        # set or find other attributes
        obj.numvalues = obj.shape[0]
        obj.name = kwds.get('name', None)
        obj.id = kwds.get('elemid', None)   
        obj.units = kwds.get('units', '')
        obj.varrateflag = kwds.get('varrateflag', 0)

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
        
        rate = kwds.get('rate', None)
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
        
        elem.__getitem__(indx) <==> elem[indx]

        Parameters
        ----------
        indx : None, int, slice, tuple
            first arg of tuple must be None, int, or slice object.
            second arg can also be a FrameSlice or FrameIndex instance            
            
        Returns
        -------
        view : Element or possibly float
            the requested data
            
            when Element is a CSSDC measure and a FrameIndex is supplied:

            If frame is not defined it returns the last defined state.
            If shape of the state is (1,1) the state is returned as a scalar.
            If frame < elem.frames[0] then nan is returned.
        
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
                
            elif isinstance(indx[1], FrameIndex):
                return self._state_at_frame(indx[0], indx[1].frame)
                
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

    def _state_at_frame(self, rowindx, frame):
        """
        returns state (state array) of a CSSDC measure at supplied frame

        If frame is not defined it returns the last defined state.
        If shape of the state is (1,1) the state is returned as a scalar.
        If frame < elem.frames[0] then nan is returned.

        Parameters
        ----------
        frame : int

        rowindx : slice instance or int
            specifiies the row index to return
            if None then the state of elem is referenced to time

        """
            
        indx1 = np.searchsorted(self.frames, frame)-1
        indx2 = np.searchsorted(self.frames-1, frame)-1
        indx = max(indx1, indx2)

        # before first frame        
        if indx < 0:
            return np.nan
                        
        val = np.array(self.__getitem__((rowindx, indx)), ndmin=2).transpose()
        
        if len(val) == 1:
            return val[0]
        else:
            return val

    def toarray(self, ndmin=1, order=None):
        """
        cast data to plain old numpy array
        
        Parameters
        ----------
        ndmin : int
            the minimum dimension of the resulting array
            
        order : None or string
            the column order of the resulting array
            
        Returns
        -------
        x : np.ndarray
            the Element data as a numpy array
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
        """
        evaluates whether element is a CSSDC measure
        
        Returns
        -------
        answer : bool
            True if it is a CSSDC measure, False otherwise
        """
        return self.rate != 1
        