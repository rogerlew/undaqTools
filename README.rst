==========================================================
undaqTools [*uhn-dak-tools*] 
==========================================================

undaqTools is the the unofficial pythonic interface to the 
National Advanced Driving Simulator (NADS) Data AcQuisition 
(DAQ) files.

undaqTools (unofficial) vs. ndaqTools (official)
------------------------------------------------
**Approach:**  
  ndaqTools focuses on ease-of-use (via GUIs) and 
  templating. In contrast, the focus of undaqTools is on data 
  abstraction and simplification of data extraction. 
  
**Programming Language:** 
  ndaqTools is built on MATLAB.  Whereas, undaqTools utilizes the 
  opensource Python programming language (as well as Python's 
  opensource scientific stack (NumPy, SciPy, Matplotlib, and h5py).

**Data Storage:**
  ndaqTools stores and loads DAQ data as .mat files. undaqTools 
  stores and loads data in HDF5 containers.
  
Summary
-------    
undaqTools converts the native DAQ data into the HDF5 high
performance binary data format. From there data can be quickly
accessed in Python using the Daq class of undaqTools. Daq objects
are dict subclasses. The keys are the elements of the daq 
and the values are stored in a numpy array subclass called Element. 
Each Element contain measure relevent metadata stored as instance 
attributes so these metadata does not have to be accessed across 
datastructures. 

Each Element object also has a frames attribute that keeps track of 
the frames cooresponding to the element. This means that when they are
sliced the resulting views keeps the frames in sync without 
any additional book-keeping to the end user! The element data can 
also be sliced and indexed using frame indices. These abstractions 
simplify the complexity of managing these complex datasets (see class 
hierarchy diagram below).

undaqTools can also unpack and process dynamic objects. Each dynamic
object becomes a DynObj instance in the Daq's dynobj dict attribute.
The keys to the dynamic objects are the dynamic object names. The 
DynObj containers store the measure that you would expect (position, 
frames, speed, heading, etc.) as numpy.array objects as well as a 
running relative distance measure to the Own Vehicle.

These abstractions from the original DAQ representation are intended 
to provide the end user the convenience and capability to 
decide how to best utilize their data.

**Simplified Class Hierarchy Diagram**::

    Daq(dict)
      + [elemName] -> Element (ndarray)
      |                 + data
      |                 + frames (ndarray)
      |                 + rate
      |                 + type
      |                 + ...
      |               --------------------
      |                 + isCSSDC()
      |
      + dynobjs (dict)
      |   + [doName] -> DynObj (object)
      |                   + pos (Element)
      |                   + heading (Element)
      |                   + speed (Element)
      |                   + ...
      |                 ---------------------
      |                   + process()
      |                   + read_hd5()
      |                   + write_hd5()
      |                   + ...
      |
      + info (numedTuple)
      |   + run
      |   + subject
      |   + date
      |   + ...
      |
      | + etc (dict)
      | + ...
    --------------------------------------------
      | + read_daq() <==> read()
      | + read_hd5py()
      | + write_hd5py()
      | + write_mat()
      | ...