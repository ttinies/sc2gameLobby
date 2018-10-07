"""
Copyright (c) 2018 Versentiedge LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS-IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import absolute_import
from __future__ import division  # python 2/3 compatibility
from __future__ import print_function  # python 2/3 compatibility

import os

from sc2gameLobby import gameConfig
from sc2gameLobby import gameConstants
from sc2gameLobby import genericObservation as go
from sc2gameLobby import hostGame
from sc2gameLobby import joinGame
from sc2gameLobby import versions
from sc2gameLobby.__version__ import *

config = gameConfig.Config  # set up the player/match environment as desired
host = hostGame.run  # host a new Starcraft2 match, given a configuration
join = joinGame.playerJoin  # join an existing Starcraft2 match, given a configuration
clear = gameConfig.clearConfigs  # manually reset/clear any existing (defunct) game configurations
active = gameConfig.activeConfigs  # display the games currently being set up


def updateVersion(**kwargs):
    """add/update record data using kwargs params for new keys/values"""
    versions.handle.save(kwargs)
