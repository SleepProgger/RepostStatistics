import os
from PIL import Image
from time import time
from database import ImgurDBConnector
import hashlib
import ImageHash
from StringIO import StringIO

#
# TODO:
# Add a "have i seen this before" feature via notify thanks to DeathSummer (done - add credits somewhere ?)
#

def searchForFiles(path, extensions=None):
    #print "search in", path
    for root, subFolders, files in os.walk(path):
        root = root.rstrip("/") +"/"
        for fName in files:
            if not extensions or fName.endswith(extensions):
                yield root + fName

# def to64BitSigInts(bits):
#     return tuple(struct.unpack("q", struct.pack("Q", int(bits[i:i+64], 2)))[0] for i in xrange(0, len(bits), 64))



##########
# hash functions for lsh
def aHash_256b(img):
    #img.show()
    img  = img.resize((16, 16), Image.ANTIALIAS)
    #img.show()
    pix = img.getdata()
    #img.show()
    print list(pix)
    avg = sum(pix) / (16.0*16)
    return list((1 if x < avg else 0) for x in pix)
def dHash_256_hb(img):
    size = (17, 16)
    img  = img.resize(size, Image.ANTIALIAS)
    pixels = list(img.getdata())
    i = 0
    r = list()
    for y in range(16):
        for x in range(16):
            r.append(1 if pixels[i]<pixels[i+1] else 0)
            i += 1
        i += 1
    return r
def dHash_256_vb(img):
    size = (16, 17)
    width, height = size
    img  = img.resize(size, Image.ANTIALIAS)
    pixels = list(img.getdata())
    r = list()
    for y in range(16):
        for x in range(16):
            r.append(1 if pixels[y*width+x] < pixels[(y+1)*width+x] else 0)
    return r
def adhdvHash_256b(img):
    #print aHash_256b(img), dHash_256_hb(img), dHash_256_vb(img)
    return aHash_256b(img)+dHash_256_hb(img)+dHash_256_vb(img)



class ImageDuplicatesLsh(object):
    def __init__(self, imageHashSize=256*3, imageHash=adhdvHash_256b, maxHashDiff=20, lshHashSize=8, hashtableNum=1, storageConfig=None):
        self.hashes = LSHash(lshHashSize, imageHashSize, hashtableNum, storageConfig)
        #self.hashes = LSHash(lshHashSize, imageHashSize, hashtableNum, storageConfig, matrices_filename="test.npz")
        self.maxHashDiff = maxHashDiff
        self.imageHash = imageHash

    def checkImage(self, image):
        d = self.hashes.query(self.imageHash(image), distance_func='hamming')
        return len(d) > 0 and d[0][1] <= self.maxHashDiff
    
    def insertImageHash(self, image, metaData=None):
        self.hashes.index(self.imageHash(image), metaData)
        
    def insertAndCheckImageHash(self, image, metaData=None):
        hash = self.imageHash(image)
        d = self.hashes.query(hash, distance_func='hamming')
        self.hashes.index(hash, metaData)
        return len(d) > 0 and d[0][1] <= self.maxHashDiff
    
    def insertAndGetImageHash(self, image, metaData=None, maxRows=None):
        hash = self.imageHash(image)
        #print hash
        #print len(hash), self.hashes.input_dim
        
        dups = self.hashes.query(hash, num_results=maxRows, distance_func='hamming')
        print dups
        d = tuple(x[0][1] for x in dups if x[1] <= self.maxHashDiff)
        self.hashes.index(hash, metaData)
        return d

    #def insertIfNew(self, image, metadata=None):
        
    def insertHash(self, hash, metaData=None):
        self.hashes.index(hash, metaData)




popcount = lambda n: bin(n).count('1')


# Not sure if anything except newImage() works atm TBH.
# Anyway the idea is to wrap the storage (db/ram/...) and hash creation in this class(es)
# IE: ~ = sim = SimilarImagesSql("somedb")
#         dups = sim.findDups(Image.load("someimage")) ...
class SimilarImagesSql(object):
    # todo setable init / check / hash fucntions
    
    
    def __init__(self, databasename, databaseConnection=None):
        if databaseConnection:
            self.db = databaseConnection
        else:
            self.db = ImgurDBConnector.DBConnector(databasename)
                
        #self.findFirstByCRC = self.db.findFirstByCRC
        #self.findLastByCRC = self.db.findLastByCRC
        
        self.getImageCount = self.db.getImageCount
            

    def newImage(self, image,  similarity=True):
        #print image
        self.crc = hashlib.md5(image).hexdigest()
        
        self.similarity = similarity
        #print self.crc
        
        if similarity:
            img = Image.open(StringIO(image))
            img = img.convert("L") # convert to gray
            self.aHashes = ImageHash.aHash_256(img)
            self.dHashes_h = ImageHash.dHash_256_h(img)
            self.dHashes_v = ImageHash.dHash_256_v(img)
            self.bits = sum(map(popcount, self.aHashes+self.dHashes_h+self.dHashes_v))
            if sum(self.aHashes+self.dHashes_h+self.dHashes_v) == 0:
                raise Exception('Image hash is zero')
        else:
            self.aHashes, self.dHashes_h, self.dHashes_v = ((0,0,0,0), (0,0,0,0), (0,0,0,0))
            self.bits = 0

    def getOneByCrc(self):
        return self.db.findFirstByCRC(self.crc)
    def getOneByAvg(self):
        #print (self.aHashes, self.dHashes_h, self.dHashes_v, self.bits-20, self.bits+20)
        return self.db.findFirstByHash(self.aHashes, self.dHashes_h, self.dHashes_v, self.bits-20, self.bits+20)
    
    
    def getNewest(self):
        if self.similarity:
            return self.db.findLastByHash(self.aHashes, self.dHashes_h, self.dHashes_v, self.bits-20, self.bits+20)
        else:
            return self.db.findLastByCRC(self.crc)   
    def getOldest(self):
        if self.similarity:
            return self.db.findFirstByHash(self.aHashes, self.dHashes_h, self.dHashes_v, self.bits-20, self.bits+20)
        else:
            return self.db.findFirstByCRC(self.crc)
        
    def getSimilarCount(self):
        if self.similarity:
            return self.db.getAvgSum(self.aHashes, self.dHashes_h, self.dHashes_v, self.bits-20, self.bits+20)
        else:
            return self.db.getCrcSum(self.crc)
            
        

    def getAllByCrc(self):
        return self.db.findAllByCRC(self.crc)
    def getAllByAvg(self):
        return self.db.findAllByHash(self.aHashes, self.dHashes_h, self.dHashes_v, self.bits-20, self.bits+20)
    
    
        
    def getAllSimilar(self, image, similarity=True):
        self.newImage(image, similarity)
        if similarity:
            return list(self.getAllByAvg())
        else:
            return list(self.getAllByCrc())


    def insertAndGetOne(self, image, metadata=None, similarity=True):
        self.newImage(image, similarity)
        if similarity:
            r = self.getOneByAvg()
        else:
            r = self.getOneByCrc()
        self.db.insertImage(self.aHashes, self.dHashes_h, self.dHashes_v, self.crc, self.bits, *metadata)
        return r
    
    def insertImage(self, *args):
        self.db.insertImage(self.aHashes, self.dHashes_h, self.dHashes_v, self.crc, self.bits, *args)
        
        
    def imageKnown(self):
        pass
        
    
    def inserAndGetAll(self):
        pass



        
        

if __name__ == '__main__':
    # Some testig (might be broken, no clue tbh.)
    path = "./pics_folder"
    import pstats
    import cProfile
    def test():
        dupcheck = SimilarImagesSql(':memory:')
        stime = time()
        times = 0
        dupsi = 0
        for fname in searchForFiles(path, tuple(('.jpg', '.JPG', '-jpeg', '.JPEG', '.gif', '', '.GIF', '.png', '.PNG', '.bmp', '.BMP'))):
            #print fname
            try:
                data = open(fname, 'rb').read()
                dups = dupcheck.insertAndGetOne(data, (False, u"", u"", 1, fname.decode(), u""))
            except Exception as e:
                print "EXCEPTION:", e
                continue
            times += 1
            if dups:
                print fname, dups
                dupsi += 1
                Image.open(fname).show()
                Image.open(dups[3]).show()
        stime = time()-stime
        print 'Need %f seconds for %i (%i) images. (%f/is)' %(stime, times, dupsi, (times/stime))
    #print cProfile.run('test()', sort=1)
    test()