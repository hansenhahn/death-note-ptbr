#!/usr/bin/env python
# -*- coding: utf-8 -*-

# formats/ncgr.py

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

''' Nintendo Character Graphic Resource '''

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

class NCGRFormat(object):

    def __init__(self, data):
        self.base_addr = data.tell()
    
        #data.seek(0,0)
        if data.read(4) == "RGCN":
            setattr(self, "data", data)
        else:
            raise TypeError("File not supported.")

        self.read_chunks()
        self.read_char_structure()

    def read_chunks(self):
        if not hasattr(self, "data"):
            raise AttributeError()

        chunks = {}
        self.data.seek(self.base_addr)
        # NCLR - Nitro Character Graphic Resource
        stamp = self.data.read(4)
        if stamp == "RGCN":
            chunks.update({"NCGR":{}})
            self.data.read(4) #0100FEFF
            chunks["NCGR"].update({"file_size" : struct.unpack('<L', self.data.read(4))[0]})
            chunks["NCGR"].update({"struct_size" : struct.unpack('<H', self.data.read(2))[0]})
            chunks["NCGR"].update({"total_chunks" : struct.unpack('<H', self.data.read(2))[0]})
        else:
            raise ChunkError("Error with NCGR chunk.")

        chunks_readed = 0

        # CHAR - CHARacter
        stamp = self.data.read(4)
        if stamp == "RAHC":
            chunks.update({"CHAR":{}})
            chunks["CHAR"].update({"struct_size" : struct.unpack('<L', self.data.read(4))[0]})
            chunks["CHAR"].update({"unknown_3" : struct.unpack('<H', self.data.read(2))[0]})
            chunks["CHAR"].update({"unknown_4" : struct.unpack('<H', self.data.read(2))[0]})
            chunks["CHAR"].update({"bitdepth" : struct.unpack('<L', self.data.read(4))[0]})
            # Não tenho certeza
            chunks["CHAR"].update({"tiles_per_char" : struct.unpack('<H', self.data.read(2))[0]}) # <= ?
            chunks["CHAR"].update({"bytes_per_tile" : struct.unpack('<H', self.data.read(2))[0]}) # <= ?
            # ~~~~
            chunks["CHAR"].update({"unknown_1" : struct.unpack('<L', self.data.read(4))[0]})
            chunks["CHAR"].update({"data_size" : struct.unpack('<L', self.data.read(4))[0]})
            chunks["CHAR"].update({"unknown_2" : struct.unpack('<L', self.data.read(4))[0]})
            chunks["CHAR"].update({"data_address" : self.data.tell()})
        else:
            raise ChunkError("Error with CHAR chunk.")

        chunks_readed += 1
        if chunks_readed == chunks["NCGR"]["total_chunks"]:
            setattr(self, "chunks", chunks)
            return chunks

        # Adicionar tratamento
        # chunk CPOS
        self.data.seek(chunks["CHAR"]["data_address"] + chunks["CHAR"]["data_size"], 0)
        stamp = self.data.read(4)


        chunks_readed += 1
        if chunks_readed == chunks["NCGR"]["total_chunks"]:
            setattr(self, "chunks", chunks)
            return chunks
        else:
            raise ChunkError("Missing chunks.")

    def read_char_structure(self):
        if not hasattr(self, "chunks"):
            self.read_chunks()

        # Dúvida
        count = self.chunks["CHAR"]["data_size"]/(8 * 2**(self.chunks["CHAR"]["bitdepth"] - 1))

        bitdepth = 2**(self.chunks["CHAR"]["bitdepth"] - 1)
        if bitdepth < 8:
            sample = 8/bitdepth
            mask = 2**bitdepth-1
            shift = [x * bitdepth for x in range(sample)]

        self.data.seek(self.chunks["CHAR"]["data_address"], 0)
        #print hex(self.data.tell())

        char_data = []
        raw_data = ""
        for x in range(count):
            tile = []
            # Dúvida
            tile_data = self.data.read(8 * 2**(self.chunks["CHAR"]["bitdepth"] - 1))
            row = []
            for s in tile_data:
                c = struct.unpack('B', s)[0]
                if bitdepth < 8:
                    for i in shift:
                        row.append(mask & (c >> i))
                        if len(row) == 8:
                            tile.append(row)
                            row = []
                else:
                    row.append(c)
                    if len(row) == 8:
                        tile.append(row)
                        row = []
            raw_data += tile_data
            char_data.append(tile)

        #char_data.append([[0,0,0,0,0,0,0,0] for x in range(8)])
        setattr(self, "raw_data", raw_data)
        setattr(self, "char_data", char_data)
        return char_data



