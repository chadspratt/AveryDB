"""TableManager manages SQLite tables that are created from the input files."""
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

import table


class TableManager(object):
    """Orchestrates converting input files to SQLite tables."""
    def __init__(self):
        self.tables = {}
        # clear the sqlite db. could alternately do this on program close
        sqlitefile = open('temp.db', 'w')
        sqlitefile.truncate(0)
        sqlitefile.close()

    def addtable(self, filealias, filehandler):
        """Get a generator that converts the input file to an SQLite table."""
        newtable = table.Table(filealias)
        self.tables[filealias] = newtable
        conversiongenerator = newtable.readfile(filehandler)
        return conversiongenerator

    def buildsqlindex(self, indexalias, indexfield):
        """Build an index on the given field of the given table."""
        self.tables[indexalias].buildindex(indexfield)
