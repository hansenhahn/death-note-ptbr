#!/usr/bin/env python
# -*- coding: utf-8 -*-

# formats/nclr.py

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

''' NCLR - Nitro CoLour Resource '''

import array
import exceptions
import struct

__author__ = "Diego Hansen Hahn"
__version__ = "1.0"

from math import ceil
def gba2rgb(fd):
    try:
        rgb = struct.unpack('<H', fd.read(2))[0] & 0x7FFF
        rgb = map(lambda x,y: int(ceil(float((x >> y) & 0x1F)/31.0 * 0xFF)), [rgb]*3, [0,5,10])
        return rgb
    except:
        return (0,0,0)
        
def gba2tuple(fd):
    rgb = struct.unpack('<H', fd.read(2))[0] & 0x7FFF
    rgb = map(lambda x,y: int(float((x >> y) & 0x1F)/31.0 * 255.0), [rgb]*3, [0,5,10])
    return rgb        

class ChunkError(exceptions.Exception):
    def __init__ (self, error):
        setattr(self, "error", error)
    def __str__(self):
        return repr(self.error)

class NCLRFormat(object):

    def __init__(self, data):
        self.base_address = data.tell()
        #data.seek(0,0)
        if data.read(4) == "RLCN":
            setattr(self, "data", data)
        else:
            raise TypeError("File not supported.")

        self.read_chunks()
        self.read_pltt_structure()
        self.read_pcmp_structure()

    def read_chunks(self):
        if not hasattr(self, "data"):
            raise AttributeError()

        chunks = {}
        self.data.seek(self.base_address)
        # NCLR - Nitro CoLour Resource
        stamp = self.data.read(4)
        if stamp == "RLCN":
            chunks.update({"NCLR":{}})
            self.data.read(4) #0100FEFF
            chunks["NCLR"].update({"file_size" : struct.unpack('<L', self.data.read(4))[0]})
            chunks["NCLR"].update({"struct_size" : struct.unpack('<H', self.data.read(2))[0]})
            chunks["NCLR"].update({"total_chunks" : struct.unpack('<H', self.data.read(2))[0]})
        else:
            raise ChunkError("Error with NCLR chunk.")

        chunks_readed = 0

        # PLTT - PaLeTTe
        stamp = self.data.read(4)
        if stamp == "TTLP":
            chunks.update({"PLTT":{}})
            chunks["PLTT"].update({"struct_size" : struct.unpack('<L', self.data.read(4))[0]})
            chunks["PLTT"].update({"bitdepth" : struct.unpack('<L', self.data.read(4))[0]})
            if ( chunks["PLTT"]["bitdepth"] == 3 ):
                chunks["PLTT"].update({"palette_size" : 0x20})
            else:
                chunks["PLTT"].update({"palette_size" : 0x200})
            self.data.read(4) # ?            
            chunks["PLTT"].update({"palette_entries" : (0x10*chunks["PLTT"]["palette_size"] - struct.unpack('<L', self.data.read(4))[0])/chunks["PLTT"]["palette_size"] })
            self.data.read(4) # ?
            chunks["PLTT"].update({"data_address" : self.data.tell()})
        else:
            raise ChunkError("Error with PLTT chunk.")

        chunks_readed += 1
        if chunks_readed == chunks["NCLR"]["total_chunks"]:
            setattr(self, "chunks", chunks)
            return chunks

        self.data.seek( chunks["PLTT"]["data_address"] +  chunks["PLTT"]["palette_size"]*chunks["PLTT"]["palette_entries"] )
        # PCMP - Palette Colour MaP  [Opcional]
        stamp = self.data.read(4)
        if stamp == "PMCP":
            chunks.update({"PCMP":{}})
            chunks["PCMP"].update({"struct_size" : struct.unpack('<L', self.data.read(4))[0]})
            chunks["PCMP"].update({"bank-count" : struct.unpack('<H', self.data.read(2))[0]})
            chunks["PCMP"].update({"unknown_1" : struct.unpack('<H', self.data.read(2))[0]})
            chunks["PCMP"].update({"unknown_2" : struct.unpack('<L', self.data.read(4))[0]})
            chunks["PCMP"].update({"data_address" : self.data.tell()})
            bank_entries = []
            for _ in range( chunks["PCMP"]["bank-count"] ):
                bank_entries.append( struct.unpack('<H', self.data.read(2))[0] )
            chunks["PCMP"].update({"bank-entries" : bank_entries})
        else:
            raise ChunkError("Error with PCMP chunk.")

        chunks_readed += 1
        if chunks_readed == chunks["NCLR"]["total_chunks"]:
            setattr(self, "chunks", chunks)
            return chunks

    def read_pltt_structure(self):

        # WIP
        self.data.seek(self.chunks["PLTT"]["data_address"], 0)
        pltt = [ [] for _ in range(16)]
        if ( self.chunks["PLTT"]["bitdepth"] == 3 ):
            for i, y in enumerate(range(self.chunks["PLTT"]["palette_entries"])):
                bank = self.chunks["PCMP"]["bank-entries"][i]
                for x in range(16):
                    pltt[bank].append(gba2tuple(self.data))
        
        else:
            for i, y in enumerate(range(self.chunks["PLTT"]["palette_entries"])):
                bank = self.chunks["PCMP"]["bank-entries"][i]
                for x in range(256):
                    pltt[bank].append(gba2tuple(self.data))
                
        setattr(self, "palette_data", pltt)

        return pltt

    def read_pcmp_structure(self):
        return
