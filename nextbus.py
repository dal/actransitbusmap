#!/bin/env python3

import logging
import requests
import pprint

api_token = 'DFA4FA38EC8C5A618B1A8A3E67DFCEE0'

baseUri = 'https://api.actransit.org/transit'

routeStopMap = { '19'  : 'Buena Vista Av & Willow St',
                 '51A' : 'Santa Clara Av & Willow St',
                 '20'  : 'Park St & Buena Vista Av',
                 '21'  : 'Park St & Buena Vista Av' }

def printError(url, result):
    logging.error("Error fetching '{}': (code {}) {}".format(
        url, result.status_code, result.text))

def doRequest(url):
    res = requests.get(url)
    if res.status_code == 200:
        return res.json()
    printError(url, res)

def getDirections(route=19):
    url = '{baseUri}/actrealtime/direction?rt={route}&token={api_token}'\
          .format(baseUri=baseUri, route=route, api_token=api_token)
    return doRequest(url)

def getAllStops(route=19):
    url = '{baseUri}/actrealtime/allstops?rt={route}'\
          '&token={api_token}'.format(baseUri=baseUri, 
                                      route=route,
                                      api_token=api_token)
    return doRequest(url)

def getPattern(route=19):
    url = '{baseUri}/actrealtime/pattern?rt={route}&token={api_token}'\
          .format(baseUri=baseUri, route=route, api_token=api_token)
    return doRequest(url)

def getPrediction(route, stopId):
    url = '{baseUri}/actrealtime/prediction?'\
          'stpid={stopId}&rt={route}&token={api_token}'.format(
            baseUri=baseUri, stopId=stopId, route=route, api_token=api_token
          )
    return doRequest(url)

def getVehicles(route=19):
    url = '/{}/route/{}/vehicles/?token={}'.format(baseUri, route, api_token)
    return doRequest(url)

def parsePatternResponse(json, stopName):
    """Parse a JSON response from getPattern() and return a dict of the form
    { <direction> : <stopId>, . . . }
    """
    stopIds = {}
    if not json:
        return stopIds
    if not 'bustime-response' in json:
        return stopIds
    if not 'ptr' in json['bustime-response']:
        return stopIds
    for ptr in json['bustime-response']['ptr']:
        if not 'rtdir' in ptr or not 'pt' in ptr:
            continue
        for stop in ptr['pt']:
            if stop.get('stpnm') == stopName:
                stopIds[ptr['rtdir']] = stop['stpid']
    return stopIds

def parseStopIdResponse(json, matchStr):
    if not json:
        return None
    if 'bustime-response' in json:
        if 'stops' in json['bustime-response']:
            for stop in json['bustime-response']['stops']:
                if 'stpnm' in stop and 'stpid' in stop and \
                    stop['stpnm'] == matchStr:
                    return stop['stpid']
    return None

def parsePredictions(json):
    result = {'errors' : [],
              'predictions': []}
    if not json:
        return result
    if not 'bustime-response' in json:
        return result
    if 'error' in json['bustime-response']:
        for err in json['bustime-response']['error']:
            if 'msg' in err:
                result['errors'].append(err['msg'])
    if 'prd' in json['bustime-response']:
        for prd in json['bustime-response']['prd']:
            if 'prdctdn' in prd:
                result['predictions'].append(prd['prdctdn'])
    return result

if __name__ == '__main__':
    for route, stopName in routeStopMap.items():
        pattern = getPattern(route)
        dirsToStopIds = parsePatternResponse(pattern, stopName)
        print('Line {} {}:'.format(route, stopName))
        for direction, stopId in dirsToStopIds.items():
            predictions = getPrediction(route, stopId)
            predResult = parsePredictions(predictions)
            if predResult['predictions']:
                predStr = ', '.join(['{} min'.format(p) 
                                     for p in predResult['predictions']])
                print('  {}: {}'.format(direction, predStr))
            if predResult['errors']:
                print('  {}: {}'.format(direction, predResult['errors'][0]))
        print('')


    #stopId = parseStopIdResponse(stopIdResponse, 'Buena Vista Av & Willow St')
    #if stopId:
    #    pprint.pprint(getPrediction('19', stopId))
