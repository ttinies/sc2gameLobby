
from __future__ import absolute_import
from __future__ import division       # python 2/3 compatibility
from __future__ import print_function # python 2/3 compatibility

import os

from sc2common.constants import *

################################################################################
class TimeoutExceeded(Exception): pass

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
MIN_REQUIRED_PLAYERS    = 2   # players
DEFAULT_TIMEOUT         = 120 # seconds
URL_BASE                = "http://%s:%s/%s/"

