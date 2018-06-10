"""
PURPOSE: send request communications to a ladder server

    sendMatchResult()

    requestMatch()
        find matchup
        listen for matchup assignment
        launch client using assignment info
        issue commands as assigned
        play game
            if W, agent app result code  = 0
            else  agent app result code != 0
        reportResult() to ladder

    export / publish data
        standings by W/L
        standings by games played / sportsmanship rating
        hottest streak in standings w/ 5+ games
        service getPlayerData() request (provide info about a ladder's players)
"""

from six import iteritems # python 2/3 compatibility

import json
import requests

from sc2gameLobby import gameConstants as c
from sc2players import addPlayer, getPlayer


################################################################################
def cancelMatchRequest(cfg):
    """obtain information housed on the ladder about playerName"""
    payload = json.dumps([cfg.thePlayer])
    ladder = cfg.ladder
    return requests.post(
        url  = c.URL_BASE%(ladder.ipAddress, ladder.serverPort, "cancelmatch"),
        data = payload,
        #headers=headers,
    )


################################################################################
def ladderPlayerInfo(cfg, playerName, getMatchHistory=False):
    """obtain information housed on the ladder about playerName"""
    payload = json.dumps([playerName, getMatchHistory]) # if playerName == None, info on all players is retrieved
    ladder = cfg.ladder
    x = requests.post(
        url  = c.URL_BASE%(ladder.ipAddress, ladder.serverPort, "playerstats"),
        data = payload,
        #headers=headers,
    )
    #print("z.text", x.text) # this holds the response content
    #print("z.ok", x.ok)
    #print("z.reason", x.reason)
    if x.ok:    return x.json()
    else:       return x.ok


################################################################################
def reportMatchCompletion(cfg, results, replayData):
    """send information back to the server about the match's winners/losers"""
    payload = json.dumps([cfg.flatten(), results, replayData])
    ladder = cfg.ladder
    x = requests.post(
        url  = c.URL_BASE%(ladder.ipAddress, ladder.serverPort, "matchfinished"),
        data = payload,
        #headers=headers,
    )
    print(x.reason)
    print(x.text)
    if x.ok:    return x.json()
    else:       return x.ok


################################################################################
def sendMatchRequest(cfg):
    payload = cfg.toJson()
    ladder = cfg.ladder
    x = requests.post(
        # force error #url  = c.URL_BASE%(ladder.ipAddress, ladder.serverPort, "polls"),
        url  = c.URL_BASE%(ladder.ipAddress, ladder.serverPort, "newmatch"),
        data = payload,
        #headers=headers,
    )
    #print("x", x)
    #print("dir(x)", dir(x))
    #print("x.raw", x.raw)
    #print("x.url", x.url)
#    print("x.text", x.text) # this holds the response content
#    print("x.ok", x.ok)
#    print("x.reason", x.reason)
    if not x.ok:    return x.ok
    data = x.json()
    for pData in data["players"]: # if player matchup doesn't exist locally, retrieve server information and define the player
        pName = pData[0]
        try:    getPlayer(pName) # test whether player exists locally
        except ValueError: # player pName is not defined locally
            y = ladderPlayerInfo(cfg, pName)
            settings = y[0][0] # settings of player[0]
            del settings["created"]
            addPlayer(settings)
    cfg.loadJson(data)
    cfg.display()
    return cfg

