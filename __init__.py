"""
Copyright 2018 Versentiedge LLC All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS-IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import absolute_import
from __future__ import division       # python 2/3 compatibility
from __future__ import print_function # python 2/3 compatibility

import os

from sc2gamemgr import gameConfig
from sc2gamemgr import gameConstants
from sc2gamemgr import getGameData
from sc2gamemgr import genericObservation as go
from sc2gamemgr import hostGame
from sc2gamemgr import joinGame
from sc2gamemgr import replay
from sc2gamemgr import versions


################################################################################
config  = gameConfig.Config         # set up the player/match environment as desired
host    = hostGame.run              # host a new Starcraft2 match, given a configuration
join    = joinGame.playerJoin       # join an existing Starcraft2 match, given a configuration
clear   = gameConfig.clearConfigs   # manually reset/clear any existing (defunct) game configurations
active  = gameConfig.activeConfigs  # display the games currently being set up


################################################################################
def updateVersion(**kwargs):
    """add/update record data using kwargs params for new keys/values"""
    versions.handle.save(kwargs)

