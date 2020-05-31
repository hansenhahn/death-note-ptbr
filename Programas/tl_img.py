#!/usr/bin/env python
# -*- coding: windows-1252 -*-
'''
Created on 30/05/2020

@author: DiegoHH
'''
from rhFormats import nsbmd
from rhImages import bmp

import struct
import os
import sys
import glob


__title__ = "DEATHNOTE Image Extractor"
__version__ = "1.0"

def scandirs(path):
    files = []
    for currentFile in glob.glob( os.path.join(path, '*') ):
        if os.path.isdir(currentFile):
            files += scandirs(currentFile)
        else:
            files.append(currentFile)
    return files

def unpack( src, dst ):
    files = filter(lambda x: x.__contains__('.nsbmd'), scandirs(src))
    
    for _, fname in enumerate(files):
        print fname
        
        try:
            path = fname[len(src):]
            fdirs = dst + path[:-len(os.path.basename(path))]
            if not os.path.isdir(fdirs):
                os.makedirs(fdirs)       
        
            with open(fname, "rb") as fd:
                c = nsbmd.NsbmdFormat(fd)
                tex = c.read_textures()
                for t in tex:
                    print t
                    buffer = []
                    for y, line in enumerate(t.texture):
                        temp = []
                        for x, pixel in enumerate(line):
                            temp.append( (pixel[0],pixel[1],pixel[2]) ) 
                        buffer.append(temp)             

                    with open( fdirs + os.path.basename(path) + '.bmp', 'wb') as o:
                        p = bmp.Writer(len(t.texture[0]), len(t.texture)  ,24)
                        p.write(o, buffer)
        except:
            print "error!"
            

if __name__ == "__main__":

    import argparse
    
    os.chdir( sys.path[0] )
    #os.system( 'cls' )

    print "{0:{fill}{align}70}".format( " {0} {1} ".format( __title__, __version__ ) , align = "^" , fill = "=" )

    parser = argparse.ArgumentParser()
    parser.add_argument( '-s', dest = "src", type = str, nargs = "?", required = True )
    parser.add_argument( '-d', dest = "dst", type = str, nargs = "?", required = True )
    
    args = parser.parse_args()
    
    print "Unpacking images"           
    unpack( args.src , args.dst )

    sys.exit(1)