from __future__ import print_function

# Copyright (c) 2013, Roger Lew
# All rights reserved.

import numpy as np

def arburg(x, order):
    """
    Autoregressive (AR) all-pole model parameters estimated using Burg method

    Parameters
    ----------
    x : array_like
        Input data. real-valued
    order : int
        model order
    
    Returns
    -------
    returns AR coefficients
    
    """
    x = np.array(x)
    N = len(x)
    rho = np.sum(np.abs(x)**2.) / N
    den = rho * 2. * N

    ef = np.array(x) # forward errors
    eb = np.array(x) # backward errors

    # AR coeffs
    a = np.ones(1)
    
    # reflection coeffs
    ref = np.zeros(order)

    E = np.zeros(order+1)
    E[0] = rho

    for m in xrange(order):
        # reflection coefficient
        efp = ef[1:]
        ebp = eb[0:-1]
        num = -2.* np.dot(ebp.T, efp)
        den = np.dot(efp.T, efp)
        den += np.dot(ebp, ebp.T)
        ref[m] = num / den

        # forward and backward prediction errors
        ef = efp + ref[m] * ebp
        eb = ebp + ref[m].T * efp

        # AR coefficients
        a.resize(len(a)+1)
        a += ref[m] * a[::-1]
        
        # prediction error
        E[m+1] = (1. - ref[m].T*ref[m]) * E[m]

    return a