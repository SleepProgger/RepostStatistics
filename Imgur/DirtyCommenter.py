import json
from time import time, sleep

def lognprint(*args):
    print 'DirtyCommenter', args

class DirtyCommenter(object):
    def __init__(self, factory, config):
        self.config = config
        self.factory = factory
        self.refToken = config['refresh_token']
        self.acToken = 0
        self.validTill = 0
        
    def refreshToken(self):
        imgur = self.factory.buildAPI()
        req = self.factory.buildRequestOAuthRefresh(self.refToken)
        res = imgur.retrieveRaw(req)
                
        lognprint('Access Token: %s\nRefresh Token: %s\nExpires: %d seconds from now.' % (
            res[1]['access_token'],
            res[1]['refresh_token'],
            res[1]['expires_in']
        ))
        self.validTill = time()+res[1]['expires_in'] - 20 # cause i am to lazy to catch timing errors
        self.acToken = res[1]['access_token']
        self.refToken = res[1]['refresh_token']
        self.config['refresh_token'] = self.refToken
        
        with open('config.json', 'w') as cFile:
            json.dump(self.config, cFile)
        
    #
    # ATTENTION: 
    # I replaced the real functions interacting with imgur with dummy functions, to avoid spamming imgur when testing.
    # OFC: you should remove them when in an "stable" state
    # 
    
    def writeComment(self, galerie, text, retries=3):
        lognprint("DUMMY COMMENTER: Write Comment to gallery %s with retries %i: %s" % (galerie, retries, text))
           
    def _writeComment(self, galerie, text, retries=3):
        for i in xrange(retries):
            try:
                if time() >= self.validTill:
                    self.refreshToken()
                
                if len(text) > 140: # TODO split into more messages
                    text = text[:140]
                auth = self.factory.buildOAuth(self.acToken, None, int(time())+3600)
                imgur = self.factory.buildAPI(auth)
                req = self.factory.buildRequest((u'gallery', galerie, u'comment'), {
                    'comment': text.encode('utf-8')
                })
                res = imgur.retrieve(req)
                lognprint(u"Success! https://www.imgur.com/gallery/%s/comment/%s" % (galerie, res['id']))
                return res['id']
            except Exception as e: # TODO catch correct Exception
                # TODO except when message contains "returned empty response with code 200" or send and check error code (what to do whith the already posted db ?))
                lognprint(u'write comment exception', str(e), "at gallery", galerie)
        return False
    
        
    def writeReply(self, galerie, parentId, text, retries=3):
        lognprint("DUMMY COMMENTER: Write Reply to gallery %s, parentid %s, with retries %i: %s." % (galerie, parentId, retries, text))
        
    def _writeReply(self, galerie, parentId, text, retries=3):
        for i in xrange(retries):
            try:
                if time() >= self.validTill:
                    self.refreshToken()
                
                if len(text) > 140: # TODO split into more messages
                    text = text[:140]
                auth = self.factory.buildOAuth(self.acToken, None, int(time())+3600)
                imgur = self.factory.buildAPI(auth)
                req = self.factory.buildRequest(('comment',), {
                    u'comment': text.encode('utf-8'),
                    u'image_id': galerie,
                    u'parent_id': parentId
                })
                res = imgur.retrieve(req)
                lognprint(u"Success! https://www.imgur.com/gallery/%s/comment/%s" % (galerie, res['id']))
                return res['id']
            except Exception as e: # TODO catch correct Exception
                lognprint(u'write reply exception', str(e), "at gallerie", galerie)
        return False
    
    def sendAuthReqMessage(self, endpoint, data=None, retries=1):
        lognprint("DUMMY COMMENTER: Send generic authed message to endpoint %s." % (endpoint,))
        
    def _sendAuthReqMessage(self, endpoint, data=None, retries=1):
        for i in xrange(retries):
            try:
                if time() >= self.validTill:
                    self.refreshToken()
                auth = self.factory.buildOAuth(self.acToken, None, int(time())+3600)
                imgur = self.factory.buildAPI(auth)
                req = self.factory.buildRequest(endpoint, data=data)
                res = imgur.retrieve(req)
                lognprint(u"Success sending", endpoint, data)
                return res
            except Exception as e: # TODO catch correct Exception
                lognprint(u'Exception requesting', endpoint, data, ":", str(e))
        return False
    
    def _msplit_cut_follow(self):
        # []
        pass
    
    def writeComent_(self, gallerie, text, handler=None):
        if handler is None: handler = self._msplit_cut
        text = handler(text)