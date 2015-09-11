import urllib2
import socket
from time import sleep

def lognprint(*args):
    pass

# just a little function allowing to retry http requests
# TODO: move this function to somewhere more appropriate
def request(url, data=None, timeout=20, retries=1, retryTime=5):
    for i in xrange(retries):
        try:
            return urllib2.urlopen(url, data, timeout).read()
        except urllib2.HTTPError as e:
            lognprint( "Error requesting %s: %s" % (url, e.reason()) )
        except socket.error as e: 
            lognprint( "Error requesting %s: %s" % (url, str(e)) )
        lognprint( "Retry #", i+1 )
        sleep(retryTime)
    return None

if __name__ == '__main__':
    pass