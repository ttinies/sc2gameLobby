
from __future__ import absolute_import
from __future__ import division       # python 2/3 compatibility
from __future__ import print_function # python 2/3 compatibility

import os

from s2clientprotocol import sc2api_pb2 as sc_pb
from pysc2.lib import protocol
from pysc2.lib import remote_controller
from sc2gameLobby import gameConfig
from sc2gameLobby import gameConstants as c
from sc2gameLobby import genericObservation as go


################################################################################
def playerJoin(hostCfg, config, agentCallBack=go.doNothing, debug=False):
    """cause an agent to join an already hosted game"""
    interface = sc_pb.InterfaceOptions()
    raw,score,feature,rendered = config.interfaces
    interface.raw   = raw   # whether raw data is reported in observations
    interface.score = score # whether score data is reported in observations
    interface.feature_layer.width = 24
    #interface.feature_layer.resolution = 
    #interface.feature_layer.minimap_resolution =
    hostIPs, ports = hostCfg.connection
    gameP, baseP, sharedP = ports
    joinReq = sc_pb.RequestJoinGame(options=interface) # SC2APIProtocol.RequestJoinGame
    #joinReq.observed_player_id
    joinReq.server_ports.game_port  = gameP
    joinReq.server_ports.base_port  = baseP
    joinReq.shared_port             = sharedP
    for myGP, myBP in hostCfg.slaveConnections:
        joinReq.client_ports.add(game_port=myGP, base_port=myBP)
    if config.numAgents:
        playerType   = c.PARTICIPANT
        joinReq.race = c.allowedRaces[config.race] # update joinGame request as necessary
    else: # observers don't have a selected race?
        playerType   = c.OBSERVER
        raise NotImplementedError("observer configurations aren't yet proven: %s"%(config))
    selectedIP = hostIPs[-1] # by default, assume game is local
    for mine,game in zip(config.connection[0], hostIPs): # compare my IP vs hostCfg's IP
        if game and mine==game: continue
        selectedIP = mine
        break
    print("joining Starcraft2 game @ %s game-port:%s base-port:%s shared-port:%s"%(selectedIP, gameP, baseP, sharedP))
    controller = None
    with config.launchApp(fullScreen=False, ip_address=selectedIP) as controller:
      try:
        getGameState = controller.observe # function that observes what's changed since the prior gameloop(s)
        if debug: print("Starcraft2 application is live. (%s)"%(controller.status)) # status: launched
        joinResp = controller.join_game(joinReq)
        config.updateID(joinResp.player_id)
        config.save() # "publish" the configuration file for other procs
        agentCallBack(config.name) # send the configuration to the controlling agent
        print("Join game @ %s was successful. Game is started! (%s)"%(selectedIP, controller.status)) # status: in_game
        result   = None
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
        print("%s Connection to game closed%s%s"%(type(e), os.linesep, e))
      except KeyboardInterrupt:
        print("caught command to forcibly shutdown Starcraft2 host server.")
      finally:
        #config.disable() # if the saved cfg file still exists, always remove it
        if controller: controller.quit() # force the sc2 application to close


################################################################################
if __name__=="__main__":
    selectedRace = c.ZERG
    myCfg = gameConfig.Config(raw=True, score=True, debug=True,
        agentRaces=[selectedRace])
    myCfg.save() # inform the host what this client's configuration is
    hostCfg = gameConfig.loadHostConfig()#debug=True,
    myCfg.updateRaw( # mimic host's determined game settings
        fogDisabled = hostCfg._fogDisabled_, # expect the same gameplay as host
        mapName     = hostCfg._mapName_,     # expect to play on the same map
        realtime    = hostCfg._realtime_,    # expect to play at the host's defined rate
        vers        = hostCfg._version_,     # expect to play the same game version as host
    )
    myCfg.save() # save the game params received from host
    # TODO -- or get config from remote machine
    playerJoin(hostCfg, myCfg, debug=False)

