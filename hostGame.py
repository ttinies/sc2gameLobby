
from __future__ import absolute_import
from __future__ import division       # python 2/3 compatibility
from __future__ import print_function # python 2/3 compatibility

from past.builtins import xrange # python 2/3 compatibility

from s2clientprotocol import sc2api_pb2 as sc_pb

from pysc2.lib import protocol
from pysc2.lib import remote_controller
from pysc2.lib.sc_process import FLAGS

import base64
import os
import re
import subprocess
import sys
import time

from sc2common  import types as t
from sc2players import PlayerPreGame

from sc2gameLobby import gameConfig
from sc2gameLobby import gameConstants as c
from sc2gameLobby import replay
from sc2gameLobby import resultHandler as rh

now = time.time


################################################################################
def run(config, agentCallBack, lobbyTimeout=c.DEFAULT_TIMEOUT, debug=False):
    """PURPOSE: start a starcraft2 process using the defined the config parameters"""
    FLAGS(sys.argv)
    thisPlayer = config.whoAmI()
    createReq = sc_pb.RequestCreateGame( # used to advance to "Init Game" state, when hosting
        realtime    = config.realtime,
        disable_fog = config.fogDisabled,
        random_seed = int(now()), # a game is created using the current second timestamp as the seed
        local_map   = sc_pb.LocalMap(map_path=config.mapLocalPath,
                                     map_data=config.mapData) )
    for player in config.players:
        reqPlayer = createReq.player_setup.add() # add new player; get link to settings
        playerObj = PlayerPreGame(player)
        if playerObj.isComputer:
            reqPlayer.difficulty    = playerObj.difficulty.gameValue()
        reqPlayer.type              = t.PlayerControls(playerObj.control).gameValue()
        reqPlayer.race              = playerObj.selectedRace.gameValue()
    interface = sc_pb.InterfaceOptions()
    raw,score,feature,rendered = config.interfaces
    interface.raw   = raw   # whether raw data is reported in observations
    interface.score = score # whether score data is reported in observations
    interface.feature_layer.width = 24
    #interface.feature_layer.resolution = 
    #interface.feature_layer.minimap_resolution =
    joinReq = sc_pb.RequestJoinGame(options=interface) # SC2APIProtocol.RequestJoinGame
    joinReq.race = thisPlayer.selectedRace.gameValue() # update joinGame request as necessary
    # TODO -- allow host player to be an observer, not just a player w/ race
    #joinReq.observed_player_id
    gameP, baseP, sharedP = config.ports
    if config.isMultiplayer:
        joinReq.server_ports.game_port  = gameP
        joinReq.server_ports.base_port  = baseP
        joinReq.shared_port             = sharedP
    for slaveGP, slaveBP in config.slavePorts:
        joinReq.client_ports.add(game_port=slaveGP, base_port=slaveBP)
    if debug: print("Starcraft2 game process is launching (fullscreen=%s)."%(config.fullscreen))
    controller  = None # the object that manages the application process
    finalResult = None # the observed results of the match
    replayData  = None # complete raw replay data for the match
    with config.launchApp(fullScreen=config.fullscreen) as controller:
      try:
        getGameState = controller.observe # function that observes what's changed since the prior gameloop(s)
        if debug: print("Starcraft2 application is live. (%s)"%(controller.status)) # status: launched
        controller.create_game(createReq)
        if debug: print("Starcraft2 is waiting for %d player(s) to join. (%s)"%(config.numAgents, controller.status)) # status: init_game
        playerID = controller.join_game(joinReq).player_id # SC2APIProtocol.RequestJoinGame
        config.updateID(playerID)
        #config.save() # "publish" the configuration file for other procs
        print("[HOSTGAME] player #%d %s"%(playerID, config))
        #try:    agentCallBack(config.name) # send the configuration to the controlling agent's pipeline
        #except Exception as e:
        #    print("ERROR: agent %s crashed during init: %s (%s)"%(thisPlayer.initCmd, e, type(e)))
        #    return (rh.playerCrashed(config), "") # no replay information to get
        startWaitTime = now()
        knownPlayers  = []
        numExpectedPlayers = config.numGameClients # + len(bots) : bots don't need to join; they're run by the host process automatically
        while len(knownPlayers) < numExpectedPlayers:
            elapsed = now() - startWaitTime
            if elapsed > lobbyTimeout: # wait for additional players to join
                raise c.TimeoutExceeded("timed out after waiting for players to "\
                    "join for waiting %.1f > %s seconds!"%(elapsed, lobbyTimeout))
            ginfo = controller.game_info() # SC2APIProtocol.ResponseGameInfo object
                # map_name
                # mod_names
                # local_map_path
                # player_info
                # start_raw
                # options
            numCurrentPlayers = len(ginfo.player_info)
            if numCurrentPlayers == len(knownPlayers): continue # no new players
            for pInfo in ginfo.player_info: # parse ResponseGameInfo.player_info to validate player information (SC2APIProtocol.PlayerInfo) against the specified configuration
                pID = pInfo.player_id
                if pID in knownPlayers: continue # player joined previously
                knownPlayers.append(pID)
                pTyp = t.PlayerControls(pInfo.type)
                rReq = t.SelectRaces(pInfo.race_requested)
                if pID == thisPlayer.playerID: continue # already updated
                for p in config.players: # ensure joined player is identified appropriately
                    if p.playerID: continue # ignore players with an already-set playerID
                    if p.type == pTyp and p.selectedRace == rReq: # matched player
                        config.updateID(pID, p)
                        if debug:   print("%s joined the match."%(p))
                        pID = 0 # declare that the player has been identified
                        break
                if pID: raise c.UknownPlayer("could not match %s %s %s to any "
                    "existing player of %s"%(pID, pTyp, rReq, config.players))
        if debug: print("all %d player(s) found; game has " # status: init_game
            "started! (%s)"%(numExpectedPlayers, controller.status))
        config.save() # "publish" the configuration file for other procs
        try:    agentCallBack(config.name) # send the configuration to the controlling agent's pipeline
        except Exception as e:
            print("ERROR: agent %s crashed during init: %s (%s)"%(thisPlayer.initCmd, e, type(e)))
            return (rh.playerCrashed(config), "") # no replay information to get
        while True:  # wait for game to end while players/bots do their thing
            obs = getGameState()
            result = obs.player_result
            if result: # match end condition was supplied by the host
                finalResult = rh.idPlayerResults(config, result)
                break
            try:    agentCallBack(obs) # do developer's creative stuff
            except Exception as e:
                print("ERROR: agent %s crashed during game: %s (%s)"%(thisPlayer.initCmd, e, type(e)))
                finalResult = rh.playerCrashed(config)
                break
        #if config.saveReplayAfterGame:
        #    replayData = controller.save_replay()
        #    replay.save(replayData)
        #    # TODO -- copy/ftp generated replay file to replay processing folder
        #controller.leave() # the connection to the server process is (cleanly) severed
      except (protocol.ConnectionError, protocol.ProtocolError, remote_controller.RequestError) as e:
        if debug:   print("%s Connection to game closed (NOT a bug)%s%s"%(type(e), os.linesep, e))
        else:       print(   "Connection to game host was lost.")
        finalResult = rh.playerDisconnected(config)
      except KeyboardInterrupt:
        if debug: print("caught command to forcibly shutdown Starcraft2 host process.")
        finalResult = rh.playerSurrendered(config)
      finally:
        #config.disable() # if the saved cfg file still exists, always remove it
        if replayData == None: # only get replayData if not already preset
            replayData = base64.encodestring(controller.save_replay()).decode() # convert raw bytes into str
        controller.quit() # force the sc2 application to close
        #if debug:
        print("host process has ended")
    if not finalResult:
        finalResult = rh.playerSurrendered(config)
    #if debug: print("finalResult:\n", finalResult)
    return (finalResult, replayData)

