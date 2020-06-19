#!/usr/bin/env python
# -*- coding: utf-8 -*-

# formats/ncer.py

# Copyright 2010/11 Diego Hansen Hahn (aka DiegoHH) <diegohh90 [at] hotmail [dot] com>

# Nitro VieWeR is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License.

# Nitro VieWeR is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Nitro VieWeR. If not, see <http://www.gnu.org/licenses/>.

''' Nintendo CEll Resource '''

import array
import exceptions
import struct

__author__ = "Diego Hansen Hahn"
__version__ = "1.0"

class ChunkError(exceptions.Exception):
    def __init__ (self, error):
        setattr(self, "error", error)
    def __str__(self):
        return repr(self.error)

class ObjAttr0(object):
    def __init__(self, attr):
        attr = struct.unpack('<H', attr)[0]
        self.ycoord = attr & 0xFF
        self.rotation = (attr & 0x100) >> 8
        self.double_size = (attr & 0x200) >> 9
        self.obj_disabled = (attr & 0x200) >> 9
        self.obj_mode = (attr & 0xC00) >> 10
        self.obj_mosaic = (attr & 0x1000) >> 12
        self.obj_colors = (attr & 0x2000) >> 13
        self.obj_shape = (attr & 0xC000) >> 14

    def __str__(self):
        return '''\
- Attr0 -
Y-Coordinate: %s (%s)
Rotation/Scaling Flag: %s
Double-Size Flag (see Attr0): %s
OBJ Disable (see Attr0): %s
OBJ Mode: %s
OBJ Mosaic: %s
OBJ Colors: %s
OBJ Shape: %s
''' % (self.ycoord, hex(self.ycoord), self.rotation, self.double_size, self.obj_disabled,
       self.obj_mode, self.obj_mosaic, self.obj_colors, self.obj_shape)

class ObjAttr1(object):
    def __init__(self, attr):
        attr = struct.unpack('<H', attr)[0]
        self.xcoord = attr & 0x1FF
        # Se rotation estiver setado - Attr0
        self.rotation_parameter =  (attr & 0x3E00) >> 9
        # Se rotation não estiver setado
        self.h_flip = (attr & 0x1000) >> 12
        self.v_flip = (attr & 0x2000) >> 13
        self.obj_size = (attr & 0xC000) >> 14

    def __str__(self):
        return '''\
- Attr1 -
X-Coordinate: %s (%s)
Rotation/Scaling Parameter (see Attr0): %s
Horizontal Flip (see Attr0): %s
Vertical Flip (see Attr0): %s
OBJ Size: %s
''' % (self.xcoord, hex(self.xcoord), self.rotation_parameter, self.h_flip,
       self.v_flip, self.obj_size)

class ObjAttr2(object):
    def __init__(self, attr):
        attr = struct.unpack('<H', attr)[0]
        self.tile_number = attr & 0x3FF
        self.priority = (attr & 0xC00) >> 10
        self.palette_number = (attr & 0xE000) >> 12

    def __str__(self):
        return '''\
- Attr2 -
Tile Number: %s
Priority: %s
Palette Number (see Attr0): %s
''' %(self.tile_number, self.priority, self.palette_number)

class NCERFormat(object):

    def __init__(self, data):
        #data.seek(0,0)
        # if data.read(4) == "RECN":
        setattr(self, "data", data)
        # else:
            # raise TypeError("File not supported.")

        self.read_chunks()
        self.read_cebk_structure()

    def read_chunks(self):
        if not hasattr(self, "data"):
            raise AttributeError()

        chunks = {}
        #self.data.seek(0,0)
        # NCLR - Nitro CEll Resource
        stamp = self.data.read(4)
        if stamp == "RECN":
            chunks.update({"NCER":{}})
            self.data.read(4) #0100FEFF
            chunks["NCER"].update({"file_size" : struct.unpack('<L', self.data.read(4))[0]})
            chunks["NCER"].update({"struct_size" : struct.unpack('<H', self.data.read(2))[0]})
            chunks["NCER"].update({"total_chunks" : struct.unpack('<H', self.data.read(2))[0]})
        else:
            raise ChunkError("Error with NCER chunk.")

        chunks_readed = 0

        # CEll BanK
        stamp = self.data.read(4)
        if stamp == "KBEC":
            chunks.update({"CEBK":{}})
            chunks["CEBK"].update({"struct_size" : struct.unpack('<L', self.data.read(4))[0]})
            chunks["CEBK"].update({"total_banks" : struct.unpack('<H', self.data.read(2))[0]})
            chunks["CEBK"].update({"type" : struct.unpack('<H', self.data.read(2))[0]})
            chunks["CEBK"].update({"unknown_1" : struct.unpack('<L', self.data.read(4))[0]})
            chunks["CEBK"].update({"multiplier" : struct.unpack('<L', self.data.read(4))[0]})
            chunks["CEBK"].update({"unknown_3" : struct.unpack('<L', self.data.read(4))[0]})
            self.data.read(8) # Padding ??
            chunks["CEBK"].update({"data_address" : self.data.tell()})
        else:
            raise ChunkError("Error with CEBK chunk.")

        chunks_readed += 1
        if chunks_readed == chunks["NCER"]["total_chunks"]:
            setattr(self, "chunks", chunks)
            return chunks

        # Adicionar tratamento das chunks
        # LABL e UEXT
        chunks_readed += 1
        if chunks_readed == chunks["NCER"]["total_chunks"]:
            setattr(self, "chunks", chunks)
            return chunks

        chunks_readed += 1
        if chunks_readed == chunks["NCER"]["total_chunks"]:
            setattr(self, "chunks", chunks)
            return chunks
        else:
            raise ChunkError("Missing chunks.")

    def read_cebk_structure(self):
        if not hasattr(self, "chunks"):
            self.read_chunks()

        cebk_sprite_table = []
        
        self.data.seek(self.chunks["CEBK"]["data_address"], 0)
        for x in range(self.chunks["CEBK"]["total_banks"]):
            objs_number = struct.unpack('<H', self.data.read(2))[0]
            unknown = struct.unpack('<H', self.data.read(2))[0]
            objs_address = struct.unpack('<L', self.data.read(4))[0]
            if self.chunks["CEBK"]["type"] == 1:
                xmaximum = struct.unpack('<H', self.data.read(2))[0]
                ymaximum = struct.unpack('<H', self.data.read(2))[0]
                xminimum = struct.unpack('<H', self.data.read(2))[0] 
                yminimum = struct.unpack('<H', self.data.read(2))[0]    
                #cebk_sprite_table.append((objs_number, unknown, objs_address,xmaximum,ymaximum,xminimum,yminimum))
                cebk_sprite_table.append((objs_number, unknown, objs_address))                
            else:
                cebk_sprite_table.append((objs_number, unknown, objs_address))

        cebk_sprite_attr = []
        for total, y, addr in cebk_sprite_table:
            if self.chunks["CEBK"]["type"] == 1:
                self.data.seek(self.chunks["CEBK"]["data_address"] + self.chunks["CEBK"]["total_banks"]*16 + addr, 0)
            else:
                self.data.seek(self.chunks["CEBK"]["data_address"] + self.chunks["CEBK"]["total_banks"]*8 + addr, 0)
            sprite = []
            for x in range(total):
                sprite.append((ObjAttr0(self.data.read(2)),
                               ObjAttr1(self.data.read(2)),
                               ObjAttr2(self.data.read(2))))
            cebk_sprite_attr.append(sprite)

        setattr(self, "cebk_sprite_table", cebk_sprite_table)
        setattr(self, "cebk_sprite_attr", cebk_sprite_attr)
        return cebk_sprite_attr


