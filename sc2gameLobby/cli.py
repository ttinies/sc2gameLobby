
from argparse import ArgumentParser

import sys

from sc2common import types as t
from sc2ladderMgmt import getKnownLadders
from sc2maptool.functions import filterMapNames
from sc2players import getKnownPlayers
from sc2gameLobby.__version__ import __version__
from sc2gameLobby import gameConstants as c
from sc2gameLobby import launcher


################################################################################
def main():
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
    startOption.add_argument("-l", "--ladder"   , default="versentiedge", choices=ALLOWED_LADDERS
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
    launcher.run(options)

