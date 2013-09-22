"""Retrieves, stores, and otherwise manages program options."""
##
#   Copyright 2013 Chad Spratt
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
##
import json


class OptionsManager(object):
    """docstring for Options"""
    def __init__(self):
        self.optionspath = 'dbfutil.config'
        self.optionsdata = {}

    def loadoptions(self):
        optionsfile = open(self.optionspath)
        self.optionsdata = json.load(optionsfile)

    def saveoptions(self):
        optionsfile = open(self.optionspath, 'w')
        optionsfile.write(json.dumps(self.optionsdata, indent=4, separators=(',', ': '), sort_keys=True))

    def __getitem__(self, key):
        return self.optionsdata[key]

    def __setitem__(self, key, value):
        self.optionsdata[key] = value

