#!/usr/bin/env python
# -*- coding: utf-8 -*-

# formats/nsbmd.py

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

import array
import exceptions
import struct

#from OpenGL.GL import *

__author__ = "Diego Hansen Hahn"
__version__ = "1.0"

def signed_float(int, size, frac):
    # int  <= inteiro com sinal do tipo ponto fixo
    # size <= tamanho em bits do inteiro
    # frac <= tamanho em bits da parte fracionária
    if (int & (0x1 << (size - 1))):
        int = int - (1 << size)
    return float(int) / (1 << frac)
    
from math import ceil
def gba2rgb(fd):
    #try:
        rgb = struct.unpack('<H', fd.read(2))[0] & 0x7FFF
        rgb = map(lambda x,y: int(ceil(float((x >> y) & 0x1F)/31.0 * 0xFF)), [rgb]*3, [0,5,10])
        return rgb
    # except:
        # return [0,0,0]

class ChunkError(exceptions.Exception):
    def __init__ (self, error):
        setattr(self, "error", error)
    def __str__(self):
        return repr(self.error)
        
class Texture(object):

    def __init__(self):

        pass

    def parse_parameters(self, parameters):
         #======================================================================
         # Repeat in S Direction (0=Freeze last texel-column, 1=Repeat Texture)
         # Repeat in T Direction (0=Freeze last texel-row,    1=Repeat Texture)
         # Flip in S Direction   (0=No, 1=Flip each 2nd Texture) (requires Repeat)
         # Flip in T Direction   (0=No, 1=Flip each 2nd Texture) (requires Repeat)
         #======================================================================
        # Lembrar de adicionar - Hansen
        repeat_s_direction = 0
        repeat_t_direction = 0
        flip_s_direction = 0
        flip_t_direction = 0
        width = 8 << ((parameters & 0x70) >> 4)   # Em pixel
        height = 8 << ((parameters & 0x380) >> 7)  # Em pixel
         #======================================================================
         # Formato 1 - A3I5 Translucent Texture (3bit Alpha, 5bit Color Index)
         # Formato 2 - 4-Color Palette Texture
         # Formato 3 - 16-Color Palette Texture
         # Formato 4 - 256-Color Palette Texture
         # Formato 5 - 4x4-Texel Compressed Texture
         # Formato 6 - A5I3 Translucent Texture (5bit Alpha, 3bit Color Index)
         # Formato 7 - Direct Color Texture
         #======================================================================
        format = (parameters & 0x1C00) >> 10
         # Color 0 of 4/16/256-Color Palettes (0=Displayed, 1=Made Transparent)
        transparent = (parameters & 0x2000) >> 13

        self.parsed_parameters = (width, height, format, transparent)
        return self.parsed_parameters

    def read(self, data):
        bitdepth = (0, 8, 2, 4, 8, 2, 8, 16)[self.parsed_parameters[2]]

        buffer = [[] for x in range(self.parsed_parameters[1])]
        if self.parsed_parameters[2] == 5:
            data.seek(self.data_offset, 0)
            pixmaps = []

            for z in range((self.parsed_parameters[0]*self.parsed_parameters[1]*bitdepth/8) / 4):
                # Faz o parser dos pixmaps primeiro
                pixmap = [[],[],[],[]]
                word = struct.unpack('<L', data.read(4))[0]
                for x in range(4):
                    for y in range(4):
                        pixmap[x].append(int(word & 0x3))
                        word >>= 2
                pixmaps.append(pixmap)

            data.seek(self.info_data_offset, 0)
            palette_information = []

            for x in range(len(pixmaps)):
                info = struct.unpack('<H', data.read(2))[0]
                index = info & 0x3FFF
                mode = (info & 0xC000) >> 14
                palette_information.append((mode, index))

            for x in range(len(pixmaps)):
                pixmap = pixmaps[x]
                info = palette_information[x]
                _colors = []

                data.seek(self.palette_offset + (info[1] << 2), 0)

                for y in range(4):
                    _colors.append(gba2rgb(data))

                # Monta o set de cores do pixmap em questão
                colors = []
                if info[0] == 0:
                    colors.append(_colors[0]+[0xFF])
                    colors.append(_colors[1]+[0xFF])
                    colors.append(_colors[2]+[0xFF])
                    colors.append(_colors[3]+[0x00]) # Adicionar transparência total
                elif info[0] == 1:
                    colors.append(_colors[0]+[0xFF])
                    colors.append(_colors[1]+[0xFF])
                    colors.append(map(lambda x,y : (x+y)/2, _colors[0], _colors[1])+[0xFF])
                    colors.append(_colors[3]+[0x00]) # Adicionar transparência
                elif info[0] == 2:
                    colors.append(_colors[0]+[0xFF])
                    colors.append(_colors[1]+[0xFF])
                    colors.append(_colors[2]+[0xFF])
                    colors.append(_colors[3]+[0xFF])
                elif info[0] == 3:
                    colors.append(_colors[0]+[0xFF])
                    colors.append(_colors[1]+[0xFF])
                    colors.append((map(lambda x,y : (5*x+3*y)/8, _colors[0], _colors[1]))+[0xFF])
                    colors.append((map(lambda x,y : (3*x+5*y)/8, _colors[0], _colors[1]))+[0xFF])

                for h in range(4):
                    for w in range(4):
                        pixmap[h][w] = colors[pixmap[h][w]]


            # Por fim, gera o buffer com a textura montada
            buffer = [[] for t in range(self.parsed_parameters[1])]

            for x in range(self.parsed_parameters[1] / 4):
                for y in range(self.parsed_parameters[0] / 4):
                    pixmap = pixmaps.pop(0)
                    buffer[4*x + 0] += pixmap[0]
                    buffer[4*x + 1] += pixmap[1]
                    buffer[4*x + 2] += pixmap[2]
                    buffer[4*x + 3] += pixmap[3]

            setattr(self, "texture", buffer)
            return buffer

        elif self.parsed_parameters[2] in (2, 3, 4):
            data.seek(self.data_offset, 0)

            if bitdepth < 8:
                sample = 8/bitdepth
                mask = 2**bitdepth-1
                shift = [x * bitdepth for x in range(sample)]

            buffer = [[] for x in range(self.parsed_parameters[1])]

            # Monta o bitmap indexado
            for x in range(self.parsed_parameters[1]):
                for y in range(self.parsed_parameters[0]/(8/bitdepth)):
                    pixel = struct.unpack('B', data.read(1))[0]
                    if bitdepth < 8:
                        buffer[x] += [mask & (pixel >> i) for i in shift]
                    else:
                        buffer[x].append(pixel)

            # Converte para RGB
            for x in range(self.parsed_parameters[1]):
                for y in range(self.parsed_parameters[0]):
                    data.seek(self.palette_offset + (buffer[x][y] << 1), 0)
                    pixel = gba2rgb(data)
                    if self.parsed_parameters[3] and buffer[x][y] == 0:
                        buffer[x][y] = pixel + [0x00]
                    else:
                        buffer[x][y] = pixel + [0xFF]

            setattr(self, "texture", buffer)
            return buffer
            
        elif ( self.parsed_parameters[2] == 1 ):
            data.seek(self.data_offset, 0)

            buffer = [[] for x in range(self.parsed_parameters[1])]

            # Monta o bitmap indexado
            for x in range(self.parsed_parameters[1]):
                for y in range(self.parsed_parameters[0]):
                    pixel = struct.unpack('B', data.read(1))[0]
                    buffer[x].append(pixel)        
            
            # Converte para RGB
            for x in range(self.parsed_parameters[1]):
                for y in range(self.parsed_parameters[0]):
                    data.seek(self.palette_offset + ( (buffer[x][y] & 0x1f) << 1), 0)
                    pixel = gba2rgb(data)
                    buffer[x][y] = pixel + [ int(((buffer[x][y] & 0xe0) >> 5) * 255.0/7.0)]
                        
            setattr(self, "texture", buffer)
            return buffer

        else:
            raise Exception("Unsupported texture format.")
        # Adicionar o tratamento dos demais formatos

    # def dump_texture(self, filename):
        # if not (Image and ImageDraw):
            # raise ImportError("PIL not found. Check http://www.pythonware.com/library/index.htm.")

        # if not hasattr(self, "texture"):
            # raise AttributeError("Missing texture. See Texture.read() function.")

        # im = Image.new("RGBA", (len(self.texture[0]), len(self.texture)), (0xFF, 0xFF, 0xFF, 0x0))
        # dr = ImageDraw.Draw(im)

        # for y, line in enumerate(self.texture):
            # for x, pixel in enumerate(line):
                # dr.point((x,y), fill = (pixel[0],pixel[1],pixel[2],pixel[3]))

        # im.save(filename, "PNG")
        # return True

class Command(object):
    # INCOMPLETO
    command_dict = {0x20: "COLOR", 0x21:"NORMAL", 0x22:"TEXCOORD",
                    0x23:"VTX_16", 0x24:"VTX_10", 0x25:"VTX_XY", 0x26:"VTX_XZ",
                    0x27:"VTX_YZ", 0x28:"VTX_DIFF",
                    0x40:"BEGIN_VTXS", 0x41:"END_VTXS"}

    def __init__(self, cmd, parameter):
        self.cmd = cmd
        if len(parameter) == 4:
            self.cmd_parameter_1 = struct.unpack('<L', parameter)[0]
            self.cmd_parameter_2 = None
        elif len(parameter) == 8:
            self.cmd_parameter_1 = struct.unpack('<LL', parameter)[0]
            self.cmd_parameter_2 = struct.unpack('<LL', parameter)[1]
        else:
            self.cmd_parameter_1 = None
            self.cmd_parameter_2 = None

        if self.cmd == 0x20:
            r = self.cmd_parameter_1 & 0x31
            g = (self.cmd_parameter_1 >> 5) & 0x31
            b = (self.cmd_parameter_1 >> 10) & 0x31

            r = 0 if (r == 0) else (r*2 + 1)
            g = 0 if (g == 0) else (g*2 + 1)
            b = 0 if (b == 0) else (b*2 + 1)

            self.cmd_parameter = (r, g, b)

        if self.cmd == 0x21:
            x = signed_float(self.cmd_parameter_1 & 0x3FF, 10, 6)
            y = signed_float((self.cmd_parameter_1 >> 10) & 0x3FF, 10, 6)
            z = signed_float((self.cmd_parameter_1 >> 20) & 0x3FF, 10, 6)
            self.cmd_parameter = (x, y, z)

        elif self.cmd == 0x22:
            s = signed_float(self.cmd_parameter_1 & 0xFFFF, 16, 4)
            t = signed_float((self.cmd_parameter_1 >> 16) & 0xFFFF, 16, 4)
            self.cmd_parameter = (s, t)

        elif self.cmd == 0x23:
            x = signed_float(self.cmd_parameter_1 & 0xFFFF, 16, 12)
            y = signed_float((self.cmd_parameter_1 >> 16) & 0xFFFF, 16, 12)
            z = signed_float(self.cmd_parameter_2 & 0xFFFF, 16, 12)
            self.cmd_parameter = (x, y, z)

        elif self.cmd == 0x24:
            x = signed_float(self.cmd_parameter_1 & 0x3FF, 10, 6)
            y = signed_float((self.cmd_parameter_1 >> 10) & 0x3FF, 10, 6)
            z = signed_float((self.cmd_parameter_1 >> 20) & 0x3FF, 10, 6)
            self.cmd_parameter = (x, y, z)

        elif self.cmd == 0x25:
            x = signed_float(self.cmd_parameter_1 & 0xFFFF, 16, 12)
            y = signed_float((self.cmd_parameter_1 >> 16) & 0xFFFF, 16, 12)
            z = "eq"
            self.cmd_parameter = (x, y, z)

        elif self.cmd == 0x26:
            x = signed_float(self.cmd_parameter_1 & 0xFFFF, 16, 12)
            y = "eq"
            z = signed_float((self.cmd_parameter_1 >> 16) & 0xFFFF, 16, 12)
            self.cmd_parameter = (x, y, z)

        elif self.cmd == 0x27:
            x = "eq"
            y = signed_float(self.cmd_parameter_1 & 0xFFFF, 16, 12)
            z = signed_float((self.cmd_parameter_1 >> 16) & 0xFFFF, 16, 12)
            self.cmd_parameter = (x, y, z)

        elif self.cmd == 0x28:
            x = signed_float(self.cmd_parameter_1 & 0x3FF, 10, 9) / 8
            y = signed_float((self.cmd_parameter_1 >> 10) & 0x3FF, 10, 9) / 8
            z = signed_float((self.cmd_parameter_1 >> 20) & 0x3FF, 10, 9) / 8
            self.cmd_parameter = (x, y, z)

        elif self.cmd == 0x40:
            self.cmd_parameter = ("GL_TRIANGLES", "GL_QUADS", "GL_TRIANGLE_STRIP", "GL_QUAD_STRIP")[self.cmd_parameter_1]

        else:
            self.cmd_parameter = None

    def __str__(self):
        cmd = Command.command_dict.get(self.cmd, "Unknown Command")

        if self.cmd in (0x21, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28):
            return '''[%02X] %10s  (X = %s, Y = %s, Z = %s)''' % (self.cmd, cmd,
                                                                self.cmd_parameter[0],
                                                                self.cmd_parameter[1],
                                                                self.cmd_parameter[2])
        elif self.cmd in (0x22,):
            return '''[%02X] %10s  (S = %s, T = %s)''' % (self.cmd, cmd,
                                                        self.cmd_parameter[0],
                                                        self.cmd_parameter[1])
        elif self.cmd in (0x20,):
            return '''[%02X] %10s  (R = %s, G = %s, B = %s)''' % (self.cmd, cmd,
                                                                self.cmd_parameter[0],
                                                                self.cmd_parameter[1],
                                                                self.cmd_parameter[2])
        elif self.cmd in (0x40,):
            return '''[%02X] %10s  (Type = %s)''' %(self.cmd, cmd,
                                                  self.cmd_parameter)
        elif self.cmd in (0x41,):
            return '''[%02X] %10s  (Sem Parâmetros)''' %(self.cmd, cmd)
        else:
            return '''[%02X] %10s  (Unkown Parameter)''' % (self.cmd, cmd)


class Model(object):
    def __init__(self):
        self.offset = 0
        self.name = None

        self.polygons = []

    def __str__(self):
        return '''%s %s''' % (self.name, hex(self.offset))

    def append(self, polygon):
        self.polygons.append(polygon)

    def __iter__(self):
        for polygon in self.polygons:
            yield polygon

class Polygon(object):
    def __init__(self, address, size):

        self.address = address
        self.size = size

    def read_geometry(self, data):
        data.seek(self.address, 0)

        self.geometry_commands = []

        while True:
            packed_cmd = struct.unpack('BBBB', data.read(4))
            self.size -= 4

            for i, cmd in enumerate(packed_cmd):
                if cmd == 0:
                    break
                elif cmd == 0x40: # Deve começar com este comando
                    vtx_list = []
                    vtx_list.append(Command(cmd, data.read(4)))
                    self.size -= 4
                elif cmd == 0x41: # E terminar com este comando
                    vtx_list.append(Command(cmd, ''))
                    self.geometry_commands.append(vtx_list)
                    if i == 3:
                        self.size -= len(data.read(4))
                elif cmd == 0x23:
                    vtx_list.append(Command(cmd, data.read(8)))
                    self.size -= 8
                else:
                    vtx_list.append(Command(cmd, data.read(4)))
                    self.size -= 4

            if self.size == 0:
                break

        return self.geometry_commands


class NsbmdFormat(object):
    def __init__(self, data):
        data.seek(0,0)
        if data.read(4) == "BMD0":
            setattr(self, "data", data)
        else:
            raise TypeError("File not supported.")

        self.read_chunks()
        self.read_models()

    def read_chunks(self):
        if not hasattr(self, "data"):
            raise AttributeError()

        chunks = {}
        self.data.seek(0,0)
        # BMD0
        stamp = self.data.read(4)
        if stamp == "BMD0":
            chunks.update({"BMD0":{}})
            self.data.read(4) #0002FEFF
            chunks["BMD0"].update({"file_size" : struct.unpack('<L', self.data.read(4))[0]})
            chunks["BMD0"].update({"struct_size" : struct.unpack('<H', self.data.read(2))[0]})
            chunks["BMD0"].update({"total_chunks" : struct.unpack('<H', self.data.read(2))[0]})
            chunks["BMD0"].update({"chunk_address" : [struct.unpack('<L', self.data.read(4))[0] for _ in range(chunks["BMD0"]["total_chunks"])]})
        else:
            raise ChunkError("Error with BMD0 chunk.")

        chunks_readed = 0

        for addr in chunks["BMD0"]["chunk_address"]:
            self.data.seek(addr,0)
            stamp = self.data.read(4)
            if stamp == "MDL0":
                chunks.update({"MDL0-offset":addr})
                chunks.update({"MDL0":{}})
                chunks["MDL0"].update({"struct_size" : struct.unpack('<L', self.data.read(4))[0]})
                self.data.read(1)
                chunks["MDL0"].update({"object_count" : struct.unpack('B', self.data.read(1))[0]})
                chunks["MDL0"].update({"header_size" : struct.unpack('<H', self.data.read(2))[0]})
                chunks["MDL0"].update({"data_size" : struct.unpack('<H', self.data.read(2))[0]})
                chunks["MDL0"].update({"block_size" : struct.unpack('<H', self.data.read(2))[0]})
                chunks["MDL0"].update({"unknown_1" : struct.unpack('<L', self.data.read(4))[0]})
                self.data.read(4 * chunks["MDL0"]["object_count"]) # Não serve mesmo pra nada?
                self.data.read(4) # ??
                models = [Model() for x in range(chunks["MDL0"]["object_count"])]
                for model in models:
                    model.offset = struct.unpack('<L', self.data.read(4))[0]
                for model in models:
                    model.name = self.data.read(16)
            elif stamp == "TEX0":
                chunks.update({"TEX0-offset":addr})
                chunks.update({"TEX0":{}})
                chunks["TEX0"].update({"struct_size": struct.unpack('<L', self.data.read(4))[0]})
                self.data.read(4)
                chunks["TEX0"].update({"tex_data_size": struct.unpack('<H', self.data.read(2))[0] << 3})
                chunks["TEX0"].update({"tex_info_offset": struct.unpack('<H', self.data.read(2))[0]})
                self.data.read(4)
                chunks["TEX0"].update({"tex_data_offset": struct.unpack('<L', self.data.read(4))[0]})
                self.data.read(4)
                chunks["TEX0"].update({"ctex_data_size": struct.unpack('<H', self.data.read(2))[0] << 3})
                chunks["TEX0"].update({"ctex_info_offset": struct.unpack('<H', self.data.read(2))[0]})
                self.data.read(4)
                chunks["TEX0"].update({"ctex_data_offset": struct.unpack('<L', self.data.read(4))[0]})
                chunks["TEX0"].update({"ctex_info_data_offset": struct.unpack('<L', self.data.read(4))[0]})
                self.data.read(4)
                chunks["TEX0"].update({"palette_data_size": struct.unpack('<L', self.data.read(4))[0] << 3})
                chunks["TEX0"].update({"palette_info_offset": struct.unpack('<L', self.data.read(4))[0]})
                chunks["TEX0"].update({"palette_data_offset": struct.unpack('<L', self.data.read(4))[0]})

        setattr(self, "chunks", chunks)
        setattr(self, "models", models)

    def read_models(self):
        for model in self.models:
            self.data.seek(self.chunks["MDL0-offset"] + model.offset, 0)
            setattr(model, "size", struct.unpack('<L', self.data.read(4))[0])
            setattr(model, "bones_offset", struct.unpack('<L', self.data.read(4))[0])
            setattr(model, "materials_offset", struct.unpack('<L', self.data.read(4))[0])
            setattr(model, "polygons_start", struct.unpack('<L', self.data.read(4))[0])
            setattr(model, "polygons_end", struct.unpack('<L', self.data.read(4))[0])

            self.read_polygons(model)

        return self.models

    def read_polygons(self, model):
        self.data.seek(self.chunks["MDL0-offset"] + model.offset + model.polygons_start)
        # Lendo o header
        self.data.read(1)
        setattr(model, "polygon_count", struct.unpack('B', self.data.read(1))[0])
        size = struct.unpack('<H', self.data.read(2))[0] # Constante??

        # Continuar...
        self.data.seek(size - 4, 1)

        address = self.data.tell()
        # Lendo as definições dos polígonos...
        # Criar um objeto só pra isso?
        for i in range(model.polygon_count):
            address = self.data.tell()
            self.data.read(8)
            paddr = struct.unpack('<L', self.data.read(4))[0] + address
            psize = struct.unpack('<L', self.data.read(4))[0]
            link = self.data.tell()
            p = Polygon(paddr, psize)
            p.read_geometry(self.data)
            model.append(p)
            self.data.seek(link)

        return model
        
    def read_textures(self):
        # Textures Info Section
        self.data.seek(self.chunks["TEX0-offset"] + self.chunks["TEX0"]["tex_info_offset"])
        self.data.read(1)
        count = struct.unpack('B', self.data.read(1))[0]
        size = struct.unpack('<H', self.data.read(2))[0]
        self.data.read(4) # Guardar esses valores?
        self.data.read(4) # 0000017F
        self.data.read(4 * count)
        self.data.read(4)

        textures = [Texture() for x in range(count)]
        for texture in textures:
            offset = struct.unpack('<H', self.data.read(2))[0] << 3
            parameters = struct.unpack('<H', self.data.read(2))[0]
            parameters = texture.parse_parameters(parameters)
            # Formato:
            if parameters[2] == 5:
                setattr(texture, "data_offset", self.chunks["TEX0-offset"] + self.chunks["TEX0"]["ctex_data_offset"] + offset)
                setattr(texture, "info_data_offset", self.chunks["TEX0-offset"] + self.chunks["TEX0"]["ctex_info_data_offset"] + (offset >> 1))
            else:
                setattr(texture, "data_offset", self.chunks["TEX0-offset"] + self.chunks["TEX0"]["tex_data_offset"] + offset)

            # Não sei direito o que significam
            self.data.read(1)
            self.data.read(1)
            self.data.read(1)
            self.data.read(1)

        for texture in textures:
            setattr(texture, "name", self.data.read(16).replace("\x00", ""))

        # Palette Info Section
        self.data.seek(self.chunks["TEX0-offset"] + self.chunks["TEX0"]["palette_info_offset"])
        self.data.read(1)
        count = struct.unpack('B', self.data.read(1))[0]
        size = struct.unpack('<H', self.data.read(2))[0]
        self.data.read(4) # Guardar esses valores?
        self.data.read(4) # 0000017F
        self.data.read(4 * count)
        self.data.read(4)

        palettes_offset = []
        for texture in textures:
            offset = struct.unpack('<L', self.data.read(4))[0] << 3
            setattr(texture, "palette_offset", (self.chunks["TEX0-offset"] + self.chunks["TEX0"]["palette_data_offset"] + offset))
        for texture in textures:
            setattr(texture, "palette_name", self.data.read(16).replace("\x00", ""))

        for texture in textures:
            texture.read(self.data)

        setattr(self, "textures", textures)
        return self.textures


