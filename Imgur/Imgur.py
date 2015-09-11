#!/usr/bin/env python3

from urllib2 import urlopen, HTTPError, URLError

import json
from .Auth.Expired import Expired

class Imgur:
    
    def __init__(self, client_id, secret, auth, ratelimit):
        self.client_id = client_id
        self.secret = secret
        self.auth = auth
        self.ratelimit = ratelimit

    def retrieveRaw(self, request):
        request = self.auth.addAuthorizationHeader(request)
        try:
            req = urlopen(request, timeout=20)
        except URLError as e:
            print e
            return (e, {u'success':False, 'data':{'error':{'message':str(e)}}})
        t = req.read()
#        print "FU", t

        if not t:
            return (req, {u'success':False,'data':{'error':{'message':'%s returned empty response with code %i and content "%s"' % (request.get_full_url(), req.getcode(), str(t))}}})
        res = json.loads(t.decode('utf-8'))
        return (req, res)

    def retrieve(self, request):
        try:
            (req, res) = self.retrieveRaw(request)
        except HTTPError as e:
            if e.code == 403:
                raise Expired()
            else:
                print("Error %d\n%s\n" % (e.code, e.read()))
                raise e

        self.ratelimit.update(req.info())
        if res['success'] is not True:
            if 'data' in res and 'error' in res['data']: 
                raise Exception(res['data']['error']['message'])
            raise Exception("Empty return: %s / %s" % (str(res), str(req)))

        return res['data']

    def getRateLimit(self):
        return self.ratelimit

    def getAuth(self):
        return self.auth
    
    def getClientID(self):
        return self.client_id