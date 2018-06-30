
"""
Copyright 2018 Versentiedge LLC All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS-IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import absolute_import
from __future__ import division       # python 2/3 compatibility
from __future__ import print_function # python 2/3 compatibility

from six import iteritems # python 2/3 compatibility
from argparse import ArgumentParser

import importlib
import json
import os
import re
import requests
import subprocess
import sys
import time

from sc2common import types as t
from sc2players import getPlayer, getKnownPlayers, PlayerPreGame, PlayerRecord
from sc2ladderMgmt import getLadder, getKnownLadders
from sc2maptool.functions import selectMap, filterMapNames
from sc2gameLobby.__version__ import __version__
from sc2gameLobby.gameConfig import Config
from sc2gameLobby import connectToServer
from sc2gameLobby import gameConstants as c
from sc2gameLobby import genericObservation as go
from sc2gameLobby import host, join
from sc2gameLobby import resultHandler as rh
from sc2gameLobby import versions


################################################################################
def exitStatement(msg, code=1):
    printMsg = msg
    if code: printMsg = "ERROR: %s"%(msg)
    print("%s%s"%(os.linesep, printMsg))
    sys.exit(code)


################################################################################
def badConnect(ladder, code=2):
    exitStatement("A connection could not be made. %s may not be available or "
    "you may not be connected to the internet."%(ladder), code=code)


################################################################################
def getLaunchConfig(options):
    player = PlayerPreGame(getPlayer(options.player), selectedRace=options.race, observe=options.observe)
    ret = Config( # create game config
            expo        = c.EXPO_SELECT[options.exp],
            version     = options.version or versions.handle.mostRecent['version'],
            ladder      = getLadder(options.ladder),
            players     = [player],
            whichPlayer = player.name,
            mode        = t.GameModes(options.mode),
            themap      = options.map,# or selectMap(options.map),
            numObservers= options.obs,
            trust       = True,
           #slaves      = [],
           #agentRaces  = [race.type],
            fogDisabled = options.nofog,
            stepSize    = options.step,
            opponents   = options.opponents.split(',') if options.opponents else [],
            fullscreen  = not options.windowed,
            raw         = options.raw,
            score       = options.score,
            feature     = options.feature,
            render      = options.rendered,
           #resolution
           #minimap
           #layerwidth
            replay      = options.replay,
           #debug       = options.debug,
        )
    ret.connection # force generation of IP address and ports attributes 
    return ret


################################################################################
if __name__ == "__main__":
    ALLOWED_PLAYERS = list(getKnownPlayers())
    ALLOWED_LADDERS = list(getKnownLadders())
    ALLOWED_MAPS    = filterMapNames("", closestMatch=False)
    description = "PURPOSE: front-end interface to easily and reliably match against opponents and run Starcraft2 opponents."
    parser = ArgumentParser(description=description, epilog="version: %s"%__version__)
    gameOptions = parser.add_argument_group('game lobby actions')
    gameOptions.add_argument("--nogui"          , action="store_true"   , help="launch game directly using command-line arguments formatted as key=value.")
    gameOptions.add_argument("--search"         , default=""            , help="retrieve player information from the ladder (comma separated names)", metavar="PLAYERS")
    gameOptions.add_argument("--history"        , action="store_true"   , help="include match history when using the --search option.")
    startOption = parser.add_argument_group('sc2 game client gameplay options')
    startOption.add_argument("-l", "--ladder"   , default="localhost"   , choices=ALLOWED_LADDERS
                                                                        , help="the ladder where the game is run.  Allowed values: " + ", ".join(ALLOWED_LADDERS), metavar='')
    startOption.add_argument("-p", "--player"   , default="defaulthuman", choices=ALLOWED_PLAYERS
                                                                        , help="the player profile the ladder identifies you with.  Allowed values: " + ", ".join(ALLOWED_PLAYERS), metavar='')
    startOption.add_argument("-v", "--version"  , type=int              , help="the specific game version to play.", metavar='')
    startOption.add_argument("-e", "--exp"      , default="lotv", choices=c.EXPO_SELECT.keys(), metavar=''
                                                                        , help="the specific game expansion version to play.  Allowed values: " + ", ".join(c.EXPO_SELECT.keys()))
    startOption.add_argument("-r", "--race"     , default=c.RANDOM, choices=t.SelectRaces.ALLOWED_TYPES, metavar=''
                                                                        , help="selected race to play. Allowed values: " + ", ".join(t.SelectRaces.ALLOWED_TYPES))
    startOption.add_argument("-m", "--mode"     , default=c.MODE_1V1, choices=t.GameModes.ALLOWED_TYPES, metavar=''
                                                                        , help="game mode to play. DEFAULT: %s"%c.MODE_1V1)
    startOption.add_argument("-o", "--obs"      , default=0, type=int   , help="the number of observers that will watch this match for this player", metavar='int')
    startOption.add_argument("--observe"        , action="store_true"   , help="be a match observer, not a participant.")
    localOption = parser.add_argument_group("this individual sc2 client's options")
    localOption.add_argument("--windowed"       , action="store_true"   , help="launch client in windowed mode (default: full screen).")
    localOption.add_argument("--replay"         , action="store_true"   , help="store a replay file after the match finishes.")
    noLadderOpt = parser.add_argument_group('mandate a non-ladder (custom) match')
    noLadderOpt.add_argument("--opponents"      , default=""            , help="specify specific opponent(s), comma separated.", metavar='LIST')
    noLadderOpt.add_argument("--nofog"          , action="store_true"   , help="disable fog of war.")
    noLadderOpt.add_argument("--map"            , default=None          , help="play on a specific map.", metavar='MAPNAME')
    noLadderOpt.add_argument("--step"           , default=0, type=int   , help="the number of steps between step() actions.  A zero value means that the game runs in realtime (default)", metavar='int')
    aiBotOption = parser.add_argument_group("observation response contents for AI / bots")
    aiBotOption.add_argument("--raw"            , action="store_true"   , help="return raw data in observations")
    aiBotOption.add_argument("--feature"        , action="store_true"   , help="return feature data in observations.")
    aiBotOption.add_argument("--rendered"       , action="store_true"   , help="return fully rendered data in observations.")
    aiBotOption.add_argument("--score"          , action="store_true"   , help="return current score data in observations.")
    aiBotOption.add_argument("--resolution"     , default=""            , help="resolution that the feature/rendered data is returned in.", metavar='AxB')
    aiBotOption.add_argument("--minimap"        , default=""            , help="resolution that the feature/rendered minimap data is returned in.", metavar='AxB')
    aiBotOption.add_argument("--layerwidth"     , type=int, default=24  , help="the mapping of number of pixels to game grid coordinates.", metavar='int')
    # TODO -- add all other options
    versionOpts = parser.add_argument_group('sc2 game client version handling')
    versionOpts.add_argument("--update"         , type=str,default=""   , help="update an existing version.", metavar='<label>,<version>,<base-version>')
    versionOpts.add_argument("--add"            , type=str,default=""   , help="add a new version.", metavar='<label>,<version>,<base-version>')
    versionOpts.add_argument("--versions"       , action="store_true"   , help="display known Starcraft 2 public versions.")
    options = parser.parse_args()
    sys.argv = sys.argv[:1] # remove all arguments to avoid problems with absl FLAGS :(
    if options.search or options.history:
        if not options.player: options.player = options.search
        cfg = getLaunchConfig(options)
        try: httpResp = connectToServer.ladderPlayerInfo(cfg, options.search, getMatchHistory=options.history)
        except requests.exceptions.ConnectionError as e: badConnect(cfg.ladder)
        if not httpResp.ok: exitStatement(httpResp.text)
        printStr = "%15s : %s"
        for playerAttrs, playerHistory in httpResp.json():
            player = PlayerRecord(source=playerAttrs)
            print(player)
            for k in ["type", "difficulty", "initCmd", "rating"]:
                print(printStr%(k, getattr(player, k)))
            if "created" in playerAttrs:    print(printStr%("created", time.strftime('%Y-%m-%d', time.localtime(player.created))))
            if playerHistory: # TODO -- do something with playerHistory, when implemented
                for h in playerH:   print(printStr%("history", h))
            print()
    elif options.nogui:
        cfg = getLaunchConfig(options)
        if False: # only display in debug/verbose mode?
            print("REQUESTED CONFIGURATION")
            cfg.display()
            print(cfg.whoAmI().initCmd)
            print()
        try:    httpResp = connectToServer.sendMatchRequest(cfg)
        except requests.exceptions.ConnectionError as e: badConnect(cfg.ladder)
        ### cancel match request ### (would have to be issued as subprocess after match request, but before a match is assigned
            #import time
            #time.sleep(1)
            #print(connectToServer.cancelMatchRequest(cfg).text)
        if not httpResp.ok: exitStatement(httpResp.text)
        data = httpResp.json()
        for pData in data["players"]: # if player matchup doesn't exist locally, retrieve server information and define the player
            pName = pData[0]
            try:    getPlayer(pName) # test whether player exists locally
            except ValueError: # player w/ name pName is not defined locally
                try: y = connectToServer.ladderPlayerInfo(cfg, pName) # get player info from ladder
                except requests.exceptions.ConnectionError as e: badConnect(cfg.ladder)
                settings = y[0][0] # settings of player[0]
                del settings["created"] # creation data is retained locally
                addPlayer(settings) # ensures that loading json + inflation succeeds
        matchCfg = Config()
        matchCfg.loadJson(data)
        print("SERVER-ASSIGNED CONFIGURATION")
        matchCfg.display()
        print()
        ### launch game; collect results ###
        thisPlayer = matchCfg.whoAmI()
        agentStuff = [] # preserve python agent info (if applicable)
        result     = None
        replayData = ""
        callBack   = go.doNothing # play with human control only (default) 
        if thisPlayer.initCmd: # launch the desired player appropriately
            if re.search("^\w+\.[\w\.]+$", thisPlayer.initCmd): # found a python command; extract callback and agent process/object stuff
                parts = thisPlayer.initCmd.split(".")
                moduleName = parts[0]
                try:
                    thing = importlib.import_module(moduleName)
                    for part in parts[1:]: # access callable defined by the agent
                        thing = getattr(thing, part)
                    agentStuff = thing() # execute to acquire a list of the callback and any additional, to-be-retained objects necessary to run the agent process 
                    callBack = agentStuff[0] # callback is always first item in list
                except ModuleNotFoundError as e:    exitStatement("agent %s initialization command (%s) did not begin with a module (expected: %s). Given: %s"%(thisPlayer.name, thisPlayer.initCmd, moduleName, e))
                except AttributeError as e:         exitStatement("invalid %s init command format (%s): %s"%(thisPlayer, thisPlayer.initCmd, e))
                except Exception as e:              exitStatement("general failure to initialize agent %s: %s %s"%(thisPlayer.name, type(e), e))
            else: # launch separate process that manages the agent and results
                p = subprocess.Popen(thisPlayer.initCmd.split())
                p.communicate()
                msg = "Command-line bot %s finished normally."%(thisPlayer)
                if p.returncode: # otherwise rely on client to send game result to server (else server catches the non-reporting offender)
                    msg = "Command-line bot %s crashed (%d)."%(thisPlayer, p.returncode)
                    try: # while non-python agent manages communication including match completion reporting to ladder server, some crash events can be reported by this process
                        httpResp = connectToServer.reportMatchCompletion(matchCfg, result, replayData)
                        if not httpResp.ok: msg += " %s!"%(httpResp.text)
                    except requests.exceptions.ConnectionError as e: # process can't report game result if it crashes
                        msg += " lost prior connection to %s!"%(cfg.ladder)
                exitStatement(msg, code=p.returncode)
        try:
            if matchCfg.host: # host contains details of the host to connect to
                  func = join # join game on host when host details are provided
            else: func = host # no value means this machine is hosting
            result,replayData = func(matchCfg, agentCallBack=callBack, debug=False)
        except c.TimeoutExceeded as e: # match failed to launch
            print(e)
            result = rh.launchFailure(matchCfg) # report UNDECIDED results
        finally:
            for item in agentStuff: # eradicate all agent's processes
                if hasattr(item, "terminate"): item.terminate()
            agentStuff = []
        ### simulate sending match results ###
            #results = []
            #from numpy.random import choice
            #from time import sleep
            #import json
            #print("*"*80)
            #for i,p in enumerate(matchCfg.players):
            #    playerName = p.name
            #    if i%2: results.append( [playerName, int(not results[-1][1])] )
            #    else:   results.append( [playerName, int(choice([0, 1]))] )
            #sleep(1.5)
            #results = dict(results)
            #print(json.dumps(results, indent=4))
            #try:
            #    httpResp = connectToServer.reportMatchCompletion(matchCfg, results, "")
            #    if not httpResp.ok: exitStatement(httpResp.text)
            #except requests.exceptions.ConnectionError as e: badConnect(cfg.ladder)
            #print(httpResp.json())
        ### send actual results ###
        replaySize = len(replayData) if replayData else 0
        print("FINAL RESULT: (%d)"%(replaySize))
        print(json.dumps(result, indent=4))
        if result != None: # regular result is expected to be reported by
            try:
                httpResp = connectToServer.reportMatchCompletion(matchCfg, result, replayData)
                if not httpResp.ok: exitStatement(httpResp.text)
            except requests.exceptions.ConnectionError as e: badConnect(cfg.ladder)
            print(httpResp.json()) # also display effective rating changes 
    elif options.add:       versions.addNew(*options.add.split(','))
    elif options.update:
        keys = [
            "label",
            "version",
            "base-version",
            "data-hash",
            "fixed-hash",
            "replay-hash",
        ]
        data = {}
        for k,v in zip(keys, options.update.split(',')):
            data[k] = v
        versions.handle.update(data)
        versions.handle.save()
    elif options.versions: # simply display the jsonData reformatted
        for v,record in sorted(iteritems(versions.handle.ALL_VERS_DATA)):
            print(v)
            for k,v in sorted(iteritems(record)):
                print("%15s: %s"%(k,v))
            print()
    else: # without an action explicitly specified, launch the GUI with selected options
        cfg = getLaunchConfig(options)
        cfg.display()
        print(ALLOWED_PLAYERS)
        print(ALLOWED_LADDERS)
        print(ALLOWED_MAPS)
        # TODO -- launch GUI that manages communication to server
        print("ERROR: GUI mode is not yet implemented.")

