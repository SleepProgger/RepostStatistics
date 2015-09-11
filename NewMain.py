# -*- coding: UTF-8 -*-
import sys
import json
from Imgur.Factory import Factory
from time import time, sleep, gmtime, strftime, localtime
from database.ImgurDBConnector import DBConnector
from mynet import Web
from stuff.Similarity import levenshtein_n
from stuff.Format import crudeTimeFormat
from dupFinder.FindDuplicates import SimilarImagesSql
import Imgur.DirtyCommenter
from worker import CommentSender
import re
from traceback import format_exc
import codecs

#
# TODO
# - PORT TO NEW IMGUR API PYTHON LIB. It is WAY better as the old version, and does't need most of the code i added.
#   When done, remove the old imgur api files and use them from the installed module... 
# - Do the job split stuff (what did i even ment with that ? oO)
# - check if image is still online and doesn't changed before posting ?
# - Check if image is meme, reaction pic ?
# - check if it was from the  same user and other stuff (reddit ...) (same user is done)
# - Synonym before levensthein for title
# - adjust levensthein, weight ops (remove more as change ?) 
# - Cooler similarity bar (unicode with ~3 widthes) ? (stars are as good as it gets ? (percentage would be more efficient though.))
# - Register for repost notification
# - month format for last seen
# - galeries (might not be doable within api limits)
# - gifs (something better as just crc the data ?)
# - add repost tags (done)
# - use logging module instead of my crude own impl.
#


logfile = 'imgur.log'
lfile = codecs.open(logfile, 'ab', encoding='utf-8')
def lognprint(*args):
    lognprint_base(strftime(u"%a, %d %b %Y %H:%M:%S", localtime()) + u' :\t' + (u' '.join(map(unicode, args))) + u'\n')
def lognprint_base(out):
    lfile.write(out)
    lfile.flush()
    sys.stdout.write(out.encode("utf-8"))
Imgur.DirtyCommenter.lognprint = lognprint
CommentSender.lognprint = lognprint
Web.lognprint = lognprint
DirtyCommenter = Imgur.DirtyCommenter.DirtyCommenter
CommentSender = CommentSender.CommentSender

def genUnicodeSuccessBar(length, curVal, maxVal, elems=[u'▃',u'▅',u'▇'], blank=u'▁', borderLeft=u'╠', borderRight=u'╣'):
    elemsWBlank = elems + [blank]
    ret = borderLeft
    n = (float(curVal)/maxVal)
    full = int(n*length)
    rest = int(round((n*length - full)*len(elems)))
    ret += elems[-1]*full
    if full  < length and rest > 0:
        ret += elemsWBlank[rest-1]
        ret += blank*(length-full-1)
    else:
        ret += blank*(length-full)
    ret += borderRight
    return ret
    


str_duplicate = u"Image last seen %s before at http://imgur.com/gallery/%s %s"
str_similar = u"Image probably last seen %s before at http://imgur.com/gallery/%s %s"
str_duplicate_first = u"First seen %s before at http://imgur.com/gallery/%s %s"
str_similar_first = u"Probably first seen %s before at http://imgur.com/gallery/%s %s"
str_duplicate_firstTimes = u"Seen %i times since %s before at http://imgur.com/gallery/%s %s"
str_similar_firstTimes = u"Probably seen %i times since %s before at http://imgur.com/gallery/%s %s"

_crudeTimeFormat = crudeTimeFormat
crudeTimeFormat = lambda *args: unicode(_crudeTimeFormat(*args))

#exit()
def sendDupMessage(newE, dups, commenter, db, byCrc=True):
#    newE = (newE[u'datetime'], "", newE[u'id'], newE[u'title'])
    newE = (newE[u'datetime'], "", newE[u'account_id'], newE[u'id'], newE[u'title'])
    #datetime, userurl, userid, link, title = dups[-1]
#     trip = False
#     if lastSeen[2] == firstSeen[2]:
#         newE, lastSeen = sorted([newE, lastSeen], reverse=True)
#     else:
#         newE, lastSeen, firstSeen = sorted([newE, lastSeen, firstSeen], reverse=True)
#         trip = True
        
    if db.commentWritten(newE[2]):
        return 
    
    message = list()
    
    #commenter.appendComment(galleryId, message, retries, parentCommentId=-1, childComment=None):
    
    # shouldn'T be needed as the db sort it by date, but sometimes there is a bug ?! TODO: 
    dups.sort()
    
    lastSeen = dups[-1]
    firstSeen = dups[0]
    seen = len(dups)
    trip = firstSeen[3] != lastSeen[3]
        
    # last seen    
    to, tn = (lastSeen[4].lower().strip(), newE[4].lower().strip())
    titleInf = u"Title similarity: " + genUnicodeSuccessBar(5, 1-levenshtein_n(to, tn), 1, [u'★'], u'☆', u'', u'')
    if byCrc:
        #commentId = commenter.writeComment(newE[2], str_duplicate % (crudeTimeFormat(newE[0]-lastSeen[0]),lastSeen[2], titleInf))
        message = [commenter.TYPE_COMMENT_OR_REPLY, newE[3], str_duplicate % (crudeTimeFormat(newE[0]-lastSeen[0]),lastSeen[3], titleInf), 5, -1]
    else:
        #commentId = commenter.writeComment(newE[2], str_similar % (crudeTimeFormat(newE[0]-lastSeen[0]), lastSeen[2], titleInf))
        message = [commenter.TYPE_COMMENT_OR_REPLY, newE[3], str_similar % (crudeTimeFormat(newE[0]-lastSeen[0]), lastSeen[3], titleInf), 5, -1]

                
    # first seen
    if trip:
        to, tn = (firstSeen[4].lower().strip(), newE[4].lower().strip())
        titleInf = u"Title similarity: " + genUnicodeSuccessBar(5, 1-levenshtein_n(to, tn), 1, [u'★'], u'☆', u'', u'')
        if byCrc:
            if seen > 2:
                #commentId = commenter.writeReply(newE[2], commentId, str_duplicate_firstTimes % (seen-1, crudeTimeFormat(newE[0]-firstSeen[0]), firstSeen[2], titleInf))
                message.append( [commenter.TYPE_COMMENT_OR_REPLY, newE[3], str_duplicate_firstTimes % (seen-1, crudeTimeFormat(newE[0]-firstSeen[0]), firstSeen[3], titleInf), 7, -1] )
            else:
                #commentId = commenter.writeReply(newE[2], commentId, str_duplicate_first % (crudeTimeFormat(newE[0]-firstSeen[0]), firstSeen[2], titleInf))
                message.append( [commenter.TYPE_COMMENT_OR_REPLY, newE[3], str_duplicate_first % (crudeTimeFormat(newE[0]-firstSeen[0]), firstSeen[3], titleInf), 7, -1] )
        else:
            if seen > 2:                
                #commentId = commenter.writeReply(newE[2], commentId, str_similar_firstTimes % (seen-1, crudeTimeFormat(newE[0]-firstSeen[0]), firstSeen[2], titleInf))
                message.append( [commenter.TYPE_COMMENT_OR_REPLY, newE[3], str_similar_firstTimes % (seen-1, crudeTimeFormat(newE[0]-firstSeen[0]), firstSeen[3], titleInf), 7, -1] )
            else:
                #commentId = commenter.writeReply(newE[2], commentId, str_similar_first % (crudeTimeFormat(newE[0]-firstSeen[0]), firstSeen[2], titleInf))
                message.append( [commenter.TYPE_COMMENT_OR_REPLY, newE[3], str_similar_first % (crudeTimeFormat(newE[0]-firstSeen[0]), firstSeen[3], titleInf), 7, -1] )
        #sleep(28)

    commenter.queue.append(message)
    db.logComment(newE[3], -1)


popcount = lambda n: bin(n).count('1')


def updateFields(galImage, db):
    # update userid
    db.execute('UPDATE galeries SET userid = ? WHERE link = ?;', (galImage[u'account_id'], galImage[u'id']) )
    # update size, lastChecked, width, height
    db.execute('UPDATE images SET size = ?, width = ?, height = ?, lastChecked = ? WHERE galerieId = (SELECT rowid FROM galeries WHERE link = ?);', (galImage[u'size'], galImage[u'width'], galImage[u'height'], time(), galImage[u'id']) )        


from PIL import Image


def update_elem(elem, factory, imgur, dupcheck, commenter, times, maxPostTime, alwaysPost=False):
    # times -> updates, known, skipped, errors, albums = (0, 0, 0, 0, 0)
    #time_hash, time_db_gen, time_db_dup, time_api_request, time_image, time_message = (0, 0, 0, 0, 0, 0) # TIMING
    times, times_ = times
    
    con = dupcheck.db
    if elem[u'is_album']:
        times[4] += 1
        return False
    times_[1] -= time() # TIMING
    if con.galerieExists(elem[u'id']):
        times[1] += 1
        updateFields(elem, con)
        times_[1] += time() # TIMING
        return False
    times_[1] += time() # TIMING
    
    #TODO: 
    #sleep(3)
    #yield True
    #time_image -= time() # TIMING
    
    # dirty fix because when the size is higher x (TODO) imgur delivers the thumbnail as link url
    if elem['animated'] and elem[u'link'].endswith("h.gif") and elem['gifv']:
        lognprint('WARNING: Switch %s with %s' % (elem['link'], elem['gifv']))
        elem[u'link'] = elem[u'gifv'] 
    data = Web.request(elem[u'link'], retries=2)
    #time_image += time() # TIMING
    if not data:
        lognprint("Error requesting image", elem[u'link'])
        times[3] += 1
        return False
    try:
        #times_[0] -= time() # TIMING
        dupcheck.newImage(data, not elem[u'animated'])
        #times_[0] += time() # TIMING
        # aHashes, dHashes_h, dHashes_v, crc, bits, animated, user, link, datetime, title, iPath, size, bitcountupper, bitcountlower, mDiffA, mDiffdh, mDiffdv
    except Exception as e: # TODO catch specific excption
        lognprint('EXCEPTION: Hash creation exception:', e)
        return False
        
    times_[2] -= time() # TIMING
    nid, ids = con.insertImageAndDups(dupcheck.aHashes, dupcheck.dHashes_h, dupcheck.dHashes_v, dupcheck.crc, dupcheck.bits,
                                      elem[u'animated'], elem[u'account_url'], elem[u'account_id'], elem[u'id'], elem[u'datetime'], elem[u'title'], elem[u'link'], elem[u'size'], dupcheck.bits+22, dupcheck.bits-22, 5, 8, 8, elem[u'width'], elem[u'height'],
                                      3, 10 
                                      )
    times_[2] += time() # TIMING
    times_[1] -= time() # TIMING                
    dups = con.get_image_data_from_ids(ids, elem[u'datetime'])
    times_[1] += time() # TIMING
        
    #lognprint("DEBUG: nid/ins:", nid, ins)
    postIt = False
    if alwaysPost:
        postIt = True    
    elif elem[u'ups']-elem[u'downs'] < 40:
        times[2] += 1
    else: 
        postIt = True    
    if postIt and dups and len(dups) > 0:
        
        #gallery, tag, retries, upvote=True
        # TODO: this should always be send (or never as tags are shit now anyway) 
        #if alwaysPost or not ("mrw" in elem[u'title'].lower() or "mfw" in elem[u'title'].lower() or elem[u'title'].lower().startswith("when")):  
        #    commenter.appendTag(elem[u'id'], "rep ost", 7)
            #yield True
        #ret = comenter.sendAuthReqMessage(('gallery', gallery_id, "vote",  "tag", tag, ("up" if upvote else "down")), {})
        
        if not alwaysPost and not shouldIPost(con, elem, dups, maxPostTime):
            times[2] += 1
        else:
            lognprint("DUPLICATE:", "(", len(dups), ")", elem[u'id'], "==", dups)
            sendDupMessage(elem, dups, commenter, dupcheck.db, elem[u'animated'])
    times[0] += 1
    con.commit()
    return postIt


def updateGallery(factory, imgur, dupcheck, commenter, pages=5, start=0, gType="hot", timeD="day", post=True, maxPostTime=60*60*24*3):
    con = dupcheck.db
    for i in xrange(start, start+pages):
        #updates, known, skipped, errors, albums = (0, 0, 0, 0, 0)
        times = [0]*5
        #time_hash, time_db_gen, time_db_dup, time_api_request, time_image, time_message = (0, 0, 0, 0, 0, 0) # TIMING
        times_ = [0]*6
        
        times_[3] -= time()
        req = factory.buildRequest(('gallery', gType, 'viral', str(i), timeD))
        for j in xrange(5):
            try:
                res = imgur.retrieve(req)
                break
            except Exception as e:
                lognprint("EXCEPTION:", e)
                times_[3] += time() # TIMING
                sleep(60)
                times_[3] -= time() # TIMING
                lognprint("Retry #", j+1)
        else:
            lognprint("Connection problems")
            raise StopIteration()
        times_[3] += time() # TIMING
            
        if not res:
            lognprint("Page", i, "not found")
            continue
        
        yield True
        
        #print "PAGE", i
        for elem in res:
            if not isinstance(elem, dict):
                lognprint("Error: Strange elem:", elem)
                times[3][0] += 1
                continue
            
            if update_elem(elem, factory, imgur, dupcheck, commenter, [times, times_], maxPostTime, alwaysPost=False):
                sleep(3)           
            yield True
        lognprint("PAGE", gType, timeD, i, "=> updates:", times[0], "known:", times[1], "skipped:", times[2], "albums skipped:", times[4], "errors:", times[3], 'client_remaining', imgur.ratelimit.client_remaining)
        #time_hash, time_db_gen, time_db_dup, time_api_request, time_image, time_message = (0, 0, 0, 0, 0, 0) # TIMING
        lognprint("TIMES: time_hash: %.6f time_db_gen: %.6f time_db_dup: %.6f time_api_request: %.6f time_image: %.6f time_message: %.6f" % tuple(times_))
        sleep(5)

def shouldIPost(con, elem, dups, maxPostTime):
    #return True
    #lastDup = dups[-1]
    datetime, userurl, userid, link, title = dups[-1]
    to, tn = (elem[u'title'].lower().strip(), title.lower().strip())
    levn = levenshtein_n(to, tn)
    # TODO: make this readable    
    return (
                time() < elem[u'datetime'] + maxPostTime
                and (
                     not (
                          # TODO: use userblacklist by id plus names till all entries have ids
                          ( elem[u'account_url'] is not None and con.is_user_blocked(int(elem[u'account_id'])))
                          #or ( userurl is not None and lastDup[1].lower() in userBlackList )
                     )
                ) 
                and (
                     levn < 0.4 or (
                                        abs(elem[u'datetime']-datetime) < 60*60*24*60         # time diff < 60 days
                                        and u'mrw' not in elem[u'title'].lower().split(u' ')    # not mrw
                                        and u'mfw' not in elem[u'title'].lower().split(u' ')    # not mfw
                                        and not elem[u'title'].lower().startswith(u'when')      # not start with when
                                    )
                     
                )
                # TODO: drop this when all user have an userid
                and (elem[u'account_url'] is None or elem[u'account_url'] != userurl)
                and (elem['account_id'] != 0 or elem['account_id'] != userid)
            )

def request(factory, imgurApi, data, kdata=None, times=5, delay=30):
    req = factory.buildRequest(data, kdata)                
    for j in xrange(times):
        try:
            res = imgurApi.retrieve(req)
            break
        except Exception as e:
            lognprint("EXCEPTION requesting '%s' : " % str(kdata), e)
            sleep(delay)
            lognprint("Retry #", j+1)
    else:
        lognprint("Connection problems")
        return False
    return res

from os.path import isfile
from os import remove
import math
def main():
    if isfile('.lock'):
        lognprint("Already running")
        exit(0)
    lock = open(".lock", "wb")
    lock.write(str(time()))
    lock.close();
    
    lognprint_base("#"*80+"\n")
    lognprint("START", strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()))
    lognprint_base("#"*80+"\n")  
    
    
    
    # open our db and stuff
    connection = DBConnector("test", re_analyze=False)
    dupcheck = SimilarImagesSql(None, connection)
    config = None
    try:
        fd = open('config.json', 'r')
    except:
        lognprint("config file [config.json] not found.")
        sys.exit(1)
    try:
        config = json.loads(fd.read())
    except:
        lognprint("invalid json in config file.")
        sys.exit(1)
    factory = Factory(config)
    imgurApi = factory.buildAPI()
    commenter = CommentSender(factory, config, 40)
    commentTask = commenter.startSendLoop()


    
    # Adding user ids from our blocked ids file.
    # This isn't really secure but works so far.
    # The file is cleared after adding.
    lognprint("Adding user from blocked.txt")
    fd = open("blocked.txt", "rb+")
    for line in fd:
        line = line.strip()
        try:
            lognprint("Add user with id %s to blocklist" % line)
            connection.add_blocked_user(int(line)) 
        except Exception as e:
            lognprint("Problem adding user to blocklist:", e)
    fd.truncate(0)
    fd.close()
    # Same for user who wishe to be unblocked.
    lognprint("Removing user from unblocked.txt")
    fd = open("unblocked.txt", "rb+")
    for line in fd:
        line = line.strip()
        try:
            lognprint("Unblock user with id %s" % line)
            lognprint("Status: ", connection.remove_blocked_user(int(line))) 
        except Exception as e:
            lognprint("Problem unblocking user:", e)
    fd.truncate(0)
    fd.close()


    # used for debugging. Not used atm (TODO: REMOVE and use profiler if required ?!?)
#     ret = dict()
#     debug = False
#     if debug:
#         connection.galerieExists = Timing.funcHook(connection.galerieExists, ret)
#         connection.commit = Timing.funcHook(connection.commit, ret)
#         connection.execute = Timing.funcHook(connection.execute, ret)
#         connection.getByAvg = Timing.funcHook(connection.getByAvg, ret)
#         connection.getByCrc = Timing.funcHook(connection.getByCrc, ret)
#         connection.insertImage = Timing.funcHook(connection.insertImage, ret)
#         
#         ImageHash.aHash_256 = Timing.funcHook(ImageHash.aHash_256, ret)
#         ImageHash.dHash_256_h = Timing.funcHook(ImageHash.dHash_256_h, ret)
#         ImageHash.dHash_256_v = Timing.funcHook(ImageHash.dHash_256_v, ret)

    
    # Crawl the tops of the day from the different galleries, and reanalyze the db, as something seems to get messed up with the indices TODO: check what
    for i in updateGallery(factory, imgurApi, dupcheck, commenter, pages=4, start=0, gType="user", timeD="day"): commentTask.next()
    #for i in updateGallery(factory, imgurApi, dupcheck, commenter, 3, start=0, gType="user", timeD="day"): commentTask.next()
    connection.execute("ANALYZE;")
    #for i in updateGallery(factory, imgurApi, dupcheck, commenter, 2, start=4, gType="user", timeD="day"): commentTask.next()
    for i in updateGallery(factory, imgurApi, dupcheck, commenter, pages=4, start=0, gType="hot", timeD="day"): commentTask.next()
    #for i in updateGallery(factory, imgurApi, dupcheck, commenter, 3, start=0, gType="hot", timeD="day"): commentTask.next()
    connection.execute("ANALYZE;")
    for i in updateGallery(factory, imgurApi, dupcheck, commenter, pages=4, start=0, gType="top", timeD="day"): commentTask.next()
    #for i in updateGallery(factory, imgurApi, dupcheck, commenter, 3, start=0, gType="top", timeD="day"): commentTask.next()
    connection.execute("ANALYZE;")

    
    # Add old entries. Pretty dirty but works (kind of)
    tstep, hstep, nstep = (4, 4, 4)
    #tstep, hstep, nstep = (5, 5, 5)
    tstart, hstart, nstart = json.load(open('borders', 'rb')) 
    #map(int, bfile.read().split(';'))
    for i in updateGallery(factory, imgurApi, dupcheck, commenter, tstep, start=tstart, gType="top", timeD="all", post=True): commentTask.next()
    connection.execute("ANALYZE;")
    for i in updateGallery(factory, imgurApi, dupcheck, commenter, hstep, start=hstart, gType="hot", timeD="all", post=True): commentTask.next()
    connection.execute("ANALYZE;")
    for i in updateGallery(factory, imgurApi, dupcheck, commenter, nstep, start=nstart, gType="user", timeD="all", post=True): commentTask.next()
    connection.execute("ANALYZE;")
    # save the sites from which to crawl at the next run         
    json.dump([(tstart+tstep)%2000, (hstart+hstep)%800, (nstart+nstep)%2000], open('borders', 'wb') )
    
    w, m, y = json.load(open('borders_wmy', 'rb'))
    for i in updateGallery(factory, imgurApi, dupcheck, commenter, 4, start=w, gType="top", timeD="week", post=True): commentTask.next()
    connection.execute("ANALYZE;")
    for i in updateGallery(factory, imgurApi, dupcheck, commenter, 4, start=m, gType="top", timeD="month", post=True): commentTask.next()
    connection.execute("ANALYZE;")
    for i in updateGallery(factory, imgurApi, dupcheck, commenter, 4, start=y, gType="top", timeD="year", post=True): commentTask.next()
    connection.execute("ANALYZE;")
    json.dump([(w+4)%1000, (m+4)%2000, (y+4)%3000], open('borders_wmy', 'wb') )


    while len(commenter.queue) > 0:
        sleep(1)
        commentTask.next()


    # check notifications and scan posts where they occured.
    # TODO: this is ugly as hell and should also move somewhere else.
    dcommenter = commenter.commenter #DirtyCommenter(factory, config)
    notifies = dcommenter.sendAuthReqMessage('3/notification.json?new=true', retries=3)
    n = 0
    img_con_id = -1 
    notis = list()
    if notifies:
        for noti in notifies['messages']:
            nid = noti['id']
            noti = noti['content']
            if noti['with_account'] == u"48" and u"mentioned you in a comment" in noti["last_message"]:
                notis.append(nid)
                n += 1
                img_con_id = noti["id"]
    for i in xrange(1, 100):
        if n <= 0: break
        img_con = dcommenter.sendAuthReqMessage(('conversations', str(img_con_id), str(i)), retries=3)
        for message in img_con["messages"][::-1]:
            if n <= 0: break          
            if not u"mentioned you in a comment" in message["body"]:
                continue
            n -= 1
            image_id = re.search("glory at http://imgur\.com/gallery/([a-zA-Z0-9]+)/comment/[0-9]+/", message["body"])
            if not image_id:
                lognprint("Unparsable imgur notification '%s'" % str(message))
                continue
            image_id = image_id.group(1)
            if connection.already_commented(image_id):
                lognprint("Got notify for %s but already commented." % str(image_id))
                continue
            if connection.galerieExists(image_id):
                ori, dups = connection.get_reposts_by_image_hash(image_id)
                dups = list(dups)
                print "dup len", len(dups), dups
                if len(dups) <= 0:
                    lognprint("Got notify for %s but is no repost." % str(image_id))
                    continue
                #g.datetime, g.userurl, g.userid, g.link, g.title
                newE = {'datetime':ori[0], "account_id":ori[2], "id":image_id, "title":ori[4] }
                sendDupMessage(newE, dups, commenter, connection, connection.is_animated_by_hash(image_id))
                connection.commit()
                continue
            res = request(factory, imgurApi, ('gallery', 'image', str(image_id)), times=2, delay=20)
            sleep(20)
            if not res: continue
            if update_elem(res, factory, imgurApi, dupcheck, commenter, [[0]*5, [0]*6], 60*60*24*365*5, alwaysPost=True):
                lognprint("Successfuly summoned at %s." % image_id)
            else:
                lognprint("Failed summoning at %s." % image_id)
            connection.commit()
                
    if len(notis) > 0: img_con = dcommenter.sendAuthReqMessage(('notification',), {"ids":",".join(map(str, notis))}, retries=3)

    # Write out all remaining comments from the queue
    while len(commenter.queue) > 0:
        sleep(1)
        commentTask.next()


    


    # print some debuggin infos    
    lognprint("Current images indexed:", connection.getImageCount())
    lognprint('Oldest image', (time()-connection.getOldestImage())/31536000.0, 'years')
    lognprint('client_remaining', imgurApi.ratelimit.client_remaining)
    lognprint('user_remaining', imgurApi.ratelimit.user_remaining)
    lognprint('user_reset', imgurApi.ratelimit.user_reset - time(), 'seconds')
    
    # Get the current points, because i like statistics :)
    imgur = factory.buildAPI()  
    req = factory.buildRequest(('account', 'RepostStatistics'))
    ret = imgur.retrieve(req)['reputation']
    d = json.load(open('points', 'r'))
    d.append((time(), ret))
    json.dump(d, open('points', 'w'))
    lognprint('Points', ret)
    
    lognprint('Reposts: %i' % connection.getReprostCount())
    lognprint('blocked user:', connection.execute('SELECT count() from blocked_user;').fetchone())
    
    # I updated the database format some times, so we need to get the additional data for the old posts.
    # This shows how much entries still need updates. TODO:
    comments = connection.execute('SELECT count() from comments;').fetchone()[0]
    lognprint('comments written:', comments, "-", comments*2)
    lognprint('noUserId:', connection.execute('SELECT count() from galeries where userid = 0;').fetchone())
    lognprint('noSize:', connection.execute('SELECT count() from images where size = 0;').fetchone())
    lognprint('noWidth:', connection.execute('SELECT count() from images where width = -1;').fetchone())
    lognprint('noHeight:', connection.execute('SELECT count() from images where height = -1;').fetchone())
    
    
    
    #remove(".lock")

if __name__ == '__main__':        
#     exit()
    try:
        main()
    except Exception as e:
        lognprint("Last hope catcher: Exception:", format_exc())
    remove(".lock")
        
