
from __future__ import absolute_import
from __future__ import division       # python 2/3 compatibility
from __future__ import print_function # python 2/3 compatibility

from past.builtins import xrange # python 2/3 compatibility

from s2clientprotocol import sc2api_pb2 as sc_pb

from pysc2.lib import protocol
from pysc2.lib import remote_controller
from pysc2.lib.sc_process import FLAGS
from sc2gameLobby import gameConfig
from sc2gameLobby import gameConstants as c
from sc2gameLobby import genericObservation as go
from sc2gameLobby import replay

import os
import sys
import time

now = time.time


################################################################################
def run(config, agentCallBack=go.doNothing, lobbyTimeout=c.DEFAULT_TIMEOUT, debug=False):
    """PURPOSE: start a starcraft2 process using the defined the config parameters"""
    FLAGS(sys.argv)
    createReq = sc_pb.RequestCreateGame( # used to advance to "Init Game" state, when hosting
        realtime    = config.realtime,
        disable_fog = config.fogDisabled,
        random_seed = int(now()), # a game is created using the current second timestamp as the seed
        local_map   = sc_pb.LocalMap(map_path=config.mapLocalPath,
                                     map_data=config.mapData) )
    agentRaces, bots, numObservers = config.allLobbySlots # add players to create game request in the protocol's required format
    for race in agentRaces:
        reqPlayer = createReq.player_setup.add() # add new player; get link to settings
        reqPlayer.type       = c.allowedTypes[c.PARTICIPANT]
        reqPlayer.race       = c.allowedRaces[race]
    for race,difficulty in bots:
        reqPlayer = createReq.player_setup.add() # add new player; get link to settings
        reqPlayer.type       = c.allowedTypes[c.COMPUTER]
        reqPlayer.race       = c.allowedRaces[race]
        reqPlayer.difficulty = c.allowedDifficulties[difficulty]
    for i in xrange(numObservers): # an extra slot is reserved for the host
        reqPlayer = createReq.player_setup.add() # add new player; get link to settings
        reqPlayer.type       = c.allowedTypes[c.OBSERVER]
    interface = sc_pb.InterfaceOptions()
    raw,score,feature,rendered = config.interfaces
    interface.raw   = raw   # whether raw data is reported in observations
    interface.score = score # whether score data is reported in observations
    interface.feature_layer.width = 24
    #interface.feature_layer.resolution = 
    #interface.feature_layer.minimap_resolution =
    joinReq = sc_pb.RequestJoinGame(options=interface) # SC2APIProtocol.RequestJoinGame
    joinReq.race = c.allowedRaces[config.race] # update joinGame request as necessary
    # TODO -- allow host player to be an observer, not just a player w/ race
    #joinReq.observed_player_id
    gameP, baseP, sharedP = config.ports
    if config.isMultiplayer:
        joinReq.server_ports.game_port  = gameP
        joinReq.server_ports.base_port  = baseP
        joinReq.shared_port             = sharedP
    for slaveGP, slaveBP in config.slaveConnections:
        joinReq.client_ports.add(game_port=slaveGP, base_port=slaveBP)
    if debug: print("Starcraft2 game process is launching.")
    controller = None
    with config.launchApp(fullScreen=True) as controller:
      try:
        getGameState = controller.observe # function that observes what's changed since the prior gameloop(s)
        if debug: print("Starcraft2 application is live. (%s)"%(controller.status)) # status: launched
        controller.create_game(createReq)
        if debug: print("Starcraft2 is waiting for %d player(s) to join. (%s)"%(config.numAgents, controller.status)) # status: init_game
        playerID = controller.join_game(joinReq).player_id # SC2APIProtocol.RequestJoinGame
        config.updateID(playerID)
        config.save() # "publish" the configuration file for other procs
        print("[HOSTGAME] %d %s"%(playerID, config))
        agentCallBack(config.name) # send the configuration to the controlling agent's pipeline
        startWaitTime = now()
        knownPlayers  = []
        numExpectedPlayers = config.numGameClients # + len(bots) : bots don't need to join; they're run by the host process automatically
        while len(knownPlayers) < numExpectedPlayers:
            elapsed = now() - startWaitTime
            if elapsed > lobbyTimeout: # wait for additional players to join
                raise c.TimeoutExceeded("timed out after waiting for players to join for waiting %.1f > %s seconds!"%(elapsed, lobbyTimeout))
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
                playerID = pInfo.player_id
                if playerID in knownPlayers: continue # player joined previously
                knownPlayers.append(playerID)
                if debug:
                    typ  = c.convertValueToType(pInfo.type)
                    rReq = c.convertValueToRace(pInfo.race_requested)
                    if   typ==c.PARTICIPANT:    print("player #%d joined: agent(%s)"%(playerID, rReq))
                    elif typ==c.COMPUTER:       print("player #%d joined: bot(%s, %s)"%(playerID, rReq, c.convertValueToDifficulty(pInfo.difficulty)))
                    elif typ==c.OBSERVER:       print("player #%d joined: observer"%(playerID))
                    else:                       print("player #%d joined: unknown type.%s%s"%(playerID, os.linesep, str(pInfo).rstrip()))
        if debug: print("all %d players found; game is started! (%s)"%(numExpectedPlayers, controller.status)) # status: init_game
        result = None
        while True:  # wait for game to end while players/bots do their thing
            obs = getGameState()
            result = obs.player_result
            if result: break
            agentCallBack(obs) # do developer's creative stuff
        if debug: print("Result:\n", result)
        if config.saveReplayAfterGame:
            replayData = controller.save_replay()
            replay.save(replayData)
            # TODO -- copy/ftp generated replay file to replay processing folder
        #controller.leave() # the connection to the server process is (cleanly) severed
      except (protocol.ConnectionError, protocol.ProtocolError, remote_controller.RequestError) as e:
        if debug:   print("%s Connection to game closed (NOT a bug)%s%s"%(type(e), os.linesep, e))
        else:       print(   "Connection to game closed.")
      except KeyboardInterrupt:
        print("caught command to forcibly shutdown Starcraft2 host server.")
      finally:
        #config.disable() # if the saved cfg file still exists, always remove it
        controller.quit() # force the sc2 application to close
        #if debug:
        print("host process has ended")


################################################################################
if __name__=="__main__":
    numOtherPlayers = 1                         # vs other agent
    allBots         = []                        # vs other agent
    #numOtherPlayers = 0                         # vs bot only
    #allBots         = [(c.TERRAN, c.HARDER)]    # vs bot only
    selectedRace    = c.RANDOM
    allConnects     = []
    allRaces        = [selectedRace]
    for slave in gameConfig.getSlaveConfigs(numConfigs=numOtherPlayers):
        allConnects.append(slave.ports)
        allRaces.append(   slave.race)
    config = gameConfig.Config(raw=True, score=True, host=True, debug=False,
        agentRaces=allRaces, bots=allBots, connects=allConnects,
    )
    config.save()
    run(config, agentCallBack=go.doNothing, debug=True)

