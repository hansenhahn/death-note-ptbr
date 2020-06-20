#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 30/05/2020

@author: DiegoHH
'''
import struct
import os
import sys
import glob
import re
import codecs

__title__ = "DEATHNOTE Text Extractor"
__version__ = "1.0"

BLOCK_TAG = r'^[BLK:(.+?) NU:(.+?) ARG0:(.+?) ARG1:(.+?)]$'
TAG_IN_LINE = r'(<.+?>)'
GET_TAG = r'^<(.+?)>$'

# caracteres acentuados
TAG_TO_SHIFTJIS = { "`A": "\xa6", "'A": "\xa7", "^A": "\xa8", "~A": "\xa9",
          "\"A": "\xaa", "'C": "\xab", "`E": "\xac", "'E": "\xad",
          "^E": "\xae", "~E": "\xaf", "\"E": "\xb0", "`I": "\xb1",
          "'I": "\xb2", "^I": "\xb3", "\"I": "\xb4", "`O": "\xb5",
          "'O": "\xb6", "^O": "\xb7", "~O": "\xb8", "\"O": "\xb9",
          "`U": "\xba", "'U": "\xbb", "~U": "\xbc", "\"U": "\xbd",
          "~N": "\xbe", "\"Y": "\xbf", 
          "`a": "\xc0", "'a": "\xc1", "^a": "\xc2", "~a": "\xc3",
          "\"a": "\xc4", "'c": "\xc5", "`e": "\xc6", "'e": "\xc7",
          "^e": "\xc8", "~e": "\xc9", "\"e": "\xca", "`i": "\xcb",
          "'i": "\xcc", "^i": "\xcd", "\"i": "\xce", "`o": "\xcf",
          "'o": "\xd0", "^o": "\xd1", "~o": "\xd2", "\"o": "\xd3",
          "`u": "\xd4", "'u": "\xd5", "~u": "\xd6", "\"u": "\xd7",
          "~n": "\xd8", "\"y": "\xd9" }
          
UTF8_TO_TAG = [ (u"À", u"`A"),  (u"Á", u"'A"),  (u"Â", u"^A"),  (u"Ã", u"~A"),
          (u"Ä", u"\"A"), (u"Ç", u"'C"),  (u"È", u"`E"),  (u"É", u"'E"),
          (u"Ê", u"^E"),  (u"Ë", u"\"E"), (u"Ì", u"`I"),
          (u"Í", u"'I"),  (u"Î", u"^I"),  (u"Ï", u"\"I"), (u"Ò", u"`O"),
          (u"Ó", u"'O"),  (u"Ô", u"^O"),  (u"Õ", u"~O"),  (u"Ö", u"\"O"),
          (u"Ù", u"`U"),  (u"Ú", u"'U"),  (u"Ü", u"\"U"),
          (u"Ñ", u"~N"),
          (u"à", u"`a"),  (u"á", u"'a"),  (u"â", u"^a"),  (u"ã", u"~a"),
          (u"ä", u"\"a"), (u"ç", u"'c"),  (u"è", u"`e"),  (u"é", u"'e"),
          (u"ê", u"^e"),  (u"ë", u"\"e"), (u"ì", u"`i"),
          (u"í", u"'i"),  (u"î", u"^i"),  (u"ï", u"\"i"), (u"ò", u"`o"),
          (u"ó", u"'o"),  (u"ô", u"^o"),  (u"õ", u"~o"),  (u"ö", u"\"o"),
          (u"ù", u"`u"),  (u"ú", u"'u"),  (u"ü", u"\"u"),
          (u"ñ", u"~n"), ]          


def scandirs(path):
    files = []
    for currentFile in glob.glob( os.path.join(path, '*') ):
        if os.path.isdir(currentFile):
            files += scandirs(currentFile)
        else:
            files.append(currentFile)
    return files
    
def pack( src, dst ):
    
    files = filter(lambda x: x.__contains__('.txt'), scandirs(src))
    
    for _, fname in enumerate(files):
        print fname
        with open( fname , "r" ) as ifd:
            txtblocks = []
            total = 0 
            for line in ifd:  
                line = line.strip( '\r\n' )
                line = codecs.decode(line, "utf-8")
                for c in UTF8_TO_TAG: line = line.replace(c[0], '<'+c[1]+'>')
                line = codecs.encode(line, "cp932")
                
                if line.startswith( '[' ) and line.endswith( ']' ):
                    args = line[1:-1].split(" ")
                    blk = int(args[0].split(":")[1])
                    nu = int(args[1].split(":")[1])
                    arg0 = int(args[2].split(":")[1])
                    arg1 = int(args[3].split(":")[1])
                    if blk >= len(txtblocks):
                        txtblocks.append([])
                    temp = ""
                    total += 1
                    
                elif line == "!****************************!":
                    # fim de bloco
                    temp = temp[:-1]
                    temp += "\x1f\x00"
                    txtblocks[blk].append((arg0,arg1,temp,nu))
                    
                else:    
                    splitted = re.split( TAG_IN_LINE, line )
                    for string in splitted:
                        tag = re.match( GET_TAG, string )
                        # Se não for uma tag, é texto plano
                        if not tag:                     
                            while len(string) > 0:
                                if ((ord(string[0]) >= 0x80 and ord(string[0]) <= 0x9f) or
                                    (ord(string[0]) >= 0xe0 and ord(string[0]) <= 0xff)):
                                    temp += "\x02" + string[0] + string[1]
                                    string = string[2:]
                                else:
                                    temp += string[0]
                                    string = string[1:]
                        else:
                            tag = tag.groups()[0]
                            tag = tag.split(" ")
                            if tag[0] == "color":
                                temp += "\x03" + chr(int(tag[1]))
                            elif tag[0] in TAG_TO_SHIFTJIS:
                                temp += TAG_TO_SHIFTJIS[tag[0]]
                            else:
                                print "Tag error ", tag
                                raise Exception
                            #pass
                    temp += "\x0a" # quebra de linha           
            
            basename = fname[len(src)+1:].replace(".txt", "")
            out = open(os.path.join(dst, basename), "r+b")
            out.write( struct.pack("<L", len(txtblocks)) ) #entradas
            link_entries = out.tell()
            out.seek( len(txtblocks) * 12, 1 )
            link_fat = out.tell()
            out.seek( total * 16, 1 )
            addr1 = []
            for txt in txtblocks:
                addr2 = []
                for t in txt:
                    addr2.append(out.tell())
                    out.write(t[2])
                while (out.tell() % 16): out.seek(1,1)  
                addr1.append(out.tell())                
                for a in addr2:
                    out.write(struct.pack("<L", a))
               
            out.seek( link_fat )
            addr = []
            for i, txt in enumerate(txtblocks):
                addr.append(out.tell())
                a = addr1[i]
                for j, t in enumerate(txt):
                    out.write( struct.pack("<L", t[0]) )
                    out.write( struct.pack("<L", t[3] ))
                    out.write( struct.pack("<L", t[1]) )
                    out.write( struct.pack("<L", a + 4*j) )
                    
            out.seek( link_entries )
            for i, txt in enumerate(txtblocks):
                out.write( struct.pack("<L", len(txt)) )
                #out.write( struct.pack("<L", 0)) # nao sei o que é, entao vou preservar o valor original
                out.seek(4,1)
                out.write( struct.pack("<L", addr[i]) )                
            
            out.close()
        

def unpack( src, dst ):

    files = filter(lambda x: x.__contains__('.bin'), scandirs(src))

    with open( "do_not_delete_3d.log", "w" ) as log:
        for _, fname in enumerate(files):
            try:
                print fname
                path = fname[len(src):]
                fdirs = dst + path[:-len(os.path.basename(path))]
                if not os.path.isdir(fdirs):
                    os.makedirs(fdirs)   
                    
                out = open(fdirs + os.path.basename(path) + '.txt' , "w")
                    
                with open(fname, "rb") as fd:
                    tbl_entries = struct.unpack("<L", fd.read(4))[0]
                    tbl_main  = []
                    for _ in range(tbl_entries):
                        tbl_main.append( struct.unpack("<3L", fd.read(12)) )

                    for j, args in enumerate(tbl_main):
                        entries, _ , ptr = args
                        fd.seek( ptr )
                        tbl_sec = []
                        for x in range(entries):
                            tbl_sec.append(struct.unpack("<4L", fd.read(16)))

                        for i, args in enumerate(tbl_sec):
                            arg0, nu, arg1, ptr2 = args
                            fd.seek( ptr2 )
                            txt_ptr = struct.unpack("<L", fd.read(4))[0]
                        
                            fd.seek( txt_ptr )
                            buffer = ""
                            while True:
                                c = fd.read(1)
                                if c == "\x00":
                                    break
                                elif c == "\x02":
                                    buffer += fd.read(2)
                                elif c == "\x03":
                                    buffer += "<color %d>" % ord(fd.read(1))
                                elif c == "\x1f":
                                    buffer += "\n"
                                else:
                                    buffer += c
                            
                            out.write("[BLK:%d NU:%d ARG0:%d ARG1:%d]\n" % (j, nu, arg0, arg1))
                            out.write( buffer )
                            out.write("!****************************!\n")
                        
                out.close()
                
                out = open(fdirs + os.path.basename(path) + '.txt' , "r")
                data = codecs.decode(out.read(), "cp932")
                out.close()
                
                out = open(fdirs + os.path.basename(path) + '.txt' , "w")
                out.write( codecs.encode(data, "utf-8") )
                out.close()                
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
    
    if ( args.mode == "u" ):
        print "Unpacking texts"           
        unpack( args.src , args.dst )
    elif ( args.mode == "p" ):
        print "Packing texts"
        pack( args.src, args.dst )

    sys.exit(1)