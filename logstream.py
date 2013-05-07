from __future__ import print_function

# Copyright (c) 2013, Roger Lew
# All rights reserved.

from collections import OrderedDict

from undaqTools.element import Element, FrameSlice
from undaqTools.misc import _isint
            
def find_epochs(stream):
    '''
    Pulls the starting and stopping frames for epochs defined in a logstream.
    
    Parameters
    ----------
    stream : Element
       sliced to just the row you are interested in
    
    returns a OrderedDict of FrameSlice objects. FrameSlice objects are 
    namedTuples with named fields start, stop, and step fields. Element
    objects know how to slice relative to the frames specified by these
    FrameSlice objects
    
    Ignores epoch with a state of 0.
    
    Assumes that each epoch only occurs once. Raises RuntimeError if a 
    non-zero  epoch state occurs more than once.
    '''

    if not isinstance(stream, Element):
        raise ValueError('stream should be Element not %s'%type(stream))
        
    frames = stream.frames
    stream = stream.flatten()
    
    # we will return an OrderedDict so that the epochs match the order 
    # that they occured but can also be mapped 
    epochs = OrderedDict()
    
    # declare a, b in this scope so we can use them afterward
    # they hold a state and the subsequent state
    a,b = 0,0
    
    # loop through stream
    for i in xrange(len(stream)-1):
        
        # update state variables
        a,b = int(stream[i]), int(stream[i+1])
        
        # detect a change from one state to another
        if a != b:
            # entering epoch b
            if b!= 0 and b not in epochs:
                epochs[b] = frames[i]
            
            # existing epoch a
            if a in epochs:
                # if epochs[a] is an not an int then state a has
                # occured more than once and an Exception should be raised
                if not _isint(epochs[a]):
                    msg = "Epoch '%i' has already occured"%a
                    raise RuntimeError(msg)
                    
                # if everything is kosher then save the state as a namedTuple
                epochs[a] = FrameSlice(epochs[a], frames[i], None)
    
    # this is to take care of the case when the stream ends with a non-zero 
    # state
    if b!= 0:
        if _isint(epochs[b]):
            epochs[b] = FrameSlice(epochs[b], None, None)
            
    return epochs
