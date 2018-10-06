#
# Copyright 2018 Versentiedge Inc. All Rights Reserved.
#   *** partially modified version previously published by Google Inc. ***
#   - revised logic when selecting the executable version
#   - now relies on external game version management module
#   - added mapsDir to ensure game knows where to find maps
#   - remove start() from LocalBase to allow a pure passthrough to lib.RunConfig
#   - added versionsDir to consolidate version dir lookups
#   - added validVersionExecutables to get all game versions available on this machine
#
# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Configs for how to run SC2 from a normal install on various platforms."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from six import iteritems # python 2/3 compatibility

import copy
import os
import platform
import sys

from sc2gameLobby import versions
from pysc2.run_configs import lib
from pysc2.lib import sc_process


################################################################################
class LocalBase(lib.RunConfig):
  """Base run config for the deepmind file hierarchy."""
  ##############################################################################
  def __init__(self, base_dir, exec_name, cwd=None, env=None):
    base_dir = os.path.expanduser(base_dir)
    cwd = cwd and os.path.join(base_dir, cwd)
    super(LocalBase, self).__init__(
        replay_dir=os.path.join(base_dir, "Replays"),
        data_dir=base_dir, tmp_dir=None, cwd=cwd, env=env)
    self._exec_name = exec_name
    self.xyz = None
  ##############################################################################
  @property
  def is64bit(self):
      """whether the this machine is 64-bit capable or not"""
      return platform.machine().endswith('64')
  ##############################################################################
  @property
  def mapsDir(self):
      return os.path.join(self.data_dir, "Maps")
  ##############################################################################
  @property
  def mostRecentVersion(self):
      versMap = self.versionMap()
      orderedVersions = sorted(list(iteritems(versMap)))
      compatibleVersions = versions.handle.search(orderedVersions[-1][0])
      compatibleVersions = [(v['version'], v) for v in compatibleVersions]
      bestVersionLabel = max(compatibleVersions)[1]['label']
      return bestVersionLabel
  ##############################################################################
  @property
  def validVersionExecutables(self):
      ret = []
      for x in os.listdir(self.versionsDir):
          if x.startswith("Base"):
              ret.append(int(x[4:]))
      return ret
  ##############################################################################
  @property
  def versionsDir(self):
      return os.path.join(self.data_dir, "Versions")
  ##############################################################################
  def exec_path(self, baseVersion=None):
    """Get the exec_path for this platform. Possibly find the latest build."""
    if not os.path.isdir(self.data_dir):
        raise sc_process.SC2LaunchError("Install Starcraft II at %s or set the SC2PATH environment variable"%(self.data_dir))
    if baseVersion==None: # then select most recent version's baseVersion
        mostRecent = versions.handle.mostRecent
        if mostRecent:  return mostRecent["base-version"]
        raise sc_process.SC2LaunchError(
            "When requesting a versioned executable path without specifying base-version, expected "
            "to find StarCraft II versions installed at %s."%(self.versionsDir))
    elif isinstance(baseVersion, versions.Version):
        baseVersion = baseVersion.baseVersion
    elif str(baseVersion).count(".") > 0:
        baseVersion = versions.Version(baseVersion).baseVersion
    #else: # otherwise expect that the baseVersion specified is correct
    baseVersExec = os.path.join(self.versionsDir, "Base%s"%baseVersion, self._exec_name)
    if os.path.isfile(baseVersExec):
        return baseVersExec # if baseVersion in Versions subdir is valid, it is the correct executable
    raise sc_process.SC2LaunchError("Specified baseVersion %s does not exist at %s.%s    available: %s"%(\
        baseVersion, baseVersExec, os.linesep, " ".join(
            str(val) for val in sorted(self.versionMap().keys())) ))
  ##############################################################################
  def listVersions(self):
      ret = []
      map(ret.extend, self.versionMap().values())
      return sorted(ret)
  ##############################################################################
  def versionMap(self, debug=False):
      ret = {}
      for vKey in self.validVersionExecutables:
          labels = [r["label"] for r in versions.handle.search(**{"version":vKey})]
          ret[vKey] = labels
      return ret
      #return [versions.Version(vKey).label for vKey in self.validVersionExecutables]
  ##############################################################################
  def start(self, version=None, **kwargs):#game_version=None, data_version=None, **kwargs):
    """Launch the game process."""
    if not version:
        version = self.mostRecentVersion
    pysc2Version = lib.Version( # convert to pysc2 Version
        version.version,
        version.baseVersion,
        version.dataHash,
        version.fixedHash)
    return sc_process.StarcraftProcess(
                self,
                exec_path=self.exec_path(version.baseVersion),
                version=pysc2Version,
                **kwargs)


################################################################################
class Windows(LocalBase):
  """Run on Windows."""
  ##############################################################################
  def __init__(self):
    super(Windows, self).__init__(
        os.environ.get("SC2PATH", "C:/Program Files (x86)/StarCraft II").strip(
        '"'), "SC2_x64.exe", "Support64")
  ##############################################################################
  @classmethod
  def priority(cls):
    if platform.system() == "Windows":
      return 1


################################################################################
class MacOS(LocalBase):
  """Run on MacOS."""
  ##############################################################################
  def __init__(self):
    super(MacOS, self).__init__(
        os.environ.get("SC2PATH", "/Applications/StarCraft II"),
        "SC2.app/Contents/MacOS/SC2")
  ##############################################################################
  @classmethod
  def priority(cls):
    if platform.system() == "Darwin":
      return 1


################################################################################
class Linux(LocalBase):
  """Config to run on Linux."""
  ##############################################################################
  def __init__(self):
    base_dir = os.environ.get("SC2PATH", "~/StarCraftII")
    base_dir = os.path.expanduser(base_dir)
    env = copy.deepcopy(os.environ)
    env["LD_LIBRARY_PATH"] = ":".join(filter(None, [
        os.environ.get("LD_LIBRARY_PATH"),
        os.path.join(base_dir, "Libs/")]))
    super(Linux, self).__init__(base_dir, "SC2_x64", env=env)
  ##############################################################################
  @classmethod
  def priority(cls):
    if platform.system() == "Linux":
      return 1

