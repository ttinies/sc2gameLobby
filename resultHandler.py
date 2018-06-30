
from sc2gameLobby import gameConstants as c


################################################################################
def tieDetermined(cfg):
    """all players tied their results"""
    return assignValue(cfg, c.RESULT_TIE, c.RESULT_TIE)


################################################################################
def launchFailure(cfg):
    """report that the match failed to start as anticipated"""
    return assignValue(cfg, c.RESULT_UNDECIDED, c.RESULT_UNDECIDED)


################################################################################
def playerSurrendered(cfg):
    """the player has forceibly left the game"""
    if cfg.numAgents + cfg.numBots == 2:
          otherResult = c.RESULT_VICTORY
    else: otherResult = c.RESULT_UNDECIDED # if multiple players remain, they need to finish the match
    return assignValue(cfg, c.RESULT_DEFEAT, otherResult)


################################################################################
def playerCrashed(cfg):
    """occurs when a player's understood state hasn't changed for too long"""
    return assignValue(cfg, c.RESULT_CRASH, c.RESULT_UNDECIDED)


################################################################################
def playerDisconnected(cfg):
    """occurs when a game client loses its connection from the host"""
    return assignValue(cfg, c.RESULT_DISCONNECT, c.RESULT_UNDECIDED)


################################################################################
def assignValue(cfg, playerValue, otherValue):
    """artificially determine match results given match circumstances.
    WARNING: cheating will be detected and your player will be banned from server"""
    player = cfg.whoAmI()
    result = {}
    for p in cfg.players:
        if p.name == player.name:   val = playerValue
        else:                       val = otherValue
        result[p.name] = val
    return result 


################################################################################
def idPlayerResults(cfg, rawResult):
    """interpret standard rawResult for all players with known IDs"""
    result = {}
    knownPlayers = []
    dictResult = {plyrRes.player_id : plyrRes.result for plyrRes in rawResult}
    for p in cfg.players:
        if p.playerID and p.playerID in dictResult: # identified player w/ result
            knownPlayers.append(p)
            result[p.name] = dictResult[p.playerID]
    #if len(knownPlayers) == len(dictResult) - 1: # identified all but one player
    #    for p in cfg.players: # search for the not identified player
    #        if p in knownPlayers: continue # already found
    #        result.append( [p.name, p.playerID, dictResult[p.playerID]] )
    #        break # found missing player; stop searching
    #for r in result:
    #    print("result:>", r)
    return result

