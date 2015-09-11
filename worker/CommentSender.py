from Imgur.DirtyCommenter import DirtyCommenter
from collections import deque
from time import time
from urllib import urlencode, quote


#
# TODO:
# - Use maxlen for the deque to auto drop at large deque, or check and return false if deque is full ?
#

def lognprint(*args):
    print 'CommentSender:', args

class CommentSender(object):
    """
    Contains a generator to send comments from a queue
    Job format: DEPRECATED
    (galleryId, message, retries, parentCommentId, (child comment))
    (galleryId, message, retries, parentCommentId )
    (galleryId, message, retries, -1)
    # This should be the correct one
    (TYPE_COMMENT_OR_REPLY, galleryId, message, retries, -1)
    (TYPE_TAG, galleryId, tag, retries, upvote (boolean))
    """
    
    TYPE_COMMENT_OR_REPLY = 1
    TYPE_TAG = 2
    
    def __init__(self, factory, config, commentWait=60, failWait=120):
        self.run = False
        self.lastPost = 0
        self.commentWait, self.failWait = commentWait, failWait
        self.queue = deque()
        self.commenter = DirtyCommenter(factory, config)
        
    def startSendLoop(self):
        self.run = True
        queue = self.queue
        commenter = self.commenter
        curWait = self.commentWait
        while self.run:
            t = time()
            if len(queue) == 0 or t-self.lastPost < curWait:
                yield False
                continue
            self.lastPost = t
            msg = queue.popleft()
            if msg[0] == self.TYPE_COMMENT_OR_REPLY:
                if msg[4] == -1:
                    commentId = commenter.writeComment(msg[1], msg[2], 1)
                else:
                    commentId = commenter.writeReply(msg[1], msg[4], msg[2], 1)         
                if commentId == False:
                    if msg[3] < 1:
                        raise Exception("Max retries for comment send:", msg)
                    lognprint('%i retries remaining to send comment: %s' % (msg[3]-1, msg))
                    msg[3] -= 1
                    queue.appendleft(msg)
                    curWait = self.failWait
                    continue
                curWait = self.commentWait
                if len(msg) == 6:
                    msg[5][4] = commentId
                    queue.appendleft(msg[5])
            elif msg[0] == self.TYPE_TAG:
                ret = commenter.sendAuthReqMessage(('gallery', msg[1], "vote",  "tag", msg[2], ("up" if msg[4] else "down")), {}, retries=1)
                #lognprint(u"Tag send response from",  msg[1], ret)
                if not ret:
                    if msg[3] < 1:
                        raise Exception("Max retries for tag send:", msg)
                    lognprint('%i retries remaining to send tag: %s' % (msg[3]-1, msg))
                    msg[3] -= 1
                    queue.appendleft(msg)
                    curWait = self.failWait
                else:
                    curWait = self.commentWait
            yield True


    # TODO: use this 1 11
    def appendComment(self, galleryId, message, retries, parentCommentId=-1, childComment=None):
        if childComment:            
            self.queue.append([self.TYPE_COMMENT_OR_REPLY, galleryId, message, retries, parentCommentId, childComment])
        else:
            self.queue.append([self.TYPE_COMMENT_OR_REPLY, galleryId, message, retries, parentCommentId])
    
    def appendTag(self, gallery, tag, retries, upvote=True):
        self.queue.append([self.TYPE_TAG, gallery, quote(tag), retries, upvote])

if __name__ == '__main__':
    import sys
    import json
    from Imgur.Factory import Factory
    
    
        
    config = None
    try:
        fd = open('../config.json', 'r')
    except:
        lognprint("config file [config.json] not found.")
        sys.exit(1)
    try:
        config = json.loads(fd.read())
    except:
        lognprint("invalid json in config file.")
        sys.exit(1)
    factory = Factory(config)
    
    sender = CommentSender(factory, config, 30)
    sender.appendComment('z2slH3u', 'message', 1)
    for i in sender.startSendLoop(): pass
    