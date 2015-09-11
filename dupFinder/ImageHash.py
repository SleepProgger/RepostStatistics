from PIL import Image
from itertools import imap
import operator
#from Timing import funcHook, printTimings 
import struct

# This cast to signed ints is ugly as fuck and also dangerous. TODO: Fix this.
def to64BitSigInts(bits):
    return tuple(struct.unpack("q", struct.pack("Q", int(bits[i:i+64], 2)))[0] for i in xrange(0, len(bits), 64))

def hamming_distance_str(strA, strB):
    return sum(imap(operator.ne, strA, strB))
def hamming_distance_(strA, strB):
    return sum(imap(operator.ne, bin(strA), bin(strB)))
#def hamming_distance(numA, numB):
    #a = struct.unpack("q", struct.pack("Q", ulong))[0]
    #bin(numA^(numB)).count("1")
def hamming_distance(numA, numB):
    return bin(numA^(numB)).count("1")

# http://blog.safariflow.com/2013/11/26/image-hashing-with-python/
def aHash(img, bSize=8):
    #img = Image.open(imageName)
    #img = img.convert("L") # convert to gray
    img  = img.resize((bSize, bSize), Image.ANTIALIAS)
    #img.show()
    pix = img.getdata()
    avg = sum(pix) / (bSize*bSize)
    bits = int("".join(map(lambda x: '1' if x < avg else '0', pix)), 2)
    return bits



def dHash_h(img):
    size = (9, 8)
    img  = img.resize(size, Image.ANTIALIAS)
    pixels = list(img.getdata())
    i = 0
    r = list()
    for y in range(8):
        for x in range(8):
            r.append("1" if pixels[i]<pixels[i+1] else "0")
            i += 1
        i += 1
    return int("".join(r), 2)
    
def dHash_v(img):
    size = (8, 9)
    width, height = size
    img  = img.resize(size, Image.ANTIALIAS)
    pixels = list(img.getdata())
    r = list()
    for y in range(8):
        for x in range(8):
            r.append("1" if pixels[y*width+x] < pixels[(y+1)*width+x] else "0")
    return int("".join(r), 2)
    
    
    
def aHash_256(img):
    #img.show()
    img  = img.resize((16, 16), Image.ANTIALIAS)
    pix = img.getdata()
    avg = sum(pix) / (16*16)
#     img.save('test.png')
#     print list(pix)
#     print avg;
#     print "".join(map(lambda x: '1' if x < avg else '0', pix))
    return to64BitSigInts("".join(map(lambda x: '1' if x < avg else '0', pix)))

def dHash_256_h(img):
    size = (17, 16)
    img  = img.resize(size, Image.ANTIALIAS)
    pixels = list(img.getdata())
    i = 0
    r = list()
    for y in range(16):
        for x in range(16):
            r.append("1" if pixels[i]<pixels[i+1] else "0")
            i += 1
        i += 1
    return to64BitSigInts("".join(r))    
    
def dHash_256_v(img):
    size = (16, 17)
    width, height = size
    img  = img.resize(size, Image.ANTIALIAS)
    pixels = list(img.getdata())
    r = list()
    for y in range(16):
        for x in range(16):
            r.append("1" if pixels[y*width+x] < pixels[(y+1)*width+x] else "0")
    return to64BitSigInts("".join(r))

def searchForFiles_(path, extensions=None):
    #print "search in", path
    for root, subFolders, files in os.walk(path):
        root = root.rstrip("/") +"/"
        for fName in files:
            if not extensions or fName.endswith(extensions):
                yield root + fName

import os
def searchForDups(path, extensions=None):
    files = [dict(), dict(), dict()]
    #i = 0
    for fname in searchForFiles_(path, extensions):
        #if i > 100: break
        #i+=1
        
        #full = path + file
        #print full
        #if os.path.isfile(full) and (extensions and file.endswith(extensions)):
        try:
            img = Image.open(fname)
            img = img.convert("L") # convert to gray
        except Exception as e:
            print "EXCEPTION:", e
            continue
        hashes = (aHash_256(img), dHash_256_h(img), dHash_256_v(img))
        #print full, hex(h), hex(h2), hex(h3)
        for i in range(3):
            if hashes[i] in files[i]:
                print "DUP: ", i, fname, files[i][hashes[i]]
                files[i][hashes[i]].append(fname)
            else:
                files[i][hashes[i]] = [fname]
                    
if __name__ == '__main__':   
    searchForDups("res/", ("jpg", "jpeg", "bmp", "png"))    
    
