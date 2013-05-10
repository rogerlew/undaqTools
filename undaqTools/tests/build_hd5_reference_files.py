from undaqTools import Daq

if __name__ == '__main__':
    
    for test_file in ['./data/data reduction_20130204125617.daq',
                      './data/Alaska_0_20130301142422.daq']:
        
        hdf5file = test_file[:-4]+'.hdf5'
        
        try:
           with open(hdf5file):
               pass
        except IOError:
           daq = Daq()
           daq.read(test_file)
           daq.write_hd5(hdf5file)
