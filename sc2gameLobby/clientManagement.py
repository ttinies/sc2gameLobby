
from s2clientprotocol import sc2api_pb2
from pysc2.lib import protocol
from pysc2.lib import remote_controller

import portpicker
import queue
import socket
import sys
import time
import websocket

from sc2gameLobby import gameConstants as c


################################################################################
class ClientController(remote_controller.RemoteController):
    """similar to pysc2 StarcratProcess, but without the process to enable multiple game connections"""
    ############################################################################
    def __init__(self, url=None, port=None, timeout=c.INITIAL_TIMEOUT):
        sys.argv = sys.argv[:1] # trim to force flags to do nothing
        FLAGS = protocol.flags.FLAGS
        FLAGS(sys.argv) # always ensure flags did its checking
        self._url       = None
        self._port      = None
        self._client    = None
        self._name      = ""
        if url!=None or port!=None:
            self.connect(url=url, port=port, timeout=timeout)
    ############################################################################
    def __str__(self): return self.__repr__()
    def __repr__(self):
        url  = " %s"     %self._url  if self._url  else ""
        port = ":%s"%self._port if self._port else ""
        try:    stat = self.status
        except: stat = "disconnected"
        return "<%s%s%s %s>"%(self.name, url, port, stat)
    ############################################################################
    def __nonzero__(self):
        """whether this ClientController is connected"""
        try:    self.status
        except: return False
        return True
    ############################################################################
    @property
    def name(self):
        if not self._name: # execute only once, if needed
            self._name = str(self.__class__).split('.')[-1].rstrip("'>")
        return self._name
    ############################################################################
    def close(self):
        """Shut down the socket connection, client and controller"""
        self._sock = None
        self._controller = None
        if hasattr(self, "_port") and self._port:
            portpicker.return_port(self._port)
            self._port = None
    ############################################################################
    def __enter__(self):
        return self
    ############################################################################
    def __exit__(self, unused_exception_type, unused_exc_value, unused_traceback):
        self.close()
    ############################################################################
    def __del__(self):
        # Prefer using a context manager, but this cleans most other cases.
        self.close()
    ############################################################################
    def connect(self, url=c.LOCALHOST, port=None, timeout=c.INITIAL_TIMEOUT,
                      debug=False):
        """socket connect to an already running starcraft2 process"""
        if port != None: # force a selection to a new port
            if self._port!=None: # if previously allocated port, return it
                portpicker.return_port(self._port)
            self._port = port
        elif self._port==None: # no connection exists
            self._port = portpicker.pick_unused_port()
        self._url = url
        if ":" in url and not url.startswith("["):  # Support ipv6 addresses.
            url = "[%s]" % url
        for i in range(timeout):
            startTime = time.time()
            if debug:
                print("attempt #%d to websocket connect to %s:%s"%(i, url, port))
            try:
                finalUrl = "ws://%s:%s/sc2api" %(url, self._port)
                ws = websocket.create_connection(finalUrl, timeout=timeout)
                #print("ws:", ws)
                self._client = protocol.StarcraftProtocol(ws)
                #super(ClientController, self).__init__(client) # ensure RemoteController initializtion is performed
                #if self.ping(): print("init ping()") # ensure the latest state is synced
                # ping returns:
                #   game_version:   "4.1.2.60604"
                #   data_version:   "33D9FE28909573253B7FC352CE7AEA40"
                #   data_build:     60604
                #   base_build:     60321
                return self
            except socket.error: pass  # SC2 hasn't started listening yet.
            except websocket.WebSocketException as err:
                print(err, type(err))
                if "Handshake Status 404" in str(err):
                    pass  # SC2 is listening, but hasn't set up the /sc2api endpoint yet.
                else: raise
            except Exception as e:
                print(type(e), e)
            sleepTime = max(0, 1 - (time.time() - startTime)) # try to wait for up to 1 second total
            if sleepTime:   time.sleep(sleepTime)
        raise websocket.WebSocketException("Could not connect to game at %s on port %s"%(url, port))
    ############################################################################
    @remote_controller.valid_status(remote_controller.Status.in_game)
    def debug(self, *debugReqs):
        """send a debug command to control the game state's setup"""
        return self._client.send(debug=sc2api_pb2.RequestDebug(debug=debugReqs))
    ############################################################################
    def getNewReplay(self):
        request = sc2api_pb2.RequestReplayInfo(replay_path="dummy.SC2Replay", download_data=True)
        #request.replay_path = ?
        #request.replay_data = ?
        #request.download_data=True
        return self._client.send(replay_info=request)


ClientController.__bool__ = ClientController.__nonzero__ # python2-3 compatibility

