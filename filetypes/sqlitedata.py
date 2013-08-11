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
        # connect to the database
        conn = sqlite3.connect(filename)
        cur = conn.cursor()
        if tablename is None:
            # get a list of the tables
            cur.execute("SELECT name FROM sqlite_master" +
                        "WHERE type='table' ORDER BY name")
            tablenames = [result[0] for result in cur.fetchall()]
            return tablenames

        self.fieldattrorder = ['Name', 'Affinity']

        # ask the user which tables they want to

        # XXX very incomplete
        # filehandler would be
        self.filehandler = open(filename, mode)
        # suggested method for defining blank values for field types
        self.blankvalues = {'TEXT': '', 'NUMERIC': 0, 'REAL': 0.0, 'INT': 0}

    # converts fields to universal types
    def getfields(self):
        """Get the field definitions from an input file."""
        fieldlist = []
        fieldattributes = OrderedDict
        fieldlist.append(field.Field('newfield', fieldattributes,
                                     dataformat='example'))
        return fieldlist

    # takes universal-type fields and converts to format specific fields
    def setfields(self, newfields):
        """Set the field definitions of an output file."""
        for unknownfield in newfields:
            # "addfield" is a hypothetical function of the format library
            # save the field however you need to
            self.filehandler.addfield(self.convertfield(unknownfield))

    def addrecord(self, newrecord):
        """Write a record (stored as a dictionary) to the output file."""
        for fieldname in newrecord:
            fieldvalue = newrecord[fieldname]
            # store fieldvalue somehow

    def close(self):
        """Close the open file, if any."""
        self.filehandler.close()

    def convertfield(self, unknownfield):
        """Take a field of unknown type, return a field of the format type."""
        examplefield = unknownfield.copy()
        if examplefield.hasformat('example'):
            examplefield.setformat('example')
        else:
            exampleattributes = OrderedDict()
            if unknownfield.hasattribute('attr0'):
                exampleattributes['attr0'] = unknownfield['attr0']
            else:
                exampleattributes['attr0'] = 'attr0_defaultval'
            examplefield.setformat('example', exampleattributes)
        return examplefield

    def detecttype(self, valuelist):
        """Examine a list of values and determine an appropriate field type."""
        fieldtype = None
        for value in valuelist:
            if (fieldtype in ['INTEGER', None] and
                    re.search('^[0-9]+$', value)):
                fieldtype = 'INTEGER'
            elif (fieldtype in ['REAL', 'INTEGER', 'NONE'] and
                  re.search('^[.0-9]+$', value)):
                fieldtype = 'REAL'
            else:
                fieldtype = 'TEXT'
        return fieldtype

    def getblankvalue(self, outputfield):
        """Return a blank value that matches the type of the field."""
        return self.blankvalues[outputfield['type']]

    def getrecordcount(self):
        """Return number of records, or None if it's too costly to count."""
        # hypothetical
        return self.filehandler.getrecordcount()

    def __iter__(self):
        """Get the records from an input file in sequence."""
        # hypothetical
        for record in self.filehandler:
            yield record
