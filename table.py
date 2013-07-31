"""Table stores an input file as an SQLite table and adds indexes to it."""
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
import sqlite3
from collections import OrderedDict


class Table(object):
    """Controls an SQLite table used for storing values from an input file."""
    def __init__(self, tablename):
        self.tablename = tablename
        self.sqlname = 'table_' + tablename
        # fields[fieldname] = field
        self.fields = OrderedDict()

    # long-running, should yield periodically so the GUI can function
    def readfile(self, inputfile):
        """Read the contents of a data file in to an SQLite table."""
        for field in inputfile.getfields():
            self.fields[field.originalname] = field
            field.sqlname = (self.tablename + '_' + field.originalname + ' ' +
                             field['type'])
        # create a string of question marks for the queries
        # one question mark for each field. four fields = '?, ?, ?, ?'
        qmarklist = []
        for _counter in range(len(self.fields)):
            qmarklist.append('?')
        qmarks = ', '.join(qmarklist)

        # open the database
        conn = sqlite3.connect('temp.db')
        cur = conn.cursor()
        # make a list of the field names, as they'll be in the table
#        sqlfieldnames = [f.sqlname for f in self.fields.values()]
        sqlfieldnames = [self.fields[fn].sqlname for fn in self.fields]
        # create the table
        cur.execute('CREATE TABLE ' + self.sqlname + ' (' +
                    ', '.join(sqlfieldnames) + ')')
        recordcount = inputfile.getrecordcount()
        i = 0
        insertquery = ('INSERT INTO ' + self.sqlname +
                       ' VALUES (' + qmarks + ');')
        # insert each record from the input file
        for record in inputfile:
            values = [record[fn] for fn in self.fields]
            cur.execute(insertquery, values)
            i += 1
            # Take a break so the gui can be used
            if i % 250 == 0:
                if recordcount is None:
                    yield 'pulse'
                else:
                    yield float(i) / recordcount
        conn.commit()

    def buildindex(self, fieldname):
        """Create an index for a given field."""
        # open the database
        conn = sqlite3.connect('temp.db')
        cur = conn.cursor()
        print ('CREATE INDEX IF NOT EXISTS ' +
               self.fields[fieldname].sqlname +
               '_index ON ' + self.sqlname + '(' +
               self.fields[fieldname].sqlname + ')')
        cur.execute('CREATE INDEX IF NOT EXISTS ' +
                    self.fields[fieldname].sqlname +
                    '_index ON ' + self.sqlname + '(' +
                    self.fields[fieldname].sqlname + ')')
