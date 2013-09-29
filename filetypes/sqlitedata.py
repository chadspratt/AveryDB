"""SQLiteFile is used to provide a standardized interface to sqlite3."""
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
from collections import OrderedDict
import re
import sqlite3

import table
import field


class SQLiteData(table.Table):
    """Handle all input and output for "example" files (not a real format)."""
    def __init__(self, filename, tablename=None, mode='r'):
        super(SQLiteData, self).__init__(filename, tablename=None)
        # If no table name was passed
        if tablename is None:
            # connect to the database
            with sqlite3.connect(filename) as conn:
                cur = conn.cursor()
                # get a list of the tables
                cur.execute("SELECT name FROM sqlite_master " +
                            "WHERE type='table' ORDER BY name")
                tablenames = [result[0] for result in cur.fetchall()]
                # and return the list in an exception
                raise table.NeedTableError(tablenames)
        self.tablename = tablename
        self.fieldattrorder = ['Name', 'Affinity', 'Value']
        self.blankvalues = {'TEXT': '', 'NUMERIC': 0, 'REAL': 0.0,
                            'INTEGER': 0}
        # used for ordering the values of output records
        self.fieldnames = []
        # list of ?'s used for insert queries, initialized when fields are set
        self.qmarks = ''
        # connection/cursor used for insert queries, closed by self.close()
        self.conn = None
        self.cur = None
        self.namelenlimit = None

    # converts fields to universal types
    def getfields(self):
        """Get the field definitions from an input file."""
        # connect to the database
        with sqlite3.connect(self.filename) as conn:
            cur = conn.cursor()
            # get the string that creates the table
            # ex: 'CREATE TABLE newtable (itemID INTEGER, itemName TEXT)'
            cur.execute("SELECT sql FROM sqlite_master WHERE tbl_name='" +
                        self.tablename + "' AND type='table'")
            tablestr = cur.fetchone()[0]
            # extract the field names and types (affinities)
            fields = re.findall('(\w+) (NULL|INTEGER|REAL|TEXT|BLOB)',
                                tablestr)
            # construct the list of fields
            fieldlist = []
            for curfield in fields:
                # store affinity in a dictionary, by the general name 'type'
                fieldattributes = OrderedDict()
                fieldattributes['type'] = str(curfield[1])
                # create the field and add it to the list
                newfield = field.Field(str(curfield[0]), fieldattributes,
                                       namelen=None, dataformat='sqlite')
                fieldlist.append(newfield)
            return fieldlist

    # takes universal-type fields and converts to format specific fields
    def setfields(self, newfields):
        """Set the field definitions of an output file."""
        # make a list of all the fieldnames with their types
        fieldlist = []
        for unknownfield in newfields:
            fieldlist.append(unknownfield.name + ' ' + unknownfield['type'])
            self.fieldnames.append(unknownfield.name)
        # combine them into one string
        # ex: 'itemID INTEGER, itemName TEXT'
        fieldstr = ', '.join(fieldlist)
        # connect to the database
        with sqlite3.connect(self.filename) as conn:
            cur = conn.cursor()
            # create the table
            # XXX what if the table exists
#            print 'tablename:', self.tablename
#            print 'fieldstr:', fieldstr
            try:
                cur.execute('CREATE TABLE ' + self.tablename +
                            '(' + fieldstr + ')')
            except sqlite3.OperationalError:
                raise table.TableExistsError
        # init the string of ?'s used for insertion queries
        qmarklist = []
        for _counter in range(len(newfields)):
            qmarklist.append('?')
        qmarks = ', '.join(qmarklist)
        self.insertquery = ('INSERT INTO ' + self.tablename +
                            ' VALUES (' + qmarks + ');')

    def addrecord(self, newrecord):
        """Write a record (stored as a dictionary) to the output file."""
        if self.cur is None:
            self.conn = sqlite3.connect(self.filename)
            self.cur = self.conn.cursor()
        else:
            values = [newrecord[fn] for fn in self.fieldnames]
            self.cur.execute(self.insertquery, values)

    def close(self):
        """Close the open file, if any."""
        if self.conn is not None:
            self.conn.commit()
            self.conn.close()

    def convertfield(self, unknownfield):
        """Take a field of unknown type, return a field of the format type."""
        sqlitefield = unknownfield.copy()
        if sqlitefield.hasformat('sqlite'):
            sqlitefield.setformat('sqlite')
        else:
            sqlattributes = OrderedDict()
            if sqlitefield.hasattribute('type'):
                sqlattributes['type'] = unknownfield['type']
            else:
                sqlattributes['type'] = 'TEXT'
            sqlitefield.setformat('sqlite', sqlattributes)
        sqlitefield.namelenlimit = None
        sqlitefield.resetname()
        return sqlitefield

    def getfieldtypes(self):
        """Return a list of field types to populate a combo box."""
        return self.blankvalues.keys()

    def getblankvalue(self, outputfield):
        """Return a blank value that matches the type of the field."""
        return self.blankvalues[outputfield['type']]

    def getrecordcount(self):
        """Return number of records, or None if it's too costly to count."""
        # connect to the database
        with sqlite3.connect(self.filename) as conn:
            cur = conn.cursor()
            # get the row count
            cur.execute("SELECT count(*) FROM " + self.tablename)
            return cur.fetchone()[0]

    def __iter__(self):
        """Get the records from an input file in sequence."""
        # connect to the database
        with sqlite3.connect(self.filename) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM " + self.tablename)
            for row in cur:
                yield row
