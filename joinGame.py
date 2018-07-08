
from __future__ import absolute_import
from __future__ import division       # python 2/3 compatibility
from __future__ import print_function # python 2/3 compatibility

from pysc2.lib import protocol
from pysc2.lib import remote_controller
from pysc2.lib.sc_process import FLAGS

import base64
import os
import subprocess
import sys
import time

from sc2gameLobby.clientManagement import ClientController
from sc2gameLobby import gameConfig
from sc2gameLobby import gameConstants as c
from sc2gameLobby import resultHandler as rh

now = time.time


################################################################################
def playerJoin(config, agentCallBack, lobbyTimeout=c.INITIAL_TIMEOUT, debug=True):
    """cause an agent to join an already hosted game"""
    FLAGS(sys.argv) # ignore pysc2 command-line handling (eww)
    log = protocol.logging.logging
    log.disable(log.CRITICAL) # disable pysc2 logging
    amHosting   = not bool(config.host)
    thisPlayer  = config.whoAmI()
    operPrefix  = "HOST" if amHosting else "JOIN"
    operType    = "%sGAME"%operPrefix
    hostInfo    = config.host
    try:    ipAddresses, hostPorts = hostInfo
    except ValueError:
        raise ValueError("invalid host configuration; expected IP addresses "\
                         "and ports. Given: %s"%str(hostInfo))
    print(ipAddresses)
    print(hostPorts)
    joinReq     = config.requestJoinDetails()
    selectedIP  = ipAddresses[-1] # by default, assume game is local
    for game,mine in zip(ipAddresses, config.ipAddress): # compare my IP vs hostCfg's IP
        if game and game==mine: continue
        selectedIP = mine
        break
    print("selectedIP:", selectedIP)
    selectPort  = config.clientInitPort()
    controller  = None # the object that manages the application process
    finalResult = rh.playerSurrendered(config) # default to this player losing if somehow a result wasn't acquired normally
    replayData  = "" # complete raw replay data for the match
    if debug: print("[%s] Starcraft2 game process is launching (fullscreen=%s)."%(operType, config.fullscreen))
    with config.launchApp(fullScreen=config.fullscreen, ip_address=selectedIP, port=selectPort, connect=False):
      try: # WARNING: if port equals the same port of the host on the same machine, this subsequent process closes!
        controller = ClientController()
        controller.connect(url=selectedIP, port=selectPort, timeout=lobbyTimeout) # establish socket connection
        timeToWait = c.DEFAULT_HOST_DELAY
        for i in range(timeToWait): # WARNING: the host must perform its join action with its client before any joining players issue join requests to their clients
            if debug: print("[%s] waiting %d seconds for the host to finish its init sequence."%(operType, timeToWait-i))
            time.sleep(1)
        joinResp = controller.join_game(joinReq) # SC2APIProtocol.RequestJoinGame
        print("[%s] connection to %s:%d was successful. Game is starting! (%s)"%(operType, selectedIP, selectPort, controller.status)) # status: in_game
        thisPlayer.playerID = int(joinResp.player_id) # update playerID; repsponse to join game request is authority
        if debug: print("[%s] joined match as %s."%(operType, thisPlayer)) # all players have actually joined already to advance beyond join_game (init_game)
        config.updateIDs(controller.game_info(), tag=operType, debug=debug) # SC2APIProtocol.ResponseGameInfo object
        if debug: print("[%s] all %d player(s) found; game has started! (%s)"%(operType, config.numGameClients, controller.status)) # status: init_game
        config.save() # "publish" the configuration file for other procs
        try:    agentCallBack(config.name) # send the configuration to the controlling agent
        except Exception as e:
            print("ERROR: agent %s crashed during init: %s (%s)"%(thisPlayer.initCmd, e, type(e)))
            return (rh.playerCrashed(config), "") # no replay information to get
        getGameState = controller.observe # function that observes what's changed since the prior gameloop(s)
        startWaitTime = now()
        while True:  # wait for game to end while players/bots do their thing
            obs = getGameState()
            result = obs.player_result
            if result: # match end condition was supplied by the client
                finalResult = rh.idPlayerResults(config, result)
                break
            try: agentCallBack(obs) # do developer's creative stuff
            except Exception as e:
                print("%s ERROR: agent callback %s of %s crashed during game: %s"%(type(e), agentCallBack, thisPlayer.initCmd, e))
                finalResult = rh.playerCrashed(config)
                break
            newNow = now() # periodicially acquire the game's replay data (in case of abnormal termination)
            if newNow - startWaitTime > c.REPLAY_SAVE_FREQUENCY:
                replayData = controller.save_replay()
                startWaitTime = newNow
        replayData = controller.save_replay() # one final attempt to get the complete replay data
        #controller.leave() # the connection to the server process is (cleanly) severed
      except (protocol.ConnectionError, protocol.ProtocolError, remote_controller.RequestError) as e:
        if "Status.in_game" in str(e): # state was previously in game and then exited that state
            finalResult = rh.playerSurrendered(config) # rage quit is losing
        else:
            finalResult = rh.playerDisconnected(config)
            print("%s Connection to game host has ended, even intentionally by agent. Message:%s%s"%(type(e), os.linesep, e))
      except KeyboardInterrupt:
        if debug: print("caught command to forcibly shutdown Starcraft2 client.")
        finalResult = rh.playerSurrendered(config)
      finally:
        if replayData: # ensure replay data can be transmitted over http
            replayData = base64.encodestring(replayData).decode() # convert raw bytes into str
        if controller: controller.quit() # force the sc2 application to close
    return (finalResult, replayData)

