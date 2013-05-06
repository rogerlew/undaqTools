from __future__ import with_statement

# (C) Copyright 2010 by National Advanced Driving Simulator and
# Simulation Center, the University of Iowa and The University of Iowa.
# All rights reserved.
#
# Version: 3.10r
# Authors: Created by Chris Schwarz and others at the NADS
#

'''Command line utility that takes the place of the old convert_daq'''
from pydaqTools import Daq

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", \
        help="The name of the daq file")
    parser.add_argument("-e", "--elements", \
        help="The name of a txt file with a sublist of elements")
    parser.add_argument("-o","--outname", \
        help="The desired name of the output file")
    parser.add_argument("-p","--outpath", \
        help="The path in which to save the output file")
    args = parser.parse_args()
    filename = '20120601154617.daq' # default test file
    elemfile = None
    outname = ''
    outpath = ''
    if args.file:
        filename = args.file
    if args.elements:
        elemfile = args.elements
    if args.outname:
        outname = args.outname
    if args.outpath:
        outpath = args.outpath

    daq = Daq()
    if elemfile is not None:
        daq.load_elemlist_file(elemfile)
    
    daq.read(filename, load_data=True)
    daq.write_mat(outname, outpath, VERBOSE=True)
    
    #from timeit import Timer
    #t = Timer("convert_daq('20120212145024')","from __main__ import test")
    #print t.timeit(1)
    #import cProfile
    #cProfile.run("test('20120212145024')")
    #d=convert_daq('HFCV_DriveB_main_20120611140939','elemListJoel.txt')
