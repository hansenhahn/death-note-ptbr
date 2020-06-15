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

color_codecs = { 1: "A3I5", 2 : "4-Color", 3 : "16-Color", 4 : "256-Color", 5 : "4x4-Texel", 6 : "A5I3", 7 : "DirectColor" }

def scandirs(path):
    files = []
    for currentFile in glob.glob( os.path.join(path, '*') ):
        if os.path.isdir(currentFile):
            files += scandirs(currentFile)
        else:
            files.append(currentFile)
    return files
    
def pack3d( src, dst ):
    files = filter(lambda x: x.__contains__('.bmp'), scandirs(src))
    
    for _, fname in enumerate(files):
        try:
            print fname 
            basename = fname[len(src)+1:].replace(".bmp", "")
            
            p = bmp.Reader(fname)
            texture_raw = p.read()
            
            with open( os.path.join( dst, basename.replace(".bmp", "") ) , "r+b" ) as ofd:
                c = nsbmd.NsbmdFormat(ofd)
                c.write_textures([texture_raw,])
            
        except:
           print "error!"

    
    

def unpack3d( src, dst ):
    files = filter(lambda x: x.__contains__('.nsbmd'), scandirs(src))
    
    with open( "do_not_delete_3d.log", "w" ) as log:
        for _, fname in enumerate(files):
            try:
                print fname
                path = fname[len(src):]
                fdirs = dst + path[:-len(os.path.basename(path))]
                if not os.path.isdir(fdirs):
                    os.makedirs(fdirs)       
            
                with open(fname, "rb") as fd:
                    c = nsbmd.NsbmdFormat(fd)
                    tex = c.read_textures()
                    with open( fdirs + os.path.basename(path) + '.bmp', 'wb') as o:
                        # Codecs indexados padrao
                        if tex[0].parsed_parameters[2] in (2,3,4):
                            buffer = []
                            for y, line in enumerate(tex[0].texture_raw):
                                temp = []
                                for x, pixel in enumerate(line):
                                    temp.append( pixel ) 
                                buffer.append(temp)   
                                
                            if tex[0].parsed_parameters[2] == 2:
                                    p = bmp.Writer(len(tex[0].texture_raw[0]), len(tex[0].texture_raw), 2, palette = tex[0].palette)
                                    p.write(o, buffer) 
                            elif tex[0].parsed_parameters[2] == 3:
                                    p = bmp.Writer(len(tex[0].texture_raw[0]), len(tex[0].texture_raw), 4, palette = tex[0].palette)
                                    p.write(o, buffer)   
                            elif tex[0].parsed_parameters[2] == 4:
                                    p = bmp.Writer(len(tex[0].texture_raw[0]), len(tex[0].texture_raw), 8, palette = tex[0].palette)
                                    p.write(o, buffer)                                           
                        else:
                            buffer = []
                            for y, line in enumerate(tex[0].texture_rgba):
                                temp = []
                                for x, pixel in enumerate(line):
                                    temp.append( (pixel[0],pixel[1],pixel[2]) ) 
                                buffer.append(temp)                             
                        
                            p = bmp.Writer(len(tex[0].texture_rgba[0]), len(tex[0].texture_rgba)  ,24)
                            p.write(o, buffer)
                        log.write("%s > %s\n" % ( fdirs + os.path.basename(path) + '.bmp' , color_codecs[tex[0].parsed_parameters[2]] ))    
                        
            except:
                print "error!"
            
if __name__ == "__main__":

    import argparse
    
    os.chdir( sys.path[0] )
    #os.system( 'cls' )

    print "{0:{fill}{align}70}".format( " {0} {1} ".format( __title__, __version__ ) , align = "^" , fill = "=" )

    parser = argparse.ArgumentParser()
    parser.add_argument( '-s', dest = "src", type = str, nargs = "?", required = True )
    #parser.add_argument( '-s1', dest = "src1", type = str, nargs = "?", required = False )
    parser.add_argument( '-d', dest = "dst", type = str, nargs = "?", required = True )
    parser.add_argument( '-m', dest = "mode", type = str, nargs = "?", required = True )
    
    args = parser.parse_args()
    
    if ( args.mode == "u3d" ):
        print "Unpacking images"           
        unpack3d( args.src , args.dst )
    elif ( args.mode == "p3d" ):
        pack3d( args.src, args.dst )

    sys.exit(1)