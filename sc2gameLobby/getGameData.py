

################################################################################
#def get_data(**kwargs):
#    """custom algorithm to create a temporary game to retrieve true game data
#    NOTE: very similar to pysc2.bin.gen_actions.get_data()
#    """
#    run_config = run_configs.get()
#    with run_config.start(**kwargs) as controller:
#        m = maps.get("Sequencer")  # Arbitrary ladder map.
#        create = sc_pb.RequestCreateGame(local_map=sc_pb.LocalMap(
#            map_path=m.path, map_data=m.data(run_config)))
#        create.player_setup.add(type=sc_pb.Participant)
#        create.player_setup.add(type=sc_pb.Computer, race=sc_common.Random,
#                                difficulty=sc_pb.VeryEasy)
#        join = sc_pb.RequestJoinGame(race=sc_common.Random,
#                                     options=sc_pb.InterfaceOptions(raw=True))
#        controller.create_game(create)
#        controller.join_game(join)
#        return controller.data()


from __future__ import absolute_import
from __future__ import division       # python 2/3 compatibility
from __future__ import print_function # python 2/3 compatibility

from s2clientprotocol import sc2api_pb2 as sc_pb

from pysc2.lib import protocol
from pysc2.lib import remote_controller
from pysc2.lib.sc_process import FLAGS
from sc2common import types as t
from sc2gameLobby import gameConfig
from sc2gameLobby import gameConstants as c
from sc2players import PlayerPreGame
#from sc2gamemgr import genericObservation as go

import os
import sys
import time

now = time.time


################################################################################
def run(debug=False):
    """PURPOSE: start a starcraft2 process using the defined the config parameters"""
    FLAGS(sys.argv)
    config = gameConfig.Config(
        version=None, # vers is None... unless a specific game version is desired
        themap="Sequencer",  # smaller maps load faster?
        players=["defaulthuman", "blizzbot2_easy"],
    )
    createReq = sc_pb.RequestCreateGame( # used to advance to "Init Game" state, when hosting
        realtime    = config.realtime,
        disable_fog = config.fogDisabled,
        random_seed = int(now()), # a game is created using the current second timestamp as the seed
        local_map   = sc_pb.LocalMap(map_path=config.mapLocalPath,
                                     map_data=config.mapData) )
    joinRace = None
    for player in config.players:
        reqPlayer = createReq.player_setup.add() # add new player; get link to settings
        playerObj = PlayerPreGame(player)
        if playerObj.isComputer:
              reqPlayer.difficulty  = playerObj.difficulty.gameValue()
              pType                 = playerObj.type.type
        else: pType                 = c.PARTICIPANT
        reqPlayer.type              = t.PlayerControls(pType).gameValue()
        reqPlayer.race              = playerObj.selectedRace.gameValue()
        if not playerObj.isComputer:
            joinRace                = reqPlayer.race
    interface = sc_pb.InterfaceOptions()
    raw,score,feature,rendered = config.interfaces
    interface.raw   = raw   # whether raw data is reported in observations
    interface.score = score # whether score data is reported in observations
    interface.feature_layer.width = 24
    joinReq = sc_pb.RequestJoinGame(options=interface) # SC2APIProtocol.RequestJoinGame
    joinReq.race = joinRace # update joinGame request as necessary
    if debug: print("Starcraft2 game process is launching.")
    controller = None
    with config.launchApp() as controller:
      try:
        if debug: print("Starcraft2 application is live. (%s)"%(controller.status)) # status: launched
        controller.create_game(createReq)
        if debug: print("Starcraft2 is waiting for %d player(s) to join. (%s)"%(config.numAgents, controller.status)) # status: init_game
        playerID = controller.join_game(joinReq).player_id # SC2APIProtocol.RequestJoinGame
        print("[HOSTGAME] %d %s"%(playerID, config))
        return controller.ping(), controller.data()

      except (protocol.ConnectionError, protocol.ProtocolError, remote_controller.RequestError) as e:
        if debug:   print("%s Connection to game closed (NOT a bug)%s%s"%(type(e), os.linesep, e))
        else:       print(   "Connection to game closed.")
      except KeyboardInterrupt:
        print("caught command to forcibly shutdown Starcraft2 host server.")
      finally:
        #config.disable() # if the saved cfg file still exists, always remove it
        controller.quit() # force the sc2 application to close
        print("host process has ended")

#run()

