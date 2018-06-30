
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

from sc2common    import types
from sc2gameLobby import dateFormat
from sc2gameLobby import gameConstants as c
from sc2gameLobby import ipAddresses
#import mapData
from sc2gameLobby import runConfigs
from sc2gameLobby import versions

from sc2players import getPlayer, buildPlayer, PlayerRecord, PlayerPreGame
from sc2players import constants as playerConstants
from sc2ladderMgmt.ladders import Ladder
from sc2maptool.functions import selectMap
from sc2maptool.mapRecord import MapRecord

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
    """the grand collection of information that determines how a Starcraft 2
    game is setup and intended to behave"""
    ############################################################################
    def __init__(self, load=None,
        expo=c.DEFAULT_EXPANSION, version=None,
        ladder=None, players=[], whichPlayer="", mode=None, themap=None, numObservers=0, start=None, trust=True,
        ipAddress=[], ports=[], host=[], slaves=[],
        fogDisabled=False, stepSize=0, opponents=[], fullscreen=True,
        raw=False, score=False, feature=False, render=False,
        replay=None, debug=False,
            #connects=[], 
            #state=c.GAME_INIT,
            #agentRaces=[], bots=[], 
    ):
        self._gotPorts  = False # ensure that ports are only returned if they were retrieved on this machine
        # flexible settings auto-determination
        if isinstance(players, list):       pass
        elif hasattr(players, "__iter__"):  players = list(players)
        else:                               players = [players] # wrap
        # application setup info
        self.expo       = expo
        self.version    = version # automatically calculate unless specified
        # TODO version
        # match setup info
        self.ladder     = ladder
        self.players    = players
        self.thePlayer  = whichPlayer
        self.mode       = mode
        self.themap     = themap
        self.numObserve = int(numObservers)
        self.start      = start  # indicates the final match configuration has been determined
        self.trustOpps  = trust  # request secure game hosting on an official ladder machine
        # connection info
        self.ipAddress  = ipAddress
        self.ports      = ports
        self.host       = host   # if defined, this config is for a slave
        self.slavePorts = slaves # if not defined, this is for the host
        self.ladderMsg  = ""
        # in-game behavior
        self.fogDisabled= fogDisabled
        self.stepSize   = int(stepSize)      
        self.opponents  = opponents # names of specific opponents
        self.fullscreen = fullscreen
        # observation data content
        self.raw        = raw
        self.score      = score
        self.feature    = feature
        self.render     = render
        # post-game behavior
        self.replay     = replay
        # class behavior
        self.debug      = debug
        #self.state = c.GAME_INIT
        if load:    self.load(load) # specific configuration filename to load
        else:       self.inflate()  # ensure all objects are objects
        self.isCustom   = bool(self.opponents or self.fogDisabled or \
                               self.themap    or self.stepSize)
    ############################################################################
    def __str__(self):  return self.__repr__()
    def __repr__(self):
        name = self.__class__.__name__
        if self.slavePorts: ip = [str(x) for x in self.host] # this configuration is a host configuration when slave ports are defined
        else:               ip = [str(x) for x in self.connection]
        ipStr = " @ %s"%(":".join(ip)) if ip else ""
        return "<%s %s %s%s>"%(name, self.installedApp.name(), self.version, ipStr)
    ############################################################################
    def __del__(self):
        self.returnPorts()
        try:    self.disable()
        except IOError: pass
    ############################################################################
    @property
    def attrs(self):
        data = dict(self.__dict__)
        for k,v in sorted(iteritems(data)):
            #if re.search(Config.regexRaw, k): continue # ignore attrs that aren't raw data
            if re.search("^_", k):  del data[k]
        return data
    ############################################################################
    @property
    def agents(self):
        """identify which players are agents (not observers or computers). Errors if flattened."""
        ret = []
        for player in self.players:
            if player.isComputer: continue
            try:
                if player.observer: continue
            except: pass
            ret.append(player)
        return ret
    ############################################################################
    @property
    def agentRaces(self):
        """identify the races of the players that are agents. Errors if flattened."""
        return [player.selectedRace for player in self.players if not player.isComputer]
    ############################################################################
    @property
    def computers(self):
        """identify the players that are Blizzard's built-in bots. Errors if flattened."""
        return [player for player in self.players if player.isComputer]
    ############################################################################
    @property
    def allLobbySlots(self):
        """the current configuration of the lobby's players, defined before the match starts"""
        if self.debug:
            p      = ["Lobby Configuration detail:"] + \
                     ["    %s:%s%s"%(p, " "*(12-len(p.type)), p.name)]
                     #["    agent:     %s"%p for p in self.agents] + \
                     #["    computer:  %s, %s"%(r,d) for r,d in self.computers]
            if self.observers: # must separate condition because numObs is a number, not an iterator
                p += ["    observers: %d"%self.observers]
            print(os.linesep.join(p))
        return (self.agents, self.computers, self.observers)
    ############################################################################
    @property
    def connection(self):
        """identify the remote connection parameters"""
        self.getPorts()         # acquire if necessary
        self.getIPaddresses()   # acquire if necessary
        return (self.ipAddress, self.ports)
    ############################################################################
    @property
    def execPath(self):
        """the executable application's path"""
        vers = self.version.label if self.version else None # executables in Versions folder are stored by baseVersion (modified by game data patches)
        return self.installedApp.exec_path(vers)
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
        return (self.raw    , self.score,
                self.feature, self.render)
    ############################################################################
    @property
    def isHost(self):
        """is the host if it lacks host details"""
        return not bool(self.host) and bool(self.slavePorts)
    ############################################################################
    @property
    def isMultiplayer(self):
        return self.numGameClients > 1
    ############################################################################
    @property
    def mapData(self):
        """the raw, binary contents of the Starcraft2 map file"""
        return self.themap.rawData
        #with open(self.themap.path, "rb") as f:
        #    return f.read()
    ############################################################################
    @property
    def mapLocalPath(self):
        return self.themap.path
    ############################################################################
    @property
    def name(self):
        #try:    return self.cfgFile
        #except: pass # else extract name from loaded cfg name
        #k = "host" if self.host else os.getpid()
        #self.cfgFile = os.path.join(c.FOLDER_ACTIVE_CONFIGS, "%s_%s.json"%(k, dateFormat.now()))
        #return self.cfgFile
        return os.path.join(
                    c.FOLDER_ACTIVE_CONFIGS,
                    "%s_%s.json"%(os.getpid(), dateFormat.now(self.start)))
    ############################################################################
    @property
    def numAgents(self):
        return len(self.agents)
    ############################################################################
    @property
    def numBots(self):
        return len(self.computers)
    ############################################################################
    @property
    def numGameClients(self):
        """the number of game client connections in the match"""
        return self.numAgents + self.numObserve
    ############################################################################
    @property
    def numPlayers(self):
        #return self.numAgents + self.numBots
        return len(self.players)
    ############################################################################
    @property
    def observers(self):
        """the players who are actually observers"""
        ret = []
        for player in self.players:
            try:
                if player.observer: ret.append(player)
            except: pass # ignore PlayerRecords which don't have an observer attribute
        return ret
    ############################################################################
    @property
    def os(self):
        """the operating system this match is loaded on"""
        return self.installedApp.name()
    ############################################################################
    @property
    def participants(self):
        """agents + computers (i.e. all non-observers)"""
        ret = []
        for p in self.players:
            try:
                if     p.isComputer: ret.append(p)
                if not p.isObserver: ret.append(p) # could cause an exception if player isn't a PlayerPreGame
            except AttributeError: pass
        return ret
    ############################################################################
    @property
    def realtime(self):
        """whether the game progresses in realtime or requires each player to
        summit step requests to advance the game"""
        return not bool(self.stepSize)
    ############################################################################
    @property
    def teams(self):
        players = self.participants
        div     = len(players) / 2.
        teamSize= int(div)
        if (div - teamSize) > 0.49: # if odd number of participants
            teamSize += 1 # if remainder, round up
        return (players[:teamSize], players[teamSize:])
    ############################################################################
    def addPlayer(self, player):
        if not isinstance(player, PlayerPreGame):
            raise ValueError("%s must be a %s"%(player, PlayerPreGame))
        self.players.append(player)
    ############################################################################
    def disable(self):
        try:
            os.remove(self.name) # delete the file
            #del self.cfgFile        # forget the cfg file's name
        except: pass
    ############################################################################
    def display(self, header=""):
        print(self)
        h = "[%s]  "%header.upper() if header else ""
        for k,v in sorted(iteritems(self.attrs)):
            print("%s%16s : %s"%(h,k,v))
    ############################################################################
    def flatten(self, data=None):
        """reduce all objects into simplified values as a attr dictionary that
        could be transformed back into a full configuration via inflate()"""
        if data == None: data=self.attrs
        ret = {}
        for k,v in iteritems(data):
            if   k == "expo":               v = v.type
            elif k == "version":            v = v.label
            elif k == "ladder":             v = v.name
            elif k == "players":
                newPs = []
                for i,p in enumerate(v):
                    try:    diff = p.difficulty.type
                    except: diff = p.difficulty
                    if isinstance(p, PlayerPreGame):    newPs.append( (p.name, p.type.type, p.initCmd, diff, p.rating, p.selectedRace.type, self.numObserve, p.playerID) )
                    else:                               newPs.append( (p.name, p.type.type, p.initCmd, diff, p.rating) )
                # TODO -- handle if type or observers params are not available (i.e. if a simple PlayerRecord, not a PlayerPreGame
                ret[k] = newPs
                continue
            elif k == "mode"   and self.mode:   v = v.type
            #elif k == "state":              
            elif k == "themap" and self.themap: v = v.name
            ret[k] = v
        return ret
    ############################################################################
    def inflate(self, newData={}):
        """ensure all object attribute values are objects"""
        self.__dict__.update(newData)
        #if not isinstance(self.state, types.GameStates):      self.state     = types.GameStates(self.state)
        if self.expo    and not isinstance(self.expo, types.ExpansionNames):    self.expo       = types.ExpansionNames(self.expo)
        if self.version and not isinstance(self.version, versions.Version):     self.version    = versions.Version(self.version)
        if self.ladder  and not isinstance(self.ladder, Ladder):                self.ladder     = Ladder(self.ladder)
        for i,player in enumerate(self.players): # iterate over all players
            if       isinstance(player, str):                                   self.players[i] = getPlayer(player)
            elif not isinstance(player, PlayerRecord):                          self.players[i] = buildPlayer(*player)
        if self.mode    and not isinstance(self.mode, types.GameModes):         self.mode       = types.GameModes(self.mode)
        if self.themap  and not isinstance(self.themap, MapRecord):             self.themap     = selectMap(name=self.themap)
    ############################################################################
    def launchApp(self, fullScreen=True, **kwargs):
        """Launch Starcraft2 process in the background using this configuration"""
        app = self.installedApp
        # TODO -- launch host in window minimized mode
        vers = self.getVersion()
        proc = app.start(version=vers,#game_version=vers.baseVersion, data_version=vers.dataHash,
            port=self.getPorts()[0], full_screen=fullScreen, verbose=self.debug, **kwargs)
        return proc
    ############################################################################
    def load(self, cfgFile=None, timeout=None):
        """expect that the data file has already been established"""
        #if cfgFile != None: self.cfgFile = cfgFile # if it's specified, use it
        if not cfgFile:
            cfgs = activeConfigs()
            if   len(cfgs) > 1: raise Exception("found too many configurations (%s); not clear which to load: %s"%(len(cfgs), cfgs))
            elif len(cfgs) < 1:
                if timeout: # wait for a configuration file to appear to be loaded
                    startWait = time.time()
                    timeReported = 0
                    while not cfgs:
                        timeWaited = time.time() - startWait
                        if timeWaited > timeout:
                            raise c.TimeoutExceeded("could not join game after %s seconds"%(timeout))
                        try:  cfgs = activeConfigs()
                        except:
                            if self.debug and timeWaited - timeReported >= 1:
                                timeReported += 1
                                print("second(s) waited for game to appear:  %d"%(timeReported))
                else:  raise Exception("must have a saved configuration to load or allow loading via timeout setting")
            cfgFile = cfgs.pop()
        with open(cfgFile, "rb") as f:
            data = f.read() # bytes => str
        self.loadJson(data) # str => dict
        if self.debug:
            print("configuration loaded: %s"%(self.name))
            self.display()
    ############################################################################
    def updateID(self, value, player=None):
        """ensure this player's player ID is specified by the host client"""
        if player == None:
            player = self.whoAmI()
        player.playerID = value
    ############################################################################
    def loadJson(self, data):
        """convert the json data into updating this obj's attrs"""
        if not isinstance(data, dict):
            data = json.loads(data)
        self.__dict__.update(data)
        self.inflate() # restore objects from str values
        #if self.ports:  self._gotPorts = True
        return self
    ############################################################################
    def toJson(self, data=None, pretty=False):
        """convert the flattened dictionary into json"""
        if data==None: data = self.attrs
        data = self.flatten(data) # don't send objects as str in json
        #if pretty:
        ret = json.dumps(data, indent=4, sort_keys=True)
        #self.inflate() # restore objects from json str data
        return ret
    ############################################################################
    def getVersion(self):
        """the executable application's version"""
        if isinstance(self.version, versions.Version):  return self.version
        if self.version: # verify specified version exists
            version = versions.Version(self.version) # create this object to allow self._version_ to be specified in multiple different ways by the user
            if version.baseVersion not in self.installedApp.versionMap(): # verify that the selected version has an executable
                raise runConfigs.lib.SC2LaunchError(
                    "specified game version %s executable is not available.%s    available:  %s"%( \
                    version, os.linesep, "  ".join(self.installedApp.listVersions())))
            self.version = version
        else: # get most recent executable's version
            path = self.installedApp.exec_path()
            vResult = self.installedApp.mostRecentVersion
            self.version = versions.Version(vResult)
        if self.debug: print(os.linesep.join([
            "Game configuration detail:",
            "    platform:   %s"%(self.os),
            "    app:        %s"%(self.execPath),
            "    version:    %s"%(self.version)]))
        return self.version
    ############################################################################
    def getIPaddresses(self):
        """identify the IP addresses where this process client will launch the SC2 client""" 
        if not self.ipAddress:
            self.ipAddress = ipAddresses.getAll() # update with IP address
        return self.ipAddress
    ############################################################################
    def getPorts(self):
        """acquire ports to be used by the SC2 client launched by this process"""
        if self.ports: # no need to get ports if ports are al
            return self.ports
        if not self._gotPorts:
            #if len(self.players)==0:
            #    p = getPlayer(self.players[0])
            #    if self.isComputer: return self.ports
            self.ports = [
                portpicker.pick_unused_port(), # game_port
                portpicker.pick_unused_port(), # base_port
                portpicker.pick_unused_port(), # shared_port
            ]
            self._gotPorts = True
        return self.ports
    ############################################################################
    def returnPorts(self):
        """deallocate specific ports on the current machine"""
        if self._gotPorts:
            print("deleting ports >%s<"%(self.ports))
            map(portpicker.return_port, self.ports)
            self._gotPorts = False
        self.ports = []
    ############################################################################
    def save(self, filename=None, debug=False):
        """save a data file such that all processes know the game that is running"""
        if not filename: filename = self.name
        with open(filename, "w") as f: # save config data file
            f.write(self.toJson(self.attrs))
        if self.debug or debug:
            print("saved configuration %s"%(self.name))
            for k,v in sorted(iteritems(self.attrs)):
                print("%15s : %s"%(k,v))
    ############################################################################
    def whoAmI(self):
        """return the player object that owns this configuration"""
        self.inflate() # ensure self.players contains player objects
        if self.thePlayer:
            for p in self.players:
                if p.name != self.thePlayer: continue
                return p
        elif len(self.players) == 1:
            ret = self.players[0]
            self.thePlayer = ret.name # remember this for the future in case more players are added
            return ret
        raise Exception("could not identify which player this is given %s (%s)"%(self.players, self.thePlayer))

