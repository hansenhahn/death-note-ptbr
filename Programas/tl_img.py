#!/usr/bin/env python
# -*- coding: windows-1252 -*-
'''
Created on 30/05/2020

@author: DiegoHH
'''
from rhFormats import nsbmd, nclr, ncgr, ncer
from rhImages import bmp, images

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

SHAPE_SIZE = [[( 8, 8),(16,16),(32,32),(64,64)],  # 0
              [(16, 8),(32, 8),(32,16),(64,32)],  # 1
              [( 8,16),( 8,32),(16,32),(32,64)]]  # 2
            
def unpack2d( src, dst ):
    files = filter(lambda x: x.__contains__('.xap'), scandirs(src))
    files = zip(*[iter(files)]*2)
    try:
        for _, fnames in enumerate(files):               
            file_a = fnames[0]
            file_g = fnames[1]
            
            path = file_g[len(src):]
            fdirs = dst + path[:-len(os.path.basename(path))]
            if not os.path.isdir(fdirs):
                os.makedirs(fdirs)    
            
            ifds = [open(name, "rb") for name in fnames]
            data = {}
                
            for ifd in ifds:
                stamp = ifd.read(4)
                assert stamp == "XapA"
                
                entries = struct.unpack("<H", ifd.read(2))[0]
                ifd.read(2)     # 0004
                ifd.read(4)     # 0000 0000 padding?
                link_dat = struct.unpack("<L", ifd.read(4))[0]
                
                for _ in range(entries):
                    stamp = ifd.read(4)     
                    size = struct.unpack("<L", ifd.read(4))[0]
                    ifd.read(4)
                    link = struct.unpack("<L", ifd.read(4))[0]
                    data.update({stamp:(ifd,size,link)})
            
            # Colormap
            if ("LCN0" in data) and ("GCN0" in data) and ("ECN0" in data):
                print "GCN0 found > ", data["GCN0"][0].name 
                print "LCN0 found > ", data["LCN0"][0].name
                print "ECN0 found > ", data["ECN0"][0].name  
                fd = data["LCN0"][0]
                fd.seek(data["LCN0"][2])
                color = nclr.NCLRFormat(fd)
                
                fd = data["GCN0"][0]
                fd.seek(data["GCN0"][2]) 
                tiles = ncgr.NCGRFormat(fd)
                
                fd = data["ECN0"][0]
                fd.seek(data["ECN0"][2])
                attrs = ncer.NCERFormat(fd)
                
                for i, banks in enumerate(attrs.cebk_sprite_attr):
                    for j, attr in enumerate(banks):
                            # Ver GBATek: 2D_BitmapVramAddress = (TileNo AND MaskX)*10h + (TileNo AND NOT MaskX)*80h
                            pos = attr[2].tile_number*0x80
                            path = os.path.join(fdirs, os.path.basename(data["GCN0"][0].name) + '_%03d_%03d.bmp')
                            
                            w = SHAPE_SIZE[attr[0].obj_shape][attr[1].obj_size][0]
                            h = SHAPE_SIZE[attr[0].obj_shape][attr[1].obj_size][1]   

                            output = open(path % (i,j), 'wb')
                            if ( tiles.chunks["CHAR"]["bitdepth"] == 3 ):
                                a = images.Writer( (w,h), color.palette_data[attr[2].palette_number], 4, 1 )
                                a.write(output, tiles.raw_data[pos:(pos+w*h/2)], 4, "BMP")
                            else:
                                a = images.Writer( (w,h), color.palette_data[attr[2].palette_number], 8, 1 )
                                a.write(output, tiles.raw_data[pos:(pos+w*h)], 8, "BMP")
                                                            
                            output.close()
        # 
        if "NAN0" in data:
            print "NAN0 found > ", data["NAN0"][0].name   

        if "CMN0" in data:
            print "CMN0 found > ", data["CMN0"][0].name   

        if "AMN0" in data:
            print "AMN0 found > ", data["AMN0"][0].name 
                
        map(lambda x: x.close(), ifds)
                    
    except:
        print "error!"            
    
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

                path = fname[len(src):]
                fdirs = dst + path[:-len(os.path.basename(path))]
                if not os.path.isdir(fdirs):
                    os.makedirs(fdirs)       
            
                with open(fname, "rb") as fd:
                    c = nsbmd.NsbmdFormat(fd)
                    tex = c.read_textures()
                    
                    print "NSBMD found > ", fd.name
                    
                    with open( fdirs + os.path.basename(path) + '.bmp', 'wb') as o:
                        # Codecs indexados padrao
                        if tex[0].parsed_parameters[2] in (2,3,4):                              
                            if tex[0].parsed_parameters[2] == 2:
                                    p = bmp.Writer(len(tex[0].texture_raw[0]), len(tex[0].texture_raw), 2, palette = tex[0].palette)
                                    p.write(o, tex[0].texture_raw) 
                            elif tex[0].parsed_parameters[2] == 3:
                                    p = bmp.Writer(len(tex[0].texture_raw[0]), len(tex[0].texture_raw), 4, palette = tex[0].palette)
                                    p.write(o, tex[0].texture_raw)   
                            elif tex[0].parsed_parameters[2] == 4:
                                    p = bmp.Writer(len(tex[0].texture_raw[0]), len(tex[0].texture_raw), 8, palette = tex[0].palette)
                                    p.write(o, tex[0].texture_raw)                                           
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
    parser.add_argument( '-d', dest = "dst", type = str, nargs = "?", required = True )
    parser.add_argument( '-m', dest = "mode", type = str, nargs = "?", required = True )
    
    args = parser.parse_args()
    
    if ( args.mode == "u3d" ):
        print "Unpacking images"           
        unpack3d( args.src , args.dst )
    elif ( args.mode == "u2d" ):
        unpack2d( args.src, args.dst )
    elif ( args.mode == "p3d" ):
        pack3d( args.src, args.dst )

    sys.exit(1)