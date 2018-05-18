
from __future__ import absolute_import

import os

from s2clientprotocol import common_pb2 as races
from s2clientprotocol import sc2api_pb2 as sc_pb


################################################################################
class InsufficientPlayers(  Exception): pass
class InvalidDifficulty(    Exception): pass
class InvalidMapSelection(  Exception): pass
class InvalidPlayerType(    Exception): pass
class InvalidRace(          Exception): pass
class ConfigAlreadyActive(  Exception): pass
class TimeoutExceeded(      Exception): pass


################################################################################
# Bot Difficulties
VERYEASY    = "veryeasy"
EASY        = "easy"
MEDIUM      = "medium"
MEDIUMHARD  = "mediumhard"
HARD        = "hard"
HARDER      = "harder"
VERYHARD    = "veryhard"
CHEATVISION = "cheatvision"
CHEATMONEY  = "cheatmoney"
CHEATINSANE = "cheatinsane"
################################################################################
# Player Types
COMPUTER    = "bot"
OBSERVER    = "observer"
PARTICIPANT = "agent"
################################################################################
# Races
PROTOSS     = "protoss"
ZERG        = "zerg"
TERRAN      = "terran"
NEUTRAL     = "neutral" # NPC only, non-controllable by any (e.g. map features)
RANDOM      = "random"  # only valid as a selection race, not an actual race


################################################################################
allowedTypes = { # the types of players that can watch/affect the game
    COMPUTER            : sc_pb.Computer    ,
    OBSERVER            : sc_pb.Observer    ,
    PARTICIPANT         : sc_pb.Participant ,
}
allowedRaces = { # associate print-friendly names with sc2 API enum values
    PROTOSS             : races.Protoss     ,
    ZERG                : races.Zerg        ,
    TERRAN              : races.Terran      ,
    RANDOM              : races.Random      ,
}
allowedDifficulties = { # associate print-friendly names with sc2 API enum values
    VERYEASY            : sc_pb.VeryEasy    ,
    EASY                : sc_pb.Easy        ,
    MEDIUM              : sc_pb.Medium      ,
    MEDIUMHARD          : sc_pb.MediumHard  ,
    HARD                : sc_pb.Hard        ,
    HARDER              : sc_pb.Harder      ,
    VERYHARD            : sc_pb.VeryHard    ,
    CHEATVISION         : sc_pb.CheatVision ,
    CHEATMONEY          : sc_pb.CheatMoney  ,
    CHEATINSANE         : sc_pb.CheatInsane ,
}
################################################################################
def _matchValue(value, d):
    """convert the Starcraft2 protocol value into an internally known value"""
    for k,v in d.iteritems():
        if v==value: return k # raise if provided value isn't found
    if   d==allowedTypes:           e = InvalidPlayerType
    elif d==allowedRaces:           e = InvalidRace
    elif d==allowedDifficulties:    e = InvalidDifficulty
    else:                           e = ValueError
    raise e("invalid value provided: %s"%value)
def convertValueToType(val):        return _matchValue(val, allowedTypes)
def convertValueToRace(val):        return _matchValue(val, allowedRaces)
def convertValueToDifficulty(val):  return _matchValue(val, allowedDifficulties)


################################################################################
# Match Modes
mode1v1     = "1v1"
mode1v1bot  = "1v1bot"
mode1vNbot  = "1vNbot"
mode2v2     = "2v2"
mode3v3     = "3v3"
mode4v4     = "4v4"
modeNvN     = "NvN"
modeNvNbot  = "NvNbot"
modeFFA     = "FFA"
modeFFAbot  = "FFAbot"
modeUnknown = "unknown"
agentModes={# allowed num players   teams   FFA
    mode1v1     : ([ 2 ]        ,   False,  False),
    mode2v2     : ([ 4 ]        ,   True ,  False),
    mode3v3     : ([ 6 ]        ,   True ,  False),
    mode4v4     : ([ 8 ]        ,   True ,  False),
    modeNvN     : (range(3,9)   ,   True ,  False),
    modeFFA     : (range(2,9)   ,   False,  True ),
}
botModes = {# allowed num players   teams   FFA
    mode1v1bot  : ([ 2 ]        ,   False,  False),
    mode1vNbot  : (range(3,9)   ,   False,  False),
    modeNvNbot  : (range(3,9)   ,   True ,  False),
    modeFFAbot  : (range(2,9)   ,   False,  True ),
}
allModes = {}
allModes.update(agentModes)
allModes.update(botModes)


################################################################################
# game expansions
WINGS_OF_LIBERTY        = "Wings_Of_Liberty"
HEART_OF_THE_SWARM      = "Heart_Of_The_Swarm"
LEGACY_OF_THE_VOID      = "Legacy_Of_The_Void"
DEFAULT_EXPANSION       = LEGACY_OF_THE_VOID


################################################################################
# file/folder information
SC2_FILE_REPLAY         = "SC2Replay"
SC2_FILE_MAP            = "SC2Map"
FOLDER_PLAYED_VIDEO     = "playedReplays"
FOLDER_JSON             = "jsonData"
FOLDER_ACTIVE_CONFIGS   = os.sep.join(os.path.abspath(__file__).split(os.sep)[:-1] + ["activeGames"])
JSON_HEADERS            = ["label", "base-version", "version", "data-hash", "fixed-hash", "replay-hash"]
FILE_GAME_VERSIONS      = "versions.json"
MIN_VERSION_AI_API      = 55958 # 3.16.1 is the first version that released the API
FOLDER_IGNORED_MAPS     = ["Melee", "mini_games", "Test"]


################################################################################
# misc
MIN_REQUIRED_PLAYERS    = 2
DEFAULT_TIMEOUT         = 120 # seconds

