from Imgur.Factory import Factory
import sys
import json
from urllib2 import HTTPError

def getAndSaveNewToken(factory, config, configPath):
    pin = raw_input('Please visit this URL to get a PIN to authorize: \n' + factory.getAPIUrl() + "oauth2/authorize?client_id=" + config['client_id'] + '&response_type=pin\n and insert that pin.')
    imgur = factory.buildAPI()
    req = factory.buildRequestOAuthTokenSwap('pin', pin)
    try:
        res = imgur.retrieveRaw(req)
    except HTTPError as e:
        print("Error %d\n%s" % (e.code, e.read().decode('utf8')))
        raise e
        
    print("Access Token: %s\nRefresh Token: %s\nExpires: %d seconds from now." % (
        res[1]['access_token'],
        res[1]['refresh_token'],
        res[1]['expires_in']
    ))
    config['refresh_token'] = res[1]['refresh_token']
    json.dump(config, open(configPath, 'w+'))
    return True
    

if __name__ == '__main__':
    config = None
    try:
        fd = open('../config.json', 'r')
    except:
        print("config file [config.json] not found.")
        sys.exit(1)
    try:
        config = json.loads(fd.read())
    except:
        print("invalid json in config file.")
        sys.exit(1)
    factory = Factory(config)
    getAndSaveNewToken(factory, config, '../config.json')