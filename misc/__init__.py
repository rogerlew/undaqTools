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