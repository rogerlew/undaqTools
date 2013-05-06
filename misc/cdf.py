import numpy as np

class CDF:
    """
    cumulative distribution function container object

    Parameters
    ----------
    bin_edges : array_like
        sorted in ascending order. ``(length(percentiles)+1)``
        
    percentiles : array_like
        percentile values of CDF (0-1) 

    """
    def __init__(self, bin_edges, percentiles):
        self.bin_edges = np.array(bin_edges)
        self.percentiles = np.array(percentiles)
        
    def find(self, percentile):
        """
        Returns the bin value at the given percentile

        Parameters
        ----------
        percentile : float
            Uses np.searchsorted to find closest index larger than percentile
            in self.percentiles. Returns bin value at that index.

            value should be between 0 and 1.

        Returns
        -------
        binatpercentile : float
            Value where CDF is at the supplied percentile
        """
        if percentile < 0. or percentile > 1.:
            raise ValueError('percentile must be between 0 and 1')
        
        return self.bin_edges[np.searchsorted(self.percentiles, percentile)]
    
    def plot(self):
        """
        Returns a matplotlib Figure object with CDF plotted

        Parameters
        ----------
        None

        Returns
        -------
        fig : matplotlib.figure.Figure

        See Also
        --------
        percentile : Calculates CDF percentiles for input u

        percentile

        Example
        -------
        >>> import numpy as np
        >>> u = np.random.normal(size=(1000,))
        >>> cdf = percentile(u, numbins=100)
        >>> fig = cdf.plot()
        >>> fig.show()
        """
        import matplotlib.pyplot as plt        
        plt.rc('font', family='serif')
        
        fig = plt.figure(figsize=(5,5))
        fig.subplots_adjust(left=.12)
        
        ax = fig.add_subplot(111)
        ax.plot(self.bin_edges[:-1], self.percentiles)
        ax.set_title('Cumumlative Distribution Function')
        ax.set_ylabel('Percentiles')
        ax.set_ylim([0,1])
        
        return fig

    def __repr__(self):
        return ('CDF(%s, %s)'%(repr(self.bin_edges), repr(self.percentiles)))\
               .replace('array', 'np.array')

    def __str__(self):
        st = ['  Bins       Percentiles\n',
               '------------------------\n']
        if len(self.percentiles) > 100:
            indices = range(10) + range(-10,0)
        else:
            indices = range(len(self.percentiles))

        for i in indices:
            if i == -10:
                st.append('      .         .\n'*3)

            _bin, _per = self.bin_edges[i], self.percentiles[i]
            st.append('{: >10}'.format(('{: .3f}'.format(_bin))))
            st.append('{: >10}'.format(('{: .2f}\n'.format(100*_per))))

        return ''.join(st)

def percentile(u, numbins=None):
    """
    Calculates CDF percentiles for input u

    Parameters
    ----------
    u : array_like
        Input data.

    numbins : None or int, optional
        Specifies the number of bins in the CDF object.
        
        If None than the number of bins become the length
        of u after removing nans. Otherwise numbins specifies
        the number of bins.

    
    See Also
    --------
    CDF : cumulative distribution function container object

    CDF

    Example
    -------
    >>> import numpy as np
    >>> u = np.random.normal(size=(1000,))
    >>> cdf = percentile(u, numbins=100)
    """
    u = np.array(u)
    u = u[~np.isnan(u)]
    u.sort()
    
    if numbins is None:
        numbins = len(u)

    stop = u[-1] + (u[-1]-u[0])/float(numbins)
    x = np.linspace(u[0], stop, numbins+1)
    y = np.cumsum(u+u[0])        
    y = np.interp(x[:-1], u, y)
    y /= y[-1]

    return CDF(x,y)
