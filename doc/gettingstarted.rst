Getting Started
==========================
undaqTools uses the HDF5 (Hierarchical Data Format) data model 
to store the data contained within NAD's DAQ files. An undaq.py
script is provided aid in parallel batch processing DAQ files to
HDF5. Once converted instances of undaqTools.Daq object can load 
the HDF5 files. Users can add their own analysis information to 
the Daq instances, write them to HDF5 and retrive them when 
needed.

Daq Objects
------------

Daq objects can be initialized in two ways. The first is to
read the DAQ files directly.

>>> from undaqTools import Daq
>>> daq = Daq()
>>> daq.read(daq_file)

Daq.read will also unpack and process any dynamic objects that might
be present during the drive. This can be suppressed with the 
process_dynobjs keyword argument if so desired. 

>>> daq.read(daq_file, process_dynobjs=False)

The code attempts to find the relative headway distance between each 
dynamic object and the OwnVehicle (the driver). This requires some 
numerical optimization that extends the processing time. The additional 
time required depends on the number of dynamic objects in the drive.

Once loaded, saving the hdf5 is as simple as:

>>> daq.write_hd5(hd5_file)

Once an HDF5 file has been saved it can be reloaded with:

>>> daq.read_hd5(hd5_file)

Reading HDF5 files is about 2 magnitude orders faster than reading 
DAQ files directly. To provide a means of inspecting DAQ files directly
there is a stat function.

undaqTools.stat()
------------------
If you want to get metadata from a DAQ file but don't have it converted
to HDF5 you can use the undaqTools.stat() function to pull out the info
metadata. 

>>> from undaqTools import stat
>>> info = stat('data reduction_20130204125617.daq')
Info(run='data reduction', 
     runinst='20130204125617', 
     title='Nads MiniSim', 
     numentries=245, 
     frequency=59, 
     date='Mon Feb 04 12:56:17 2013\n', 
     magic='7f4e3d2c', 
     subject='part12', 
     filename='data reduction_20130204125617.daq')

Accessing Data
---------------
Daq objects are dictionary objects. The keys coorespond to the 
NADS variable names in the DAQ files. The values are Element
object instances. The Element class inherents numpy ndarrays 
and they are always 2 dimensional.

>>> daq['VDS_Veh_Speed'].shape
(1L, 10658L)

Because Element is a numpy.ndarray subclass they behave, for the
most part, just like the plain old numpy arrays that you are 
(hopefully) use to.

>>> np.mean(daq['VDS_Veh_Speed'])
76.4363

There is some special functionality built into these Elements that
we will get to later.

Daq.match_keys()
-----------------
The DAQ files provide an almost overwhelming amount of data. When you
first start getting acquainted with your driving simulator data it is 
easy to forget what contain the the things that you are interested in. 
The match_keys function makes this a little easier by allowing you to 
find keys that match Unix style wildcard patterns. The searches are 
case insensitive.

>>> daq.match_keys('*veh*dist*')
[u'VDS_Veh_Dist', u'SCC_OwnVeh_PathDist', u'SCC_OwnVehToLeadObjDist']

Daq.etc <*dict*>
-----------------
The data reductions are usually hypothesis driven. This means that we
need to obtain dependent measures reflecting the conditions of independent
variables. To perform the statistical analyses we need to keep track of
these things as well as other metadata. Every Daq instance has an etc
dictionary that can be used to store this metadata. Daq.write_hd5() will
export the etc dict and Daq.read_hd5() will restore it. 

>>> daq.etc['Gender'] = 'M'
>>> daq.etc['Factor1'] = [ 10, 20, 10, 20, 10, 20]
>>> daq.etc['Factor2'] = ['A','A','A','B','B','B']

.. Warning::
Internal it is using repr() on every dict value to export and eval() to 
reload the values. This means you probably don't want to load .hd5 files 
that come from an untrusted source. 

Working with Elements
----------------------
Element instances inherent numpy.ndarrays. They also keep track of the 
frames that their data represent. The frames are always a 1 dimensional
and are aligned with the second axis of the Element's data.

>>> veh_spd = daq['VDS_Veh_Speed']
>>> type(veh_spd.frames)
<type 'numpy.ndarray'>
>>> veh_spd.shape
(10658L,)

Dynamic objects also contain attribute data as Elements and may only be 
present during a subset of the drive. Because the dynamic object data
and the CSSDC measures are unaligned with the Elements it is not always
possible or convenient to simply use indexes to slice Elements. We need
to slice based on frames. This is possible with fslice()

>>> daq['VDS_Veh_Speed'][0, fslice(4000, 4010)]
Element(data = [ 42.17745972  42.3068924   42.4354744   42.56311417  42.68973923
                 42.81529999  42.93975449  43.06305313  43.18511963  43.3058815 ],
      frames = [4000 4001 4002 4003 4004 4005 4006 4007 4008 4009],
        name = 'VDS_Veh_Speed',
   numvalues = 1,
        rate = 1,
 varrateflag = False,
      nptype = float32)
      
As the reader can see from the string representation other metadata from 
the header block of the DAQ file gets attached to the Element.
      
CSSDC Elements
---------------
Many of the available measures are Change State Signal Detection (CSSDC) 
measures. they contains categorical data that only updates when a change 
in state is detected. 

>>> daq['TPR_Tire_Surf_Type']
Element(data = [[11  1  1 11 11 11  1  1 11 11  3  3  3  3  3  3 11 11  1  1 11 11  1  1]
                [11  1  1 11 11 11  1  1 11 11 11 11  3  3 11 11 11 11  1  1 11 11  1  1]
                [11 11  1  1  1 11 11  1  1 11 11  3  3  3  3  3  3 11 11  1  1 11 11  1]
                [11 11  1  1 11 11 11  1  1 11 11 11 11  3  3 11 11 11 11  1  1 11 11  1]
                [ 0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0]
                [ 0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0]
                [ 0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0]
                [ 0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0]
                [ 0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0]
                [ 0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0]],
      frames = [ 2716  5519  5523  5841  5844  5845  7970  7973  8279  8284  8785  8791
                 8818  8824  9127  9132  9166  9171 10270 10274 10597 10600 12655 12659],
        name = 'TPR_Tire_Surf_Type',
   numvalues = 10,
        rate = -1 (CSSDC),
 varrateflag = False,
      nptype = int16)

The above example contains data pertaining to surface type for the 4 tires 
and has 6 unfilled rows for additional tires. 

All elements with a rate != 1 (as defined in the DAQ file) are considered 
CSSDC. We can check this with isCSSDC()

>>> daq['TPR_Tire_Surf_Type'].isCSSDC()
True
>>> daq['VDS_Veh_Speed'].isCSSDC()
False

Use findex() to get the state at a given frame (even if the frame is not defined)

>>> # frame 5800 is not explictly defined
>>> daq['TPR_Tire_Surf_Type'][:4, findex(5800)] 
array( [[ 1],
        [ 1],
        [ 1],
        [ 1]], dtype=np.int16)

If you ask for a frame before the first defined frame you will get nan. 
If you ask for a frame after the last defined frame you will get the last 
frame.

method it is easy to test whether an Element contains CSSDC data. The
value at any frame between the first and last frame defined for a
CSSDC Element can be obtained through slicing. This treats
the data as categorical and always returns the last defined state.

Timeseries Plots
-----------------

>>> fig = daq.plot_ts([('VDS_Veh_Speed', 0)])

Notes
-----
**The Absence of a Time is a Feature**
    Time is almost completly redundant with the frames data. Just start 
    thinking in frames. It will soon become second nature. When you need 
    time just divide the frames by the sampling rate.