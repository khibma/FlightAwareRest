# Kevin Hibma, Esri.
#
# API:
#    http://flightaware.com/commercial/flightxml/explorer/
# Time conversion:
#    https://github.com/fredpalmer/flightaware/blob/master/flightaware/client.py
# Passing username/key as base64:
#    http://stackoverflow.com/questions/635113/python-urllib2-basic-http-authentication-and-tr-im
#


import os
import json
import datetime
import base64

try:  # py3
    import http.client as client
    import urllib.parse as parse
    from urllib.request import urlopen as urlopen
    from urllib.request import Request as request
    from urllib.parse import urlencode as encode
except ImportError:  # py2
    import httplib as client
    from urllib2 import urlparse as parse
    from urllib2 import urlopen as urlopen
    from urllib2 import Request as request
    from urllib import urlencode as encode


# Current costs per query by class as of June 24, 2015. 
# Costs are provided as an estimate only and are not guaranteed to be 100% accurate
COST = {'cl0': 0.0,
        'cl1': 0.012,
        'cl2': 0.0079,
        'cl3': 0.0020,
        'cl4': 0.0008
        }


def from_unix_timestamp(val):
    # Date/Time from FA = UTC
    # This returns a timestruct. Could add .strftime("%Y-%m-%d %H:%M")
    return datetime.datetime.fromtimestamp(val)


class FA_REST(object):

    def __init__(self, USERNAME, KEY, MAXRESULTSIZE=15):

        self.URL = "http://flightxml.flightaware.com/json/FlightXML2"
        self.username = USERNAME
        self.apiKey = KEY
        base64string = base64.encodestring('%s:%s' % (self.username, self.apiKey)).replace('\n', '')
        self.header = {"Authorization": "Basic {}".format(base64string)}
        self.maxResultSize = self.setMaxResultSize(MAXRESULTSIZE)

        self.reqCt = {'cl0': 0,
                      'cl1': 0,
                      'cl2': 0,
                      'cl3': 0,
                      'cl4': 0}
        self.money = 0.0

        self.arrivals = []
        self.departures = []

    def setMaxResultSize(self, maxSize):
        ''' Set the max result size
            This value initialized on start up, but can be called independently
        '''

        reqURL = self.URL + '/SetMaximumResultSize'
        qdata = {'max_size': maxSize,
                 'f': 'json'}

        response = self.sendReq(reqURL, qdata, self.header)
        if "SetMaximumResultSizeResult" not in response:
            print("Could not set maxResultSize:")
            print(response)

        return response

    def cost(self, cls, count=1):
        ''' Keep track of running queries and the cost
            NOTE - A single req can return up to 15 'howMany'. If howMany is higher than 15
              logic needs to be implemented in the calling funcs to send a proper count
        '''

        self.reqCt[cls] += count
        self.money += (COST[cls] * count)
        #print ("Counts: {0} / Cost: {1} ").format(sum(self.reqCt.values()), self.money)

    def sendReq(self, URL, query_dict=None, headers=None):
        # Takes a URL and a dictionary and sends the request, returns the JSON
        # qData = parse.urlencode(qDict).encode('UTF-8') if qDict else None

        if query_dict:
            query_string = encode(query_dict).encode('UTF-8')
        else:
            query_string = encode('').encode('UTF-8')

        if headers:
            req = request(URL)
            for key, value in headers.iteritems():
                req.add_header(key, value)
        else:
            req = URL

        jsonResponse = urlopen(req, query_string)
        jsonOuput = json.loads(jsonResponse.read().decode('utf-8'))

        return jsonOuput

    def getArrivals(self, airport, offset, maxQuery, queryPerReq):
        ''' Class 2 level query (0.0079)
            This function parses the response and returns a list of arrived flights
        '''

        reqURL = self.URL + '/Arrived'

        qdata = {'airport': airport,
                 'howMany': queryPerReq,
                 'filter': 'airline',
                 'offset': offset,  # use offset if theres more to be queried
                 'f': 'json'}

        response = self.sendReq(reqURL, qdata, self.header)
        self.cost('cl2', 1)
        self.arrivals.extend(response['ArrivedResult']['arrivals'])

        if len(self.arrivals) >= maxQuery: return

        if response['ArrivedResult']['next_offset'] > 0:
            nextOffSet = response['ArrivedResult']['next_offset']
            self.getArrivals(airport, nextOffSet, maxQuery, queryPerReq)

        return

    def getDepartures(self, airport, offset, maxQuery, queryPerReq):
        ''' Class 2 level query (0.0079)
            This function parses the response and returns a list of departed flights
        '''

        reqURL = self.URL + '/Departed'
        qdata = {'airport': airport,
                 'howMany': queryPerReq,
                 'filter': 'airline',
                 'offset': offset,  # use offset if theres more to be queried
                 'f': 'json'}

        response = self.sendReq(reqURL, qdata, self.header)
        self.cost('cl2', 1)

        self.departures.extend(response['DepartedResult']['departures'])

        if len(self.departures) >= maxQuery: return

        if response['DepartedResult']['next_offset'] > 0:
            nextOffSet = response['DepartedResult']['next_offset']
            self.getDepartures(airport, nextOffSet, maxQuery, queryPerReq)

        return

    def getFlightInfo(self, ident, howMany):
        ''' Class 3 level query (0.002)'''

        reqURL = self.URL + '/FlightInfoEx'
        qdata = {'ident': ident,
                 'howMany': howMany,
                 'f': 'json'}

        response = self.sendReq(reqURL, qdata, self.header)
        self.cost('cl3', 1)
        return response

    def getFlightLastTrack(self, ident, retry=True):
        ''' Class 2 level query (0.0079)
            This function returns detailed geographic data about a flight
        '''

        reqURL = self.URL + '/GetLastTrack'
        qdata = {'ident': ident,
                 'f': 'json'}
        try:
            response = self.sendReq(reqURL, qdata, self.header)
            self.cost('cl2', 1)
            return response
        except:
            if retry:
                print("Trying to get flight track again...")
                self.getFlightLastTrack(ident, False)
            print("Failed in requesting ident: {0}").format(ident)
            return
