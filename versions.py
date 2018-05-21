
from __future__ import absolute_import
from __future__ import division       # python 2/3 compatibility
from __future__ import print_function # python 2/3 compatibility

from six import iteritems # python 2/3 compatibility
from builtins import str as text # python 2/3 compatibility
from io import BytesIO # python 2/3 compatibility

from sc2gamemgr import dateFormat
from sc2gamemgr import gameConstants as c

import json
import os
import re
import time


"""
Starcraft 2 patch/update information is copied from the following site(s):
    http://liquipedia.net/starcraft2/Patch_4.2.3 (and links listed on the page)
"""


################################################################################
def addNew(label, version, baseVersion, dataHash="", fixedHash="", replayHash=""):
    """
    Add a new version record to the database to be tracked
    VERSION RECORD EXAMPLE:
        "base-version": 55505, 
        "data-hash": "60718A7CA50D0DF42987A30CF87BCB80", 
        "fixed-hash": "0189B2804E2F6BA4C4591222089E63B2", 
        "label": "3.16", 
        "replay-hash": "B11811B13F0C85C29C5D4597BD4BA5A4", 
        "version": 55505
        """
    baseVersion = int(baseVersion)
    version     = int(version)
    minVersChecks = {"base-version":baseVersion, "version":version}
    if label in handle.ALL_VERS_DATA:
        raise ValueError("given record label (%s) is already defined.  Consider performing update() for this record instead"%(label))
    for vCheckK,vCheckV in iteritems(minVersChecks): # verify no conflicting values
        maxVersion  = min([vData[vCheckK] for vData in handle.ALL_VERS_DATA.values()])
        if vCheckV < c.MIN_VERSION_AI_API:
            raise ValueError("version %s / %s.%s does not support the Starcraft2 API"%(baseVersion, label, version))
        if vCheckV < maxVersion: # base version cannot be smaller than newest value
            raise ValueError("given %s (%d) cannot be smaller than newest known %s (%d)"%(vCheckK, vCheckV, vCheckK, maxVersion))
    uniqueValHeaders = list(c.JSON_HEADERS)
    uniqueValHeaders.remove("base-version")
    record = {"base-version" : baseVersion}
    #print("%15s : %s (%s)"%("base-version", baseVersion, type(baseVersion)))
    for k,v in zip(uniqueValHeaders, [label, version, dataHash, fixedHash, replayHash]): # new attr values must be unique within all handler records
        record[k] = v # convert to dict while checking each param
        #print("%15s : %s (%s)"%(k,v,type(v)))
        if not v: continue # ignore uniqueness requirement if value is unspecified
        if v in [r[k] for r in Handler.ALL_VERS_DATA.values()]:
            raise ValueError("'%s' '%s' is in known values: %s"%(k, v, getattr(handle, k)))
            return
    handle.save(new=record)


################################################################################
#def update(version, newValues):
#    """
#    USAGE EXAMPLES:
#        update(59729, {"fixed-hash":"123"})
#        update("3.19", {"replay-hash":"WHATEVER231"})
#    """
#    if len(newValues) == 0: raise ValueError("must provide data in paramater newValues else cannot update any record")
#    try:
#            int(version)
#            versionKey = "version"
#    except: versionKey = "label"
#    records = handle.search(version) # match record where versionKey value == version
#    if   len(records) > 1: raise ValueError("identified too many records (%d): %s"%(len(records), records))
#    elif len(records) < 1: raise ValueError("failed to identify any records given params: %s"%(records))
#    record = records.pop() # access the single, found record
#    for k,v in iteritems(newValues):   record[k] = v
#    handle._updated = True
#    handle.save()


################################################################################
class Handler(object):
    """NOTE: the data-hash field is required to launch stand-alone versions of the game"""
    ############################################################################
    ALL_VERS_DATA = None
    ############################################################################
    def __init__(self):
        self.load()
    ############################################################################
    #def __getattr__(self, key):
    #    """get all record values of a given key"""
    #    return sorted([v[key] for v in Handler.ALL_VERS_DATA.values()])
    ############################################################################
    def __len__(self):
        """the number of known version records"""
        return len(Handler.ALL_VERS_DATA)
    ############################################################################
    @property
    def mostRecent(self):
        records = iteritems(Handler.ALL_VERS_DATA)
        try: 
            label,record = max(records)
            return record
        except ValueError: return None # no versions are installed
    ############################################################################
    #def get(self, key, versFilter=""):
    #    """get a values of key where records match versFilter"""
    #    for v in self.search(versFilter): print(v)
    #    return [v[key] for v in self.search(versFilter)]
    ############################################################################
    def load(self):
        """load ALL_VERS_DATA from disk"""
        basepath = os.path.dirname(os.path.abspath(__file__))
        filename = os.sep.join([basepath, c.FOLDER_JSON, c.FILE_GAME_VERSIONS])
        Handler.ALL_VERS_DATA = {} # reset known data; do not retain defunct information
        with open(filename, "rb") as f:
            data = json.loads( f.read() )
        self.update(data)
        self._updated = False
        #for v,record in iteritems(Handler.ALL_VERS_DATA):
        #    print(type(v), v)
            #for k,v in iteritems(record):    
    ############################################################################
    def save(self, new=None, timeout=2):
        """write ALL_VERS_DATA to disk in 'pretty' format"""
        if new: self.update(new) # allow two operations (update + save) with a single command
        if not self._updated: return # nothing to do
        thisPkg = os.path.dirname(__file__)
        filename = os.path.join(thisPkg, c.FOLDER_JSON, c.FILE_GAME_VERSIONS)
        fParts = c.FILE_GAME_VERSIONS.split('.')
        newFile = os.path.join(thisPkg, c.FOLDER_JSON, "%s_%s.%s"%(fParts[0], dateFormat.now(), fParts[1]))
        if not os.path.isfile(newFile):
            #fParts = c.FILE_GAME_VERSIONS.split('.')
            #newFile = "%s%s%s_%s.%s"%(c.FOLDER_JSON, os.sep, fParts[0], dateFormat.now(), fParts[1])
            #if not os.path.isfile(newFile):
            #print(filename)
            #print(newFile)
            os.rename(filename, newFile) # backup existing version file
        recordKeys = [(record["version"], record) for record in Handler.ALL_VERS_DATA.values()]
        data = [r for k,r in sorted(recordKeys)] # i.e. get values sorted by version key
        start = time.time()
        while time.time()-start < timeout: # allow multiple retries if multiple processes fight over the version file
            try:
                with open(filename, "wb") as f:
                    f.write(str.encode(json.dumps(data, indent=4, sort_keys=True))) # python3 requires encoding str => bytes to write to file
                self._updated = False
                return
            except IOError: pass # continue waiting for file to be available
        raise # after timeout, prior exception is what matters
    ############################################################################
    def search(self, *args, **kwargs):
        """match all records that have any args in any key/field that also match
        key/value requirements specified in kwargs"""
        ret = []
        for record in Handler.ALL_VERS_DATA.values():
            matchArgs = list(kwargs.keys())
            for k,v in iteritems(kwargs): # restrict records based on key-value match requirement
                try:
                    if record[k] != v: break # a non-matching requirement means this record doesn't match
                except: break # record doesn't have required key 'k'
                matchArgs.remove(k)
            if matchArgs: continue # didn't match all required kwargs
            matchArgs = list(args)
            for k,v in iteritems(record): # find any record with a <value> in it
                if k in matchArgs: matchArgs.remove(k)
                if v in matchArgs: matchArgs.remove(v)
            if matchArgs: continue # didn't match all required args
            ret.append(record)
        return ret
    ############################################################################
    #def search(self, searchVal, keyOnly=None, **filters):
    #    """identify all version records where searchVal exists (can be a regex)"""
    #    ########################################################################
    #    def checkValues(vData, regex):
    #        for k,v in iteritems(vData):
    #            #if k == "base-version": continue # ignore matching this key; expect it will match 'version' key where applicable
    #            if re.search(regex, str(v)): return True
    #        return False
    #    ########################################################################
    #    _tmp = re.compile("")
    #    if type(searchVal) == type(_tmp):
    #          regex = searchVal
    #    else: regex = re.compile(str(searchVal))
    #    ret = {}
    #    if keyOnly!=False: # search all keys (only)
    #        for vers in Handler.ALL_VERS_DATA.values():
    #            if any([re.search(regex, str(k)) for k in vers.keys()]):
    #                ret[vers["label"]] = vers
    #    if keyOnly!=True: # search all values (only)
    #        for vers in Handler.ALL_VERS_DATA.values():
    #            if checkValues(vers, regex):   ret[vers["label"]] = vers
    #    return ret.values()
    ############################################################################
    def update(self, data):
        """update known data with with newly provided data"""
        if not isinstance(data, list): data = [data] # otherwise no conversion is necessary
        master = Handler.ALL_VERS_DATA
        for record in data:
            #print(record)
            for k,v in iteritems(record): # ensure record contents aretyped appropriately
                try:                record[k] = int(v)
                except ValueError:  record[k] = v
            try: label = record["label"] # verify this record has the required 'label' key
            except KeyError:
                raise ValueError("Must provide a valid label argument.  Given:%s%s"%(\
                    os.linesep, ("%s  "%(os.linesep)).join(
                        ["%15s:%s"%(k,v) for k,v in iteritems(kwargs)]
                    )))
            try:    masterLabel = master[label] # identify the already existing record that matches this to-be-updated record, if any
            except KeyError: # master hasn't been defined yet
                master[label] = record
                self._updated = True # a new record should also be saved
                continue
            for k,v in iteritems(record): # determine whether master needs to be updated
                try:
                    if masterLabel[k] == v:  continue # whether an entry in the record needs to be updated (doesn't match)
                except KeyError:             pass # this condition means that k is a new key, so the record must be updated
                self._updated = True
                try:    master[label].update(record) # index each record by its label
                except KeyError:             break


################################################################################
handle = Handler()
#newRecord = {
#    "fixed-hash": "", 
#    "replay-hash": "", 
#    "data-hash": "", 
#    "label": "4.2.4", 
#    "base-version": 63454, 
#    "version": 64128
#}
#handle.save(new=newRecord)


################################################################################
class Version(object):
    ############################################################################
    def __init__(self, versionVal=None):
        if versionVal: # get specific version
            records = handle.search(versionVal)
            if   len(records) > 1: raise ValueError("identified too many records (%d): %s"%(len(records), records))
            elif len(records) < 1: raise ValueError("first collect and update version information for version: %s"%(versionVal))
            record = records.pop()
        else: # select most recent version
            record = handle.mostRecent
        for k in c.JSON_HEADERS: # convert hyphenated keys into code-compatible keys
            oldK = k
            wordBoundaries = re.search("(-\w)", k)
            if wordBoundaries:
                for wb in wordBoundaries.groups():
                    newWb = wb.upper().strip('-')
                    k = re.sub(wb, newWb, k)
            setattr(self, k, record[oldK])
        while self.label.count(".") < 2: self.label += ".0" # ensure a 3-field versioning scheme
    ############################################################################
    def __str__(self):  return self.__repr__()
    def __repr__(self):
        return "%s.%s"%(self.label, self.version)
    ############################################################################
    def __getitem__(self, key):
        return getattr(self, key)
    ############################################################################
    def toTuple(self, typeCast=int):
        return [typeCast(v) for v in self.label.split('.')]
    ############################################################################
    def toFilename(self):
        return re.sub("\.", "_", str(self.label))

