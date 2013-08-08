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

import re

import table


class DataFile(object):
    """Used to open, read and write all files of all supported types."""
    def __init__(self, filename):
        self.filename = filename
        self.aliasgenerator = self._generatealias()
#        self.sqltable = table.Table()

    # generate and return an alias for the file. Each time a file is opened
    def _generatealias(self):
        """Creates a unique alias for a file."""
        filenamesplit = re.findall('[a-zA-Z0-9]+', self.filename)
        alias = filenamesplit[-2]
        # start with just the filename
        yield alias
        # append a number for successive alias requests
        dupecount = 1
        aliaslen = len(alias)  # store original length
        while True:
            # append next number to original alias
            alias = alias[:aliaslen] + str(dupecount)
            yield alias
            dupecount += 1

    def getnewalias(self):
        """Returns a modified, hopefully unique, file alias."""
        return self.aliasgenerator.next()

    # XXX call getattributeorder() instead?
    def getattributenames(self):
        return self.fieldattrorder

    def __iter__(self):
        return self.filehandler.__iter__()
