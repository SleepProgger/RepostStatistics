import sqlite3
import time

#
# Here is a bunch of stuff which needs to get removed and/or is broken.
# The most interesting function for now are:
# - insertImageAndDups
#    Inserts the hashes from an image, search for similar known images and add found (near)duplicates
#    to a table. Also returns the duplicate image ids.
# - get_image_data_from_ids
#    Does this need a description ?
# 
# TODO:
# - The search for duplicates is slow as fuck.
#   We maybe should tweak the key settings in the db.
# - Remove unused/broken/old functions
#



db_getHashes = 'SELECT ahash_1, ahash_2, ahash_3, ahash_4, dhash_h_1, dhash_h_2, dhash_h_3, dhash_h_4, dhash_v_1, dhash_v_2, dhash_v_3, dhash_v_4, imagepath from images where animated = 0;'
db_getHash = 'SELECT ahash_1, ahash_2, ahash_3, ahash_4, dhash_h_1, dhash_h_2, dhash_h_3, dhash_h_4, dhash_v_1, dhash_v_2, dhash_v_3, dhash_v_4, rowid from images where animated = 0 and imagepath = ?;'

 

 
db_getAvg_ = """
            select galerieId gid
            from images
                where animated = 0
                and bits < ? and bits > ?
                and hamming3(ahash_1, ?)+hamming3(ahash_2, ?)+hamming3(ahash_3, ?)+hamming3(ahash_4, ?) <= %i
                and hamming3(dhash_h_1, ?)+hamming3(dhash_h_2, ?)+hamming3(dhash_h_3, ?)+hamming3(dhash_h_4, ?) <= %i
                and hamming3(dhash_v_1, ?)+hamming3(dhash_v_2, ?)+hamming3(dhash_v_3, ?)+hamming3(dhash_v_4, ?) <= %i
"""
db_getAvg = db_getAvg_ % (3, 5, 5) #(10, 10, 10) #(3, 5, 5)

db_getAvg_wDiff_ = """
            select rowid iId,
                hamming3(ahash_1, ?)+hamming3(ahash_2, ?)+hamming3(ahash_3, ?)+hamming3(ahash_4, ?)
                + hamming3(dhash_h_1, ?)+hamming3(dhash_h_2, ?)+hamming3(dhash_h_3, ?)+hamming3(dhash_h_4, ?)
                + hamming3(dhash_v_1, ?)+hamming3(dhash_v_2, ?)+hamming3(dhash_v_3, ?)+hamming3(dhash_v_4, ?) diff
            from images
                where animated = 0
                and bits < ? and bits > ?
                and hamming3(ahash_1, ?)+hamming3(ahash_2, ?)+hamming3(ahash_3, ?)+hamming3(ahash_4, ?) <= %i
                and hamming3(dhash_h_1, ?)+hamming3(dhash_h_2, ?)+hamming3(dhash_h_3, ?)+hamming3(dhash_h_4, ?) <= %i
                and hamming3(dhash_v_1, ?)+hamming3(dhash_v_2, ?)+hamming3(dhash_v_3, ?)+hamming3(dhash_v_4, ?) <= %i
"""
db_getAvg_wDiff = db_getAvg_wDiff_ % (3, 5, 5) #(10, 10, 10) #(3, 5, 5)


# Prety dirty with the string substitution but for now ok i think
# TODO: not in repostTable check
db_insertDup_LSH_ = """
    INSERT INTO similarImages_byLSH
        select %%i nId, irowid iId, hamming3(ahash_1, :aH_1 )+hamming3(ahash_2, :aH_2 )+hamming3(ahash_3, :aH_3 )+hamming3(ahash_4, :aH_4 ) diffA,
            hamming3(dhash_h_1, :dH_h_1 )+hamming3(dhash_h_2, :dH_h_2 )+hamming3(dhash_h_3, :dH_h_3 )+hamming3(dhash_h_4, :dH_h_4 )
            + hamming3(dhash_v_1, :dH_v_1 )+hamming3(dhash_v_2, :dH_v_2 )+hamming3(dhash_v_3, :dH_v_3 )+hamming3(dhash_v_4, :dH_v_4 ) diffD
        from (
         select rowid irowid, ahash_1, ahash_2, ahash_3, ahash_4, dhash_h_1, dhash_h_2, dhash_h_3, dhash_h_4, dhash_v_1, dhash_v_2, dhash_v_3, dhash_v_4 from images i
            where animated = 0
            and ( bits between :lBits and :hBits )
            and hamming3(ahash_1, :aH_1 )+hamming3(ahash_2, :aH_2 )+hamming3(ahash_3, :aH_3 )+hamming3(ahash_4, :aH_4 ) <= %i
            and hamming3(dhash_h_1, :dH_h_1 )+hamming3(dhash_h_2, :dH_h_2 )+hamming3(dhash_h_3, :dH_h_3 )+hamming3(dhash_h_4, :dH_h_4 ) <= %i
            and hamming3(dhash_v_1, :dH_v_1 )+hamming3(dhash_v_2, :dH_v_2 )+hamming3(dhash_v_3, :dH_v_3 )+hamming3(dhash_v_4, :dH_v_4 ) <= %i
            and :nId != rowid
            and i.rowid not in (SELECT imgId_a from similarImages_byLSH where :nId = imgId_b )
            and i.rowid not in (SELECT imgId_b from similarImages_byLSH where :nId = imgId_a )   
        );
"""
db_insertDup_LSH = db_insertDup_LSH_ % (5, 8, 8) #(10, 10, 10) #(3, 5, 5)

 
  


db_avgExists_ = """
    SELECT g.userurl, g.link, g.datetime, g.title from galeries as g,
        (SELECT galerieId from images 
            where animated = 0 and
            (
            hamming3(ahash_1, ?) +
            hamming3(ahash_2, ?) +
            hamming3(ahash_3, ?) +
            hamming3(ahash_4, ?) <= 3
            ) and (
            hamming3(dhash_h_1, ?)+
            hamming3(dhash_h_2, ?)+
            hamming3(dhash_h_3, ?)+
            hamming3(dhash_h_4, ?)+
            hamming3(dhash_v_1, ?)+
            hamming3(dhash_v_2, ?)+
            hamming3(dhash_v_3, ?)+
            hamming3(dhash_v_4, ?) <= 10 )
        ) where galerieId=g.rowid order by g.datetime desc LIMIT 1;
"""



class DBConnector():
    def __init__(self, fname, con=None, loadExtensions=True, re_analyze=True):
        if not con:
            con = sqlite3.connect(fname)
        self.con = con
        self.create_function = con.create_function
        self.cursor = con.cursor
        self.execute = con.execute
        self.commit = con.commit
            
        if loadExtensions:
            con.enable_load_extension(loadExtensions)
            # TODO: dirty, but ok for now
            self.load_extension('Sqlite3_Hamming.dll') 
            
        # in case the db got messed up we re analyze at every start
        if re_analyze: self.execute("ANALYZE;")
            
        self.initDb()
        print "db init done"


    def load_extension(self, fPath):
        self.execute('SELECT load_extension("%s");' % fPath)
        
        
    def create_function(self, name, paramCount, funPtr):
        # Just a placeholder for the create_function method of the connection
        raise Exception("Placeholder function called")
    
        
 
    #
    # Imgur stuff
    #
    def initDb(self):
        # rowid is implicite id
        self.execute("""
        CREATE TABLE IF NOT EXISTS galeries (
            userurl VARCHAR ,
            link VARCHAR,
            datetime LONG,
            title VARCHAR,
            userid INT
        );
        """)
        self.execute("""
        CREATE TABLE IF NOT EXISTS images (
            galerieId LONG,
            imagepath VARCHAR,
            animated BOOL,
            ahash_1 LONG, ahash_2 LONG, ahash_3 LONG, ahash_4 LONG,
            dhash_h_1 LONG, dhash_h_2 LONG, dhash_h_3 LONG, dhash_h_4 LONG,
            dhash_v_1 LONG, dhash_v_2 LONG, dhash_v_3 LONG, dhash_v_4 LONG,
            crc VARCHAR,
            bits INT,    /* We use this to speed up the lookup, as when the set bits isn't in the correct range the entry is def. no duplicate */
            size INT,
            lastChecked LONG,
            width INT, height INT
        );
        """)
        self.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            postId,
            commentId
        );
        """)
        self.execute("""
            CREATE TABLE IF NOT EXISTS user(
                id           INT PRIMARY KEY,
                secret       TEXT
            );
        """)
        self.execute("""
            CREATE TABLE IF NOT EXISTS spamProt_invalidImages(
                userid       INT,
                timestamp    LONG
            );
        """)
        
        self.execute("""
            CREATE TABLE IF NOT EXISTS similarImages_byLSH(
                imgId_a        LONG,
                imgId_b        LONG,
                diff_a         INT,
                diff_d         INT
            );
        """)
        self.execute("""
            CREATE TABLE IF NOT EXISTS similarImages_byCRC(
                imgId_a        LONG,
                imgId_b        LONG
            );
        """)
        self.execute("""
            CREATE TABLE IF NOT EXISTS blocked_user(
                userid INT PRIMARY KEY
            );
        """)
        self.execute('CREATE UNIQUE INDEX IF NOT EXISTS ind_CRCDups ON similarImages_byCRC (imgId_a, imgId_b);')
        self.execute('CREATE UNIQUE INDEX IF NOT EXISTS ind_LSHDups ON similarImages_byLSH (imgId_a, imgId_b);')
        self.execute('CREATE INDEX IF NOT EXISTS gInd ON galeries (link);')
        self.execute('CREATE INDEX IF NOT EXISTS bitsI ON images (bits);')
        self.execute('CREATE INDEX IF NOT EXISTS image2gallery ON images (galerieId);')
        # i don't really know if this does any good (but it seemed like it does) ? TODO: check it
        self.execute('CREATE INDEX IF NOT EXISTS hashes on images (ahash_1,ahash_2,ahash_3,ahash_4,dhash_h_1,dhash_h_2,dhash_h_3,dhash_h_4,dhash_v_1,dhash_v_2,dhash_v_3,dhash_v_4);')
#        self.load_extension('Sqlite3_Hamming.dll')
        self.commit();


    ##################################
    # user stuff
    ##################################
    db_validateUser = "SELECT 1 from user where id = ? and secret = ?;"
    def validateUser(self, userId, userPw):
        return not self.execute(self.db_validateUser, (userId, userPw)).fetchone() is None
    
    db_antiSpam_invalidImageLimit_del = "DELETE from spamProt_invalidImages where timestamp < ?;"
    db_antiSpam_invalidImageLimit_count = "SELECT count() from spamProt_invalidImages where userid = ?;"
    def toMuchImageMisses(self, userId, missLimit=10, missTime=180):
        self.execute(self.db_antiSpam_invalidImageLimit_del, (time.time() - missTime,))
        return self.execute(self.db_antiSpam_invalidImageLimit_count, (userId,)).fetchone()[0] > missLimit
    
        
    ##################################
    # galerie and aggregation stuff
    ##################################
    db_galerieExists = "SELECT 1 from galeries where link = ?;"
    def galerieExists(self, link):
        return not self.execute(self.db_galerieExists, (link,)).fetchone() is None
    
    db_commentWritten = "SELECT 1 from comments where postid = ?;"
    def commentWritten(self, postId):
        return not self.execute(self.db_commentWritten, (postId,)).fetchone() is None
    
    db_logComment = "INSERT into comments VALUES (?, ?);"
    def logComment(self, postId, commentId):
        return not self.execute(self.db_logComment, (postId, commentId)).fetchone() is None
    
    db_already_commented = "SELECT 1 FROM comments WHERE postId = ?;"
    def already_commented(self, postId):
        return not self.execute(self.db_already_commented, (postId,)).fetchone() is None

    db_getImageCount = "SELECT count() from images;"  
    def getImageCount(self):
        return self.execute(self.db_getImageCount).fetchone()[0]
    
    def getOldestImage(self):
        return self.execute('select min(datetime) from galeries;').fetchone()[0]
    
    ##################################
    # Find images
    ##################################
    db_crcExists = "SELECT g.datetime, g.userurl, g.link, g.title from images as i, galeries as g where g.rowid = i.galerieId and i.crc = ? order by datetime desc LIMIT 1;"
    def findLastByCRC(self, crc):
        return self.execute(self.db_crcExists, (crc,)).fetchone()
    
    db_crcExists_first = "SELECT g.datetime, g.userurl, g.link, g.title from images as i, galeries as g where g.rowid = i.galerieId and i.crc = ? order by datetime asc LIMIT 1;"
    def findFirstByCRC(self, crc):
        return self.execute(self.db_crcExists_first, (crc,)).fetchone()

    db_avgExists = """
        SELECT g.datetime, g.userurl, g.link, g.title from galeries as g,
            ( %s ) where gid=g.rowid order by g.datetime desc LIMIT 1;
    """ % (db_getAvg ,)
    def findLastByHash(self, aHashes, dHashes_h, dHashes_v, bitcountlower, bitcountupper):
        return self.execute(self.db_avgExists, (bitcountupper, bitcountlower)+aHashes+dHashes_h+dHashes_v).fetchone()
    
    db_avgExists_first = """
        SELECT g.datetime, g.userurl, g.link, g.title from galeries as g,
            ( %s ) where gid=g.rowid order by g.datetime asc LIMIT 1;
    """ % (db_getAvg ,)
    def findFirstByHash(self, aHashes, dHashes_h, dHashes_v, bitcountlower, bitcountupper):
        return self.execute(self.db_avgExists_first, (bitcountupper, bitcountlower)+aHashes+dHashes_h+dHashes_v).fetchone()
    
    
    db_avgExists_all = """
        SELECT g.datetime, g.userurl, g.link, g.title from galeries as g,
            ( %s ) where gid=g.rowid order by g.datetime desc;
    """ % (db_getAvg ,)
    def findAllByHash(self, aHashes, dHashes_h, dHashes_v, bitcountlower, bitcountupper, buffersize=1024):
        for r in self.execute(self.db_avgExists_all, (bitcountupper, bitcountlower)+aHashes+dHashes_h+dHashes_v).fetchmany(buffersize):
            yield r
    
    db_crcExists_all = "SELECT g.datetime, g.userurl, g.link, g.title from images as i, galeries as g where g.rowid = i.galerieId and i.crc = ? order by datetime desc;"
    def findAllByCRC(self, crc, buffersize=1024):
        for r in self.execute(self.db_crcExists_all, (crc, )).fetchmany(buffersize):
            yield r    
    
    
    db_avgExists_all_before = """
        SELECT g.datetime, g.userurl, g.userid, g.link, g.title from galeries as g, images i, similarImages_byLSH s
            WHERE (i.rowid = s.imgId_a OR i.rowid = s.imgId_b) AND i.rowid != :iid
            AND g.rowid = i.galerieId
            AND (:iid = s.imgId_a OR :iid = s.imgId_b)
            AND diff_a <= :maxA AND diff_d <= :maxD
            AND g.datetime <= :date
            ORDER BY g.datetime ASC;
    """
    def findAllByHash_before(self, imageId, dateTime, maxAHash=3, maxDHash=10):
        cur = self.cursor()
        #print "findAllByHash_before", "start", self.db_avgExists_all_before.replace(":iid", str(imageId)).replace(":date", str(dateTime)).replace(":maxA", str(maxAHash)).replace(":maxD", str(maxDHash))
        for r in cur.execute(self.db_avgExists_all_before, {'iid':imageId, 'date':dateTime, 'maxA':maxAHash, 'maxD':maxDHash}).fetchmany():
            yield r
        #print "findAllByHash_before", "done"
        self.commit()

    db_crcExists_all_ = """SELECT g.datetime, g.userurl, g.userid, g.link, g.title
        from similarImages_byCRC s, images as i, galeries as g
        WHERE (i.rowid = s.imgId_a OR i.rowid = s.imgId_b) AND i.rowid != :iid
        AND g.rowid = i.galerieId
        AND (:iid = s.imgId_a OR :iid = s.imgId_b)
        AND g.datetime <= :date
        ORDER BY datetime ASC;
    """
    def findAllByCRC_before(self, imageId, dateTime):
        cur = self.cursor()
        #print "findAllByCRC_before", "start", self.db_crcExists_all_.replace(":iid", str(imageId)).replace(":date", str(dateTime))
        for r in cur.execute(self.db_crcExists_all_, {'iid':imageId, 'date':dateTime}).fetchmany():
            yield r
        #print "findAllByCRC_before", "done"
        self.commit()
        
    
    def get_reposts_by_image_hash(self, hash_):
        tmp = self.execute('SELECT i.rowid, animated, g.datetime FROM galeries as g, images as i WHERE g.rowid = i.galerieId AND g.link = ?;', (hash_,)).fetchone()
        ori = self.execute('SELECT g.datetime, g.userurl, g.userid, g.link, g.title FROM galeries as g, images as i WHERE g.rowid = i.galerieId AND g.link = ?;', (hash_,)).fetchone() 
        if not tmp: return False
        iid, animated, timestamp = tmp
        if animated:
            return (ori, self.findAllByCRC_before(iid, timestamp))
        return (ori, self.findAllByHash_before(iid, timestamp))
    
    def is_animated_by_hash(self, hash_):
        return self.execute('SELECT animated FROM galeries as g, images as i WHERE g.rowid = i.galerieId AND g.link = ?;', (hash_,)).fetchone()[0]
    
    
    def get_image_data_from_ids(self, ids, olderAs):
        ret = list()
        cur = self.cursor()
        for tmp_id in ids: 
            tmp = cur.execute("""SELECT g.datetime, g.userurl, g.userid, g.link, g.title
            FROM images as i, galeries as g
            WHERE g.rowid = i.galerieId AND i.rowid = ? and g.datetime < ? ORDER BY g.datetime ASC;""", (tmp_id, olderAs)).fetchone()
            if tmp: ret.append(tmp)
        return ret
    
    db_avgSum = 'select count() from  ( %s )'  %  (db_getAvg ,)
    def getAvgSum(self, aHashes, dHashes_h, dHashes_v, bitcountlower, bitcountupper):
        return self.execute(self.db_avgSum, (bitcountupper, bitcountlower)+aHashes+dHashes_h+dHashes_v).fetchone()[0]
    
    db_crcSum = "SELECT count() from images where crc = ?;"
    def getCrcSum(self, crc):
        return self.execute(self.db_crcSum, (crc,)).fetchone()[0]
    

    ##################################
    # Insert, change, remove
    ##################################   
    db_insertGalerie = "INSERT INTO galeries VALUES (?, ?, ?, ?, ?);"
    db_insertImage = "INSERT INTO images VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
    def insertImage_(self, user, link, datetime, title, iPath, animated, aHashes, dHashes_h, dHashes_v, crc, bits):
        cur = self.cursor()
        cur.execute(self.db_insertGalerie, (user, link, datetime, title, time.time()))
        cur.execute(self.db_insertImage, (cur.lastrowid, iPath, animated)+aHashes+dHashes_h+dHashes_v+(crc,bits))
        self.commit()
    
    def insertImage(self, aHashes, dHashes_h, dHashes_v, crc, bits, animated, user, userid, link, datetime, title, iPath, size):
        cur = self.cursor()
        cur.execute(self.db_insertGalerie, (user, link, datetime, title, userid))
        cur.execute(self.db_insertImage, (cur.lastrowid, iPath, animated)+aHashes+dHashes_h+dHashes_v+(crc,bits, size, time.time()))
        self.commit()      
      
    
#     db_findDuplicates_LSH = """
#             select rowid, hamming3(ahash_1, :aH_1 )+hamming3(ahash_2, :aH_2 )+hamming3(ahash_3, :aH_3 )+hamming3(ahash_4, :aH_4 ) diffA,
#                 hamming3(dhash_h_1, :dH_h_1 )+hamming3(dhash_h_2, :dH_h_2 )+hamming3(dhash_h_3, :dH_h_3 )+hamming3(dhash_h_4, :dH_h_4 )
#                 + hamming3(dhash_v_1, :dH_v_1 )+hamming3(dhash_v_2, :dH_v_2 )+hamming3(dhash_v_3, :dH_v_3 )+hamming3(dhash_v_4, :dH_v_4 ) diffD
#             from images
#                 where animated = 0
#                 and ( bits between :lBits and :hBits )
#                 and hamming3(ahash_1, :aH_1 )+hamming3(ahash_2, :aH_2 )+hamming3(ahash_3, :aH_3 )+hamming3(ahash_4, :aH_4 ) <= :min_aDiff
#                 and hamming3(dhash_h_1, :dH_h_1 )+hamming3(dhash_h_2, :dH_h_2 )+hamming3(dhash_h_3, :dH_h_3 )+hamming3(dhash_h_4, :dH_h_4 ) <= :min_dhDiff
#                 and hamming3(dhash_v_1, :dH_v_1 )+hamming3(dhash_v_2, :dH_v_2 )+hamming3(dhash_v_3, :dH_v_3 )+hamming3(dhash_v_4, :dH_v_4 ) <= :min_dvDiff
#                 and :nId != rowid;
#     """

    db_findDuplicates_LSH_ = """
            select rowid, hamming3(ahash_1, :aH_1 )+hamming3(ahash_2, :aH_2 )+hamming3(ahash_3, :aH_3 )+hamming3(ahash_4, :aH_4 ) diffA,
                hamming3(dhash_h_1, :dH_h_1 )+hamming3(dhash_h_2, :dH_h_2 )+hamming3(dhash_h_3, :dH_h_3 )+hamming3(dhash_h_4, :dH_h_4 )
                + hamming3(dhash_v_1, :dH_v_1 )+hamming3(dhash_v_2, :dH_v_2 )+hamming3(dhash_v_3, :dH_v_3 )+hamming3(dhash_v_4, :dH_v_4 ) diffD
            from images
                where animated = 0
                and ( bits between :lBits and :hBits )
                and hamming3(ahash_1, :aH_1 )+hamming3(ahash_2, :aH_2 )+hamming3(ahash_3, :aH_3 )+hamming3(ahash_4, :aH_4 ) <= :min_aDiff
                and hamming3(dhash_h_1, :dH_h_1 )+hamming3(dhash_h_2, :dH_h_2 )+hamming3(dhash_h_3, :dH_h_3 )+hamming3(dhash_h_4, :dH_h_4 ) <= :min_dhDiff
                and hamming3(dhash_v_1, :dH_v_1 )+hamming3(dhash_v_2, :dH_v_2 )+hamming3(dhash_v_3, :dH_v_3 )+hamming3(dhash_v_4, :dH_v_4 ) <= :min_dvDiff
                and :nId != rowid;
    """
    db_findDuplicates_LSH = """
            select rowid, hamming3(ahash_1, :aH_1 )+hamming3(ahash_2, :aH_2 )+hamming3(ahash_3, :aH_3 )+hamming3(ahash_4, :aH_4 ) diffA,
                hamming3(dhash_h_1, :dH_h_1 )+hamming3(dhash_h_2, :dH_h_2 )+hamming3(dhash_h_3, :dH_h_3 )+hamming3(dhash_h_4, :dH_h_4 )
                + hamming3(dhash_v_1, :dH_v_1 )+hamming3(dhash_v_2, :dH_v_2 )+hamming3(dhash_v_3, :dH_v_3 )+hamming3(dhash_v_4, :dH_v_4 ) diffD
            from (SELECT * FROM images WHERE animated = 0 AND ( bits BETWEEN :lBits AND :hBits) AND :nId != rowid) 
                WHERE hamming3(ahash_1, :aH_1 )+hamming3(ahash_2, :aH_2 )+hamming3(ahash_3, :aH_3 )+hamming3(ahash_4, :aH_4 ) <= :min_aDiff
                and hamming3(dhash_h_1, :dH_h_1 )+hamming3(dhash_h_2, :dH_h_2 )+hamming3(dhash_h_3, :dH_h_3 )+hamming3(dhash_h_4, :dH_h_4 ) <= :min_dhDiff
                and hamming3(dhash_v_1, :dH_v_1 )+hamming3(dhash_v_2, :dH_v_2 )+hamming3(dhash_v_3, :dH_v_3 )+hamming3(dhash_v_4, :dH_v_4 ) <= :min_dvDiff
                ;
    """

    db_insertDuplicate_LSH = 'INSERT INTO similarImages_byLSH VALUES (?, ?, ?, ?)'
    db_findDuplicates_CRC = """
            SELECT rowid from images i
            WHERE animated=1 AND crc = :crc
            AND :nId != rowid;
    """
    db_insertDuplicate_CRC = 'INSERT INTO similarImages_byCRC VALUES (?, ?)'        
    def insertImageAndDups(self, aHashes, dHashes_h, dHashes_v, crc, bits, animated, user, userid, link, datetime, title, iPath, size, bitcountupper, bitcountlower, mDiffA, mDiffdh, mDiffdv, width, height, retMDiffA, retMDiffd):
        cur = self.cursor()
        cur.execute(self.db_insertGalerie, (user, link, datetime, title, userid))
        cur.execute(self.db_insertImage, (cur.lastrowid, iPath, animated)+aHashes+dHashes_h+dHashes_v+(crc,bits, size, time.time(), width, height))
        nId = cur.lastrowid
        ids = list()
#         inserted = 0
        
        if animated:
            for dupId in cur.execute(self.db_findDuplicates_CRC, dict({
                                                'nId':nId,
                                                'crc':crc
                                                })).fetchmany(-1):
                dupId = dupId[0]
                try:
                    cur.execute(self.db_insertDuplicate_CRC, tuple(sorted((nId, dupId))))
#                     inserted += 1
                    ids.append(dupId)
                except sqlite3.Error as e:
                    pass # should only be the not unique exception
                    # print "SQLITE EXCEPTION CRC", e
        else:
            for dupId, diffA, diffD in cur.execute(self.db_findDuplicates_LSH, dict({
                                                    'nId':nId,
                                                    'min_aDiff':mDiffA, 'min_dhDiff':mDiffdh, 'min_dvDiff':mDiffdv,
                                                    'aH_1':aHashes[0], 'aH_2':aHashes[1], 'aH_3':aHashes[2], 'aH_4':aHashes[3],
                                                    'dH_h_1':dHashes_h[0], 'dH_h_2':dHashes_h[1], 'dH_h_3':dHashes_h[2], 'dH_h_4':dHashes_h[3],
                                                    'dH_v_1':dHashes_v[0], 'dH_v_2':dHashes_v[1], 'dH_v_3':dHashes_v[2], 'dH_v_4':dHashes_v[3],
                                                    'lBits':bitcountlower, 'hBits':bitcountupper
                                                    })).fetchmany(-1):
                try:
                    cur.execute(self.db_insertDuplicate_LSH, tuple(sorted((nId, dupId))) + (diffA, diffD) )
                    #inserted += 1
                    if diffA <= retMDiffA and diffD <= retMDiffd: 
                        ids.append(dupId)
                except sqlite3.Error as e:
                    pass # should only be the not unique exception
                    # print "SQLITE EXCEPTION LSH", e        
        self.commit()
        return (nId, ids)
    
    
    
    
    def iterHashes(self, bufferSize=10000000):
        for r in self.con.execute(self.db_getHashes).fetchmany(bufferSize):
            #if not r: break
            #for row in r:
            yield r
            
    def getHash(self, imagepath):
        d = self.con.execute(db_getHash, (imagepath,)).fetchone()
        return d

    ##################################
    # Misc
    ##################################
    db_imageRepostCount = "SELECT count() from similarImages_byLSH"
    def getRepostCount_images(self):
        return self.con.execute(self.db_imageRepostCount).fetchone()[0]
    db_animationRepostCount = "SELECT count() from similarImages_byCRC"
    def getRepostCount_animations(self):
        return self.con.execute(self.db_animationRepostCount).fetchone()[0]
    def getReprostCount(self):
        return self.getRepostCount_images() + self.getRepostCount_animations()
    
    def add_blocked_user(self, userid):
        return self.con.execute("INSERT INTO blocked_user VALUES (?);", (userid,))
    def remove_blocked_user(self, userid):
        return self.con.execute("DELETE FROM blocked_user where userid = ?;", (userid,))
    def is_user_blocked(self, userid):
        return self.con.execute("SELECT userid from blocked_user WHERE userid = ?;", (userid,)).fetchone() is not None
    

if __name__ == '__main__':
    pass