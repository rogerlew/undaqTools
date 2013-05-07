from __future__ import print_function

# Copyright (c) 2013, Roger Lew
# All rights reserved.


from collections import namedtuple

import numpy as np

_size_lookup = { 'i':4, # 32 bit integer
                 'f':4, # 32 bit float
                 'h':2, # 16 bit integer
                 'c':1, #  8 bit character
                 'd':8 }# 64 bit double

_nptype_lookup = { 'i':np.dtype('i4'),
                   'f':np.dtype('f4'),
                   'h':np.dtype('int16'),
                   'c':np.dtype('S1'),
                   'd':np.dtype('f8') }

_type_lookup = { np.dtype('i4'):'i',
                   np.dtype('f4'):'f',
                   np.dtype('int16'):'h',
                   np.dtype('S1'):'c',
                   np.dtype('f8'):'d' }
                   
def _flatten(L):
    """
    flatten a multidimensional object
    """
    for item in L:
        if isinstance(item, basestring):
             yield item
        else: 
             try:
                 for i in _flatten(item):
                     yield i
             except TypeError:
                 yield item

def _isint(x):
    try:
        return x == round(x, 0)
    except:
        return False
        
def _searchsorted(a, v):
    """
    like numpy.searchsorted but returns len(a)-1 if v > a[-1]
    and v must be an scalar
    """
    if a.flatten()[-1] <= v:
        return len(a)-1
    else:
        return np.searchsorted(a.flatten(), v)
        
def _namedtuple_factory(typename, field_names, verbose=False,
                 rename=False, docstring=''):
    # http://stackoverflow.com/a/3349937
    # this one is by martineau @ stackoverflow
    
    '''Returns a new subclass of namedtuple with the supplied
       docstring appended to the default one.

    >>> Point = my_namedtuple('Point', 'x, y', docstring='A point in 2D space')
    >>> print Point.__doc__
    Point(x, y):  A point in 2D space
    '''
    # create a base class and concatenate its docstring and the one passed
    _base = namedtuple(typename, field_names, verbose, rename)
    _docstring = ''.join([_base.__doc__, ':  ', docstring])

    # fill in template to create a no-op subclass with the combined docstring
    template = '''class subclass(_base):
        %(_docstring)r
        pass\n''' % locals()

    # execute code string in a temporary namespace
    namespace = dict(_base=_base, _docstring=_docstring)
    try:
        exec template in namespace
    except SyntaxError, e:
        raise SyntaxError(e.message + ':\n' + template)

    return namespace['subclass']  # subclass object created