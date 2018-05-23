
from __future__ import absolute_import
from __future__ import division       # python 2/3 compatibility
from __future__ import print_function # python 2/3 compatibility

from six import iteritems # python 2/3 compatibility

import glob
import json
import os
import portpicker
import random
import re
import time

from sc2gameLobby import dateFormat
from sc2gameLobby import gameConstants as c
from sc2gameLobby import ipAddresses
#import mapData
from sc2gameLobby import runConfigs
from sc2gameLobby import versions


"""
establish a configuration file containing game information such that other
processes can identify what any other established configuration already is
without necessitating inter-process communication for this information.
"""


################################################################################
def activeConfigs():
    """identify all configurations which are currently active"""
    #return [os.path.abspath(item) for item in os.listdir(c.FOLDER_ACTIVE_CONFIGS)]
    return glob.glob( os.path.join(c.FOLDER_ACTIVE_CONFIGS, "*.json") )


################################################################################
def clearConfigs():
    """remove all active configurations, if any"""
    for cfg in activeConfigs(): os.remove(cfg)


################################################################################
def loadHostConfig(timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        for cfgName in activeConfigs():
            if re.search("^host", cfgName.split(os.sep)[-1]):
                cfg = Config()
                cfg.load(cfgName)
                return cfg
    raise c.TimeoutExceeded("could not identify the host config within %d seconds."%(timeout))


################################################################################
def getSlaveConfigs(numConfigs=1, timeout=15):
    ret = set()
    start = time.time()
    while len(ret) < numConfigs: # keep looking for slave configs until they're found or timeout
        if time.time() - start > timeout:
            raise c.TimeoutExceeded("could not identify any slave configs"\
                "within %d seconds"%(timeout))
        for cfgName in activeConfigs():
            if re.search("^host", cfgName): continue
            cfg = Config(host=True)
            cfg.load(cfgName)
            ret.add( cfg )
    return ret


################################################################################
class Config(object):
    """
    Raw data values are represented with _text_ syntax.  Such attributes are
    used in saved configurations to regenerate the rest of the configuration.
    Cached data values are represented with _text syntax.  Such attributes help
    save time for subsequent queries by caching the calculated data
    """
    ############################################################################
    regexRaw   = re.compile("^_.*?_$")          # identify a raw attr
    regexCache = re.compile("^_[^_].*?[^_]$")   # identify a cached attr
    ############################################################################
    def __init__(self, mapName=None, vers=None, fogDisabled=False, realtime=True,
            host=False, connects=[], raw=False, score=False, feature=False, render=False,
            agentRaces=[], bots=[], numObservers=0, replay=None, debug=False,
            expo=c.DEFAULT_EXPANSION, load=None,
    ):
        self.updateRaw( # apply all raw parameters, even if not suppplied for defaults
            mapName=mapName, version=vers, fogDisabled=fogDisabled, realtime=realtime,
            showRaw=raw, showScore=score, showFeature=feature, showRender=render,
            agentRaces=agentRaces, bots=bots, numObs=numObservers, replay=replay,
            expansion=expo)
        self.host               = host # whether this is a host configuration or not
        self.slaveConnections   = connects
        self.debug              = debug
        if load: # allow a new Config object instantiation with values from file
            self.load(load)
            return # data already initialized appropriately do not perfrom subsequent init 
        self._ipAddr_           = ipAddresses.getAll() # update with IP address
        self._ports_            = self.ports # (game_port, base_port)
        self.mapAbsPath # calculate based on params
        self.version    # calculate based on params
        if host: self.ports.append(portpicker.pick_unused_port()) # shared_port
        if debug:
            print("raw config data:")
            self.display()
    ############################################################################
    def __str__(self):  return self.__repr__()
    def __repr__(self):
        name = self.__class__.__name__
        ip = self.connection
        ipStr = " @ %s:%s"%(ip[:2]) if ip else ""
        return "<%s %s %s%s>"%(name, self.installedApp.name(), self.version, ipStr)
    ############################################################################
    def __del__(self):
        map(portpicker.return_port, self._ports_)
        try:    self.disable()
        except IOError: pass
    ############################################################################
    @property
    def allLobbySlots(self):
        """the current configuration of the lobby's players, defined before the match starts"""
        if self.debug:
            p      = ["Lobby Configuration detail:"] + \
                     ["    agent:     %s"%r for r in self._agentRaces_] + \
                     ["    bot:       %s, %s"%(r,d) for r,d in self._bots_]
            if self._numObs_: # must separate condition because numObs is a number, not an iterator
                p += ["    observers: %d"%self._numObs_]
            print(os.linesep.join(p))
        return (list(self._agentRaces_), list(self._bots_), self._numObs_)
    ############################################################################
    @property
    def allMaps(self):
        """identify all Starcraft2 maps contained within the standard location"""
        ########################################################################
        def findAllMaps(path):
            """build a generator that iterates through all maps"""
            for item in glob.glob(os.path.join(path, "*")):
                if os.path.isdir(item): # also consider map files within the dir
                    for subitem in findAllMaps(item):   yield subitem
                elif item.endswith(c.SC2_FILE_MAP):
                    yield item
        ########################################################################
        return findAllMaps(self.installedApp.mapsDir) # build a generator
    ############################################################################
    @property
    def allReplays(self):
        raise NotImplementedError
    #  def replay_paths(self, replay_dir):
    #    """A generator yielding the full path to the replays under `replay_dir`."""
    #    replay_dir = self.abs_replay_path(replay_dir)
    #    if replay_dir.lower().endswith(".sc2replay"):
    #      yield replay_dir
    #      return
    #    for f in gfile.ListDir(replay_dir):
    #      if f.lower().endswith(".sc2replay"):
    #        yield os.path.join(replay_dir, f)
    ############################################################################
    @property
    def connection(self):
        """identify the remote connection parameters"""
        try:    return self._connect
        except: pass # raises if not yet defined
        self._connect = (self.ipAddresses, self.ports)
        return self._connect
    ############################################################################
    @property
    def execPath(self):
        """the executable application's path"""
        vers = self.version.label if self._version_ else None # executables in Versions folder are stored by baseVersion (modified by game data patches)
        return self.installedApp.exec_path(vers)
    ############################################################################
    @property
    def fogDisabled(self):
        """whether the game's fog should be disabled"""
        return self._fogDisabled_
    ############################################################################
    @property
    def installedApp(self):
        """identify the propery application to launch, given the configuration"""
        try:    return self._installedApp
        except: # raises if not yet defined
            self._installedApp = runConfigs.get() # application/install/platform management
            return self._installedApp
    ############################################################################
    @property
    def interfaces(self):
        return (self._showRaw_      , self._showScore_,
                self._showFeature_  , self._showRender_)
    ############################################################################
    @property
    def ipAddresses(self):
        try:        return self._ipAddr_
        except:     pass
        self._ipAddr_ = ipAddresses.getAll() # update with IP address
        return
    ############################################################################
    @property
    def isMultiplayer(self):
        return self.numGameClients > 1
    ############################################################################
    @property
    def mapData(self):
        """the raw, binary contents of the Starcraft2 map file"""
        with open(self.mapAbsPath, "rb") as f:
            return f.read()
    ############################################################################
    @property
    def mapLocalPath(self):
        loc = self.mapAbsPath.lstrip(self.installedApp.mapsDir)
        loc = loc.lstrip(os.sep)
        return loc
    ############################################################################
    @property
    def mapAbsPath(self):
        try:    return self._mapAbsPath
        except: pass # if not already defined, that's okay; define it now
        ########################################################################
        def hasIgnoredPath(given):
            for igPath in c.FOLDER_IGNORED_MAPS:
                matchStr = "%s%s%s"%(os.sep, igPath, os.sep)
                if matchStr in given: return True
            return False
        ########################################################################
        mapPath = self._mapName_
        bestMap = None
        if mapPath == None: # pick a map at random
            if self.debug: print("selecting a map at random...")
            bestScr = 0
            for m in self.allMaps:
                score = random.random()
                if score > bestScr: # select highest score, just because
                    if hasIgnoredPath(m): continue
                    bestMap = m
                    bestScr = score
            self._mapName_ = re.sub("[TLE]{2}\..*?$", "", os.path.basename(bestMap))
        else: # pick the map that best matches specified mapPath
            bestScr = 99999 # a big enough number to not be a valid file system path
            regex = re.compile("%s.*?%s"%(mapPath, c.SC2_FILE_MAP), flags=re.IGNORECASE)
            for m in self.allMaps:
                filename = os.path.basename(m)
                if re.search(regex, filename): # map contains specified phrase
                    score = len(filename) # the map with the smallest filename means it has the largets matching character percentage
                    if score < bestScr:
                        bestMap = m
                        bestScr = score
            if bestMap==None: raise c.InvalidMapSelection("requested map '%s"\
                "', but could not locate it within %s or its subdirectories."\
                %(mapPath, self.installedApp.mapsDir))
        self._mapAbsPath = bestMap # remember this bestPath in case mapAbsPath() is invoked later
        if self.debug: print("selected map %s"%(self.mapLocalPath))
        return self._mapAbsPath
    ############################################################################
    #@property
    #def matchup(self):
    #    """order player types, races to typify the match that is played"""
    #    sorted(self._agentRaces_)
    ############################################################################
    @property
    def name(self):
        try:    return self.cfgFile
        except: pass # else extract name from loaded cfg name
        k = "host" if self.host else os.getpid()
        self.cfgFile = os.path.join(c.FOLDER_ACTIVE_CONFIGS, "%s_%s.json"%(k, dateFormat.now()))
        return self.cfgFile
    ############################################################################
    @property
    def numAgents(self):
        return len(self._agentRaces_)
    ############################################################################
    @property
    def numBots(self):
        return len(self._bots_)
    ############################################################################
    @property
    def numGameClients(self):
        """the number of game client connections in the match"""
        return self.numAgents + self._numObs_
    ############################################################################
    @property
    def numPlayers(self):
        return self.numAgents + self.numBots
    ############################################################################
    @property
    def os(self):
        """the operating system this match is loaded on"""
        return self.installedApp.name()
    ############################################################################
    @property
    def ports(self):
        try:    return self._ports_
        except: pass
        self._ports_ = [
            portpicker.pick_unused_port(), # game_port
            portpicker.pick_unused_port(), # base_port
        ]
        return self._ports_
    ############################################################################
    @property
    def race(self):
        """useful for getting a slave's selected race"""
        try:    return self._agentRaces_[0] # race was selected
        except: return c.RANDOM # by default, race is random
    ############################################################################
    @property
    def realtime(self):
        """whether the game progresses in realtime or requires each player to
        summit step requests to advance the game"""
        return self._realtime_
    ############################################################################
    @property
    def replayData(self):
        with open(self.replayAbsPath, "rb") as f:
            return f.read()
    #  def replay_data(self, replay_path):
    #    """Return the replay data given a path to the replay."""
    #    with gfile.Open(self.abs_replay_path(replay_path), "rb") as f:
    #      return f.read()
    ############################################################################
    @property
    def replayLocalPath(self):
        raise NotImplementedError
        #return self.replayAbsPath.lstrip(self.installedApp.replaysDir)
    ############################################################################
    @property
    def replayAbsPath(self):
        raise NotImplementedError
    #  def abs_replay_path(self, replay_path):
    #    """Return the absolute path to the replay, outside the sandbox."""
    #    return os.path.join(self.replay_dir, replay_path)
    ############################################################################
    @property
    def saveReplayAfterGame(self):
        try:    return self._replay_ == True
        except: return False
    ############################################################################
    @property
    def version(self):
        """the executable application's version"""
        try:    return self._version
        except: pass # raises if not yet defined
        if self._version_: # verify specified version exists
            version = versions.Version(self._version_) # create this object to allow self._version_ to be specified in multiple different ways by the user
            if version.baseVersion not in self.installedApp.versionMap(): # verify that the selected version has an executable
                raise runConfigs.lib.SC2LaunchError(
                    "specified game version %s is not available.%s    available:  %s"%( \
                    version, os.linesep, "  ".join(self.installedApp.listVersions())))
            self._version = version
        else: # get most recent executable's version
            path = self.installedApp.exec_path()
            #vResult = int(re.search("Base(\d+)", path).groups()[0])
            vResult = self.installedApp.mostRecentVersion
            self._version = versions.Version(vResult)
            self._version_ = self._version.label
        if self.debug: print(os.linesep.join([
            "Game configuration detail:",
            "    platform:   %s"%(self.os),
            "    app:        %s"%(self.execPath),
            "    version:    %s"%(self._version)]))
        return self._version
    ############################################################################
    def addPlayerAgent(self, agentSelectRace=c.RANDOM):
        """add an agent slot to the game lobby; A human or AI is expected to play in that slot"""
        self._agentRaces_.append(agentSelectRace)
        self._agentRaces_ = sorted(self._agentRaces_)
    ############################################################################
    def addPlayerBot(self, botSelectRace=c.RANDOM, botDifficulty=c.MEDIUMHARD):
        """add a built-in bot to the game"""
        self._bots_.append( (botSelectRace, botDifficulty) )
        self._bots_ = sorted(self._bots_)
    ############################################################################
    def disable(self):
        try:
            os.remove(self.cfgFile) # delete the file
            del self.cfgFile        # forget the cfg file's name
        except: pass
    ############################################################################
    def display(self, header=""):
        h = "[%s]  "%header.upper() if header else ""
        for k,v in sorted(iteritems(self.__dict__)):
            print("%s%16s : %s"%(h,k,v))
    ############################################################################
    def clearCachedAttrs(self):
        """cause the internally defined parameters to be cleared, allowing them to be regenerated"""
        for k,v in list(iteritems(self.__dict__)):
            if re.search(Config.regexCache, k):
                delattr(self, k)
    ############################################################################
    def launchApp(self, fullScreen=True, **kwargs):
        """Launch Starcraft2 process in the background using this configuration"""
        app = self.installedApp
        # TODO -- launch host in window minimized mode
        vers = self.version
        proc = app.start(game_version=vers.baseVersion, data_version=vers.dataHash,
            port=self.ports[0], full_screen=fullScreen, verbose=self.debug, **kwargs)
        return proc
    ############################################################################
    def load(self, cfgFile=None, timeout=None):
        """expect that the data file has already been established"""
        if cfgFile != None: self.cfgFile = cfgFile # if it's specified, use it
        elif hasattr(self, "cfgFile"):  pass
        elif timeout: # wait for a configuration file to appear to be loaded
            self.cfgFile = cfgFile
            startWait = time.time()
            timeReported = 0
            while self.cfgFile==None:
                timeWaited = time.time() - startWait
                if timeWaited > timeout:
                    raise c.TimeoutExceeded("could not join game after %s seconds"%(timeout))
                try:
                    cfgs = activeConfigs()
                    self.cfgFile = cfgs.pop()
                except:
                    if self.debug and timeWaited - timeReported >= 1:
                        timeReported += 1
                        print("second(s) waited for game to appear:  %d"%(timeReported))
        else:
            cfgs = activeConfigs()
            if   len(cfgs) < 1: raise Exception("must have a saved configuration to load")
            elif len(cfgs) > 1: raise Exception("found too many configurations (%s); not clear which to load: %s"%(len(cfgs), cfgs))
            self.cfgFile = cfgs[0]
        with open(self.cfgFile, "rb") as f:
            d, self.slaveConnections = json.loads( f.read() )
        self.clearCachedAttrs() # ensure cached data is cleared to reflect current raw data
        self.__dict__.update(d)
        self.host = bool(re.search("^host", os.path.basename(cfgFile)))
        if self.debug:
            print("configuration loaded: %s"%(self.name))
            self.display()
    ############################################################################
    def newMap(self, mapName=None):
        """load this new map as part of the configuration"""
        try:    del self._mapAbsPath
        except: pass # if no map was defined previously, that's okay
        if mapName:
            mapName = os.path.basename(mapName).split('.')[0]
            mapName = re.sub("[LTE]+$", "", mapName)
        self._mapName_ = mapName
        return mapName
    ############################################################################
    def save(self):
        """save a data file such that all processes know the game that is running"""
        data = dict(self.__dict__)
        for k,v in sorted(iteritems(data)):
            if re.search(Config.regexRaw, k): continue # ignore attrs that aren't raw data
            del data[k]
        if self.debug:
            print("saved configuration %s"%(self.name))
            for k,v in sorted(iteritems(data)):
                print("%15s : %s"%(k,v))
        with open(self.name, "wb") as f: # save config data file
            f.write(str.encode(json.dumps((data, self.slaveConnections), indent=4)))
    ############################################################################
    def saveReplay(self):
        raise NotImplementedError
    #  def save_replay(self, replay_data, replay_dir, map_name):
    #    """Save a replay to a directory, returning the path to the replay."""
    ############################################################################
    def updateID(self, value):
        setattr(self, "_playerID_", value)
    ############################################################################
    def updateRaw(self, **kwargs):
        """apply all passed parameters as object attributes with values"""
        for k,v in iteritems(kwargs):
            setattr(self, "_%s_"%k, v) # the double underscore signals a special, raw attr
        if kwargs: self.clearCachedAttrs() # ensure decorated methods recalculate their cached valued since raw data may have changed

