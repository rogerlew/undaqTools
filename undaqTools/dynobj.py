from __future__ import print_function

# Copyright (c) 2013, Roger Lew
# All rights reserved.

from array import array
import math
from collections import Counter
import warnings

import h5py
import numpy as np

from undaqTools.element import Element

class DynObj:
    """
    class to represent AI controlled dynamic objects.

    The simulator `only` keeps track of the nearest 20 dynamic objects
    and packs them into the Daq in a haphazard fashion. Daq._process_dynobjs
    and DynObj.process sort out this data and create a DynObj instance for
    each dynamic object recorded during the drive.

    Attributes
    ----------
    hcsmType : int
        don't know what this is
        
    colorIndex : int
        the color of the vehicle
        
    solId : int
        vehicle type
        
    cvedId : int
        id unique to drive
        
    name : string
        name defined in Isat "Ado..."
        
    interpolated : bool (int)
        whether the data was interpolated
        
    frames : np.ndarray
       
    heading : Element
        global heading in rads (rotated 90 degrees, need to fix.)
        
    speed : Element
        vehicle speed in mph
    
    roll : Element
        roll
        
    pitch : Element
        pitch
        
    pos : Element
        global x, y, z coordinates in feet
        
    distance : Element
        distance traveled since intialized
    
    relative_distance : Element
        headway distance
        
    relative_distance_err : float
        error in relative distance estimate
        (assuming you know apriori the dynamic object travels the same path
        as the OwnVehicle)
    """
    def __init__(self):
        self.name = ''

    def process(self, cvedId, frame_indices, row_indices, daq):
        """
        unpacks data from the SCC_DynObj* Elements

        Parameters
        ----------
        cvedId : int
            numerical id of the dynamic object. Used to sort out what rows and
            columns in the SCC_DynObj* Elements coorespond to this vehicle

        frame_indices : array_like
            indices in the parent daq that contain information relevent
            to the dynamic object

        row_indices : array_like
            column by column indices specifying which rows coorespond to the
            dynamic object

        daq : Daq
            pointer to the parent Daq instance
    
        Notes
        -----
        This should really be a private method.
        
        """

        self.parent_filename = daq.info.filename
        self.i0 = i0 = frame_indices[0]      # this is the first index relative
                                             # to the daq data arrays that the
                                             # dynobj is present
        self.iend = iend = frame_indices[-1] # this is the last index that the
                                             # dynobj is present
                                             # Warning: don't mix up frame indices
                                             # with frame numbers!
        
        # treat async as int to make export and import to h5py easier
        # 0 = no frames are missing
        # 1 = frames are missing (vehicle was dropped when more than
        #     20 dynamic objects were present
        async = int(not len(frame_indices) == (self.iend - self.i0))
        
        r,c = row_indices[0], frame_indices[0]
        self.hcsmType = daq['SCC_DynObj_HcsmType'][r,c]
        self.colorIndex = daq['SCC_DynObj_ColorIndex'][r,c]
        self.solId = daq['SCC_DynObj_SolId'][r,c]
        self.cvedId = daq['SCC_DynObj_CvedId'][r,c]

        # to unpack the name we look at the 'SCC_DynObj_Name' on the first
        # frame that the dynamic object is present. The string array is
        # split into 20 segments of 32 chars. Then the following operations
        # are perfomed on the substring
        #  1. empty chars are replaced with ' '
        #  2. string is reversed and split based on white space
        #  3. resulting list of substrings are reversed
        #  4. list of substrings is concatenated
        #  5. whitespace is striped.
        str_array = daq['SCC_DynObj_Name'][r*32:r*32+32, c][::-1]
        self.name = ''.join([(s,' ')[s==''] for s in str_array]).split()[::-1]
        self.name = ''.join(self.name).strip()

        # specifies whether array attributes have been interpolated
        self.interpolated = 0

        # first we loop through the daq to extract the following
        # variables based on the frame and row indices provided
        frames = None

        row_indices_x2 = row_indices*2
        row_indices_x3 = row_indices*3
        
        heading = daq['SCC_DynObj_Heading'][row_indices, frame_indices]
        speed = daq['SCC_DynObj_Vel'][row_indices, frame_indices]
        roll = daq['SCC_DynObj_RollPitch'][row_indices_x2, frame_indices]
        pitch = daq['SCC_DynObj_RollPitch'][row_indices_x2+1, frame_indices]
        x = daq['SCC_DynObj_Pos'][row_indices_x3, frame_indices]
        y = daq['SCC_DynObj_Pos'][row_indices_x3+1, frame_indices]
        z = daq['SCC_DynObj_Pos'][row_indices_x3+2, frame_indices]
        pos = np.asarray([x,y,z])
         
        del x,y,z
        
        # positions are packed [y,x,z] for the dyn objects
        # here we swap x and y to make it consistent with OwnVeh
        # position.
        tmp = np.copy(pos[0,:])
        pos[0,:] = pos[1,:]
        pos[1,:] = tmp
        
        # need to linearly interpolate asyncronous cveds
        if async:
            _frames = np.arange(i0, iend+1, dtype='i4')
            heading = np.interp(_frames, frame_indices, heading)
            speed = np.interp(_frames, frame_indices, speed)

            pos = np.array([np.interp(_frames, frame_indices, pos[0,:]),
                            np.interp(_frames, frame_indices, pos[1,:]),
                            np.interp(_frames, frame_indices, pos[2,:])])

            roll = np.interp(_frames, frame_indices, roll)
            pitch = np.interp(_frames, frame_indices, pitch)
            
            # convert from indices to frames
            frames = _frames + int(daq.frame.frame[0]) 
            
            self.interpolated = 1

        # otherwise we just need take care of some more book-keeping
        else:
            heading = np.array(heading, ndmin=2)
            speed = np.array(speed, ndmin=2)
            
            # convert from indices to frames            
            frames = frame_indices + int(daq.frame.frame[0])

        heading = np.array(heading, ndmin=2)
        speed = np.array(speed, ndmin=2)
        roll = np.array(roll, ndmin=2)
        pitch = np.array(pitch, ndmin=2)

        # calculate distance vector. At the first frame it is
        # defined, it has a distance of 0.
        distance = np.cumsum(np.sum(np.square(np.diff(pos)), axis=0))
        distance = np.concatenate(([0.], distance))
        distance = np.array(distance, ndmin=2)

        # calculate relative distance to OwnVehicle
        #
        ###############################
        ###                         ###
        ### Caution: headache ahead ###
        ###                         ###
        ###############################
        #
        # for now it assumes that the vehicle is own the same path and
        # heading in the same direction as the OwnVehicle
        
        direction = None
        relative_distance_err = None
        if 'VDS_Veh_Dist' not in daq or 'VDS_Veh_Heading' not in daq:
            msg = "Need 'VDS_Veh_Dist' and 'VDS_Veh_Heading'"\
                  " in daq to find relative distance"
            warnings.warn(msg, RuntimeWarning) 
        else:
            (n, m) = distance.shape
    
            # calculate distance between starting position and
            # OwnVehicle over the drives duration
            ov_pos = daq['VDS_Chassis_CG_Position'][:,i0:i0+m]
    
            # Need to find a point to calibrate the relative distance
            # we need to find a point that the DynObject and OwnVeh
            # comes close to (within a few feet).
            #
            # Because the arrays are so large the time and space complexity
            # eliminates using an optimal solution. Instead what we are doing 
            # is randomly selecting 5 points over the duration that the DynObj 
            # is defined. For each of these points we calculate the distance 
            # relative to the OwnVeh over the epoch for which the DynObj is 
            # defined. The index of the minimum point yields the point in time 
            # that the OwnVeh comes closest to the randomly selected point. 
            # The minimum yields a measure of error. We select the point that 
            # comes closest to the OwnVeh. The randomly chosen index (do_imin) 
            # gives us the point in the DynObj array that should be 0 when 
            # calculating relative distance. The index to the minimum distance 
            # value gives us the point that distnace should be 0 for OwnVeh.
            
            d0s,imins = [],[]
            rand_indices = list(np.random.randint(low=0, high=m, size=(10,)))
            for ri in rand_indices:
                dmin = ov_pos - np.array(pos[:,ri], ndmin=2).T
                dmin = np.sqrt(np.sum(np.square(dmin), axis=0))

                # index where OwnVeh is closest to the starting pos of the
                # DynObject index is relative to the shorter DynObj arrays not
                # the larger daq arrays
                imins.append(dmin.argmin())
    
                # distance DynObject is likely ahead (error from pos data)
                d0s.append(dmin[imins[-1]])
    
            best_i = np.argmin(d0s)
            d0 = d0s[best_i]
            imin = imins[best_i]
            do_imin = rand_indices[best_i]
            
            del best_i, d0s, imins, ri, rand_indices
            
            # at the minimum point the OwnVeh has covered a distance of
            ov_d0 = daq['VDS_Veh_Dist'][0,i0+imin]
    
            # at the minimum point the DynObj has covered a distance of
            do_d0 = distance[:, do_imin]
    
            # Next we ned to identify whether dynamic object is heading in the
            # same direction or the opposite direction as the OwnVehicle. Here
            # we assume it is one or the other. Objects on perpendicular roads
            # or perpendicular courses won't be correctly categorized.
    
            # for OwnVeh heading is in VDS_Veh_Heading and has degree units
            ov_h = np.radians(daq['VDS_Veh_Heading'][0,i0:i0+m])
            ov_h = np.unwrap(ov_h)
    
            # compare the heading direction of OwnVehicle at its closest point
            # to the dyn object to the heading direction of the dyn object at
            # its closest point. This compares their headings at a point in
            # space NOT a point in time.
            rad_diff = math.atan2(math.sin(ov_h[imin] - heading[0,do_imin]),
                                  math.cos(ov_h[imin] - heading[0,do_imin]))
            
            # Don't know how robust this is to intersection traffic. Seems to
            # work reliably with traffic in a giant rural loop
            direction = int(rad_diff < 0.) # 1 -> same direction
                                           # 0 -> opposite direction
    
            # thus relative distance is given by
            ov_distance = daq['VDS_Veh_Dist'][:,i0:i0+m] - ov_d0
            do_distance = distance - do_d0
            if not direction:
                do_distance *= -1.
                
            relative_distance = do_distance - ov_distance
            relative_distance_err = d0
        
        self.frames = frames
        self.heading = Element(heading, frames, name='Heading')
        self.speed = Element(speed, frames, name='Speed')
        self.roll = Element(roll, frames, name='Roll')
        self.pitch = Element(pitch, frames, name='Pitch')
        self.pos = Element(pos, frames, name='Position')
        self.distance = Element(distance, frames, name='Distance')
        
        if relative_distance_err is None:
            self.direction = None
            self.relative_distance = None
            self.relative_distance_err = None            
        else:
            self.direction = direction
            self.relative_distance = \
                Element(relative_distance, frames, name='Relative_Distance')
            self.relative_distance_err = relative_distance_err
        
    def write_hd5(self, filename=None, root=None):
        """
        write_hd5(self[, filename=None][, root=None])
        
        writes DynObj to hdf5.

        Parameters
        ----------
        filename : string
            path to write to

        root : h5py.File
            handle to group
        """
        close_root = root is None
        
        if filename is None and root is None:
            filename = '%s.%s.hdf5'%(self.parent_filename, self.name)
            root = h5py.File(filename, 'w')
        elif root is None and filename is not None:
            root = h5py.File(filename, 'w')
      # else root is given
            

        root.attrs['parent_filename'] = self.parent_filename
        root.attrs['i0'] = self.i0
        root.attrs['iend'] = self.iend
        root.attrs['hcsmType'] = self.hcsmType
        root.attrs['colorIndex'] = self.colorIndex
        root.attrs['solId'] = self.solId
        root.attrs['cvedId'] = self.cvedId
        root.attrs['name'] = self.name
        root.attrs['interpolated'] = self.interpolated
        root.attrs['direction'] = self.direction
        root.attrs['relative_distance_err'] = self.relative_distance_err
        
        root.create_dataset('frames', data=self.frames)
        root.create_dataset('heading', data=self.heading)
        root.create_dataset('speed', data=self.speed)
        root.create_dataset('roll', data=self.roll)
        root.create_dataset('pitch', data=self.pitch)
        root.create_dataset('pos', data=self.pos)
        root.create_dataset('distance', data=self.distance)
        root.create_dataset('relative_distance', data=self.relative_distance)

        if close_root:
            root.close()

    def read_hd5(self, filename=None, root=None):
        """
        read_hd5(self[, filename=None][, root=None])
        
        reads a DynObj from a hdf5 file.

        Parameters
        ----------
        filename : string
            path to write to

        root : h5py.File
            handle to group
        """
        close_root = root is None
        
        if filename is None and root is None:
            raise ValueError('filename or root must be defined')
        elif root is None and filename is not None:
            root = h5py.File(filename, 'r')
                        
        self.parent_filename = root.attrs['parent_filename']
        self.i0 = root.attrs['i0']
        self.iend = root.attrs['iend']
        self.hcsmType = root.attrs['hcsmType']
        self.colorIndex = root.attrs['colorIndex']
        self.solId = root.attrs['solId']
        self.cvedId = root.attrs['cvedId']
        self.name = root.attrs['name']
        self.interpolated = root.attrs['interpolated']
        self.direction = root.attrs['direction']
        
        self.frames = frames = root['frames'][:]
        self.heading = Element(root['heading'][:], frames, name='Heading')
        self.speed = Element(root['speed'][:], frames, name='Speed')
        self.roll = Element(root['roll'][:], frames, name='Roll')
        self.pitch = Element(root['pitch'][:], frames, name='Pitch')
        self.pos = Element(root['pos'][:], frames, name='Position')
        self.distance = Element(root['distance'][:], frames, name='Distance')
        
        relative_distance = root['relative_distance'][:]
        relative_distance_err = root.attrs['relative_distance_err']
        
        if relative_distance_err is None:
            self.relative_distance = None
            self.relative_distance_err = None
        else:
            self.relative_distance = \
                Element(relative_distance, frames, name='Relative_Distance')
            self.relative_distance_err = relative_distance_err
            
        if close_root:
            root.close()

    # define __getitem__, __setitem__, and __delitem__ so DynObj can have
    # a more consistenet interface with Daq
    def __getitem__(self, indx):
        """
        provides dicionary-esque access to the Element Attributes
        """
        if indx == 'Heading':
            return self.heading
        elif indx == 'Speed':
            return self.speed
        elif indx == 'Roll':
            return self.roll
        elif indx == 'Pitch':
            return self.pitch
        elif indx == 'Position':
            return self.position
        elif indx == 'Distance':
            return self.distance
        elif indx == 'Relative_Distance':
            return self.relative_distance
            
    def __setitem__(self, indx, value):
        """
        provides dicionary-esque access to the Element Attributes
        """
        if indx == 'Heading':
            self.heading = value
        elif indx == 'Speed':
            self.speed = value
        elif indx == 'Roll':
            self.roll = value
        elif indx == 'Pitch':
            self.pitch = value
        elif indx == 'Position':
            self.position = value
        elif indx == 'Distance':
            self.distance = value
        elif indx == 'Relative_Distance':
            self.relative_distance = value
            
    def __delitem__(self, indx):
        """
        provides dicionary-esque access to the Element Attributes
        """
        if indx == 'Heading':
            self.heading = None
        elif indx == 'Speed':
            self.speed = None
        elif indx == 'Roll':
            self.roll = None
        elif indx == 'Pitch':
            self.pitch = None
        elif indx == 'Position':
            self.position = None
        elif indx == 'Distance':
            self.distance = None
        elif indx == 'Relative_Distance':
            self.relative_distance = None
