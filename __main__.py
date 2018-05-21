
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

from six import iteritems # python 2/3 compatibility
from argparse import ArgumentParser

import sys

from sc2gamemgr import versions


################################################################################
if __name__ == "__main__":
    usage_def = ""
    parser = ArgumentParser(usage_def)
    #parser.add_argument("-d", "--debug" , action="store_true", help="Enable additional information.")
    # game commands
    parser.add_argument("--host"        , action="store_true", help="host a new game.")
    parser.add_argument("--join"        , action="store_true", help="join an existing game.")
    parser.add_argument("--clear"       , action="store_true", help="purge knowledge of any existing games.")
    parser.add_argument("--games"       , type=str,default="", help="display known existing games.")
    # version handling
    parser.add_argument("--update"      , type=str,default="", help="update an existing version............................ format: <label>,<version>,<base-version>")
    parser.add_argument("--add"         , type=str,default="", help="add a new version..................................... format: <label>,<version>,<base-version>")
    parser.add_argument("--versions"    , action="store_true", help="display known versions.")
    #type=str,default="", 
    #parser.add_argument('entities', nargs='*') # the remaining arguments are processed together
    options = parser.parse_args()
    sys.argv = sys.argv[:1] # remove all arguments to avoid problems with absl FLAGS :(

    if   options.add:       versions.addNew(*options.add.split(','))
    elif options.update:
        keys = [
            "label",
            "version",
            "base-version",
            "data-hash",
            "fixed-hash",
            "replay-hash",
        ]
        data = {}
        for k,v in zip(keys, options.update.split(',')):
            data[k] = v
        versions.handle.update(data)
        versions.handle.save()
        
    if options.versions: # simply display the jsonData reformatted
        for v,record in sorted(iteritems(versions.handle.ALL_VERS_DATA)):
            print(v)
            for k,v in sorted(iteritems(record)):
                print("%15s: %s"%(k,v))
            print()

