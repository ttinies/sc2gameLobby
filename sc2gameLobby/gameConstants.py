
from __future__ import absolute_import
from __future__ import division       # python 2/3 compatibility
from __future__ import print_function # python 2/3 compatibility

import os

from sc2common.constants import *
from sc2common import types

################################################################################
class TimeoutExceeded(Exception): pass
class UnknownPlayer(Exception): pass

################################################################################
# file/folder information
SC2_FILE_REPLAY         = "SC2Replay"
SC2_FILE_MAP            = "SC2Map"
FOLDER_LOBBY_HERE       = os.path.dirname(os.path.abspath(__file__))
FOLDER_PLAYED_VIDEO     = "playedReplays"
FOLDER_JSON             = "jsonData"
FOLDER_ACTIVE_CONFIGS   = os.path.join(FOLDER_LOBBY_HERE, "activeGames")
FOLDER_MODS             = os.path.join(FOLDER_LOBBY_HERE, "mods")
JSON_HEADERS            = ["label", "base-version", "version", "data-hash", "fixed-hash", "replay-hash"]
FILE_GAME_VERSIONS      = "versions.json"
FILE_EDITOR_MOD         = os.path.join(FOLDER_MODS, "Playground.SC2Mod")
MIN_VERSION_AI_API      = 55958 # 3.16.1 is the first version that released the API
FOLDER_IGNORED_MAPS     = ["Melee", "mini_games", "Test"]
FOLDER_APP_SUPPORT      = "Support%s"         # reserved space to specify 32-bit or 64-bit items
FILE_EDITOR_APP         = "SC2Switcher%s.exe" # reserved space to specify 32-bit or 64-bit items
SUPPORT_32_BIT_TERMS    = ["", ""]
SUPPORT_64_BIT_TERMS    = ["64", "_x64"]

################################################################################
# misc
MIN_REQUIRED_PLAYERS    = 2   # players
INITIAL_TIMEOUT         = 120 # seconds
DEFAULT_TIMEOUT         = 15  # seconds
DEFAULT_HOST_DELAY      = 4   # seconds
REPLAY_SAVE_FREQUENCY   = 10  # seconds
URL_BASE                = "http://%s:%s/%s/"

