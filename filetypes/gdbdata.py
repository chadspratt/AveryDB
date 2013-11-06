"""GDBData is used to provide a standardized interface to file geodatabases."""
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
import os.path

import arcpy

import table
import field


class GDBData(table.Table):
    """Handle all input and output for file geodatabases."""
    def __init__(self, filename, tablename=None, mode='r'):
        super(GDBData, self).__init__(filename, tablename)
        print 'filename:', filename
        # If no table name was passed
        if self.tablename is None:
            if mode == 'r':
                tablenames = {}
                # open the geodatabase
                arcpy.env.workspace = filename
                # get features in root of gdb
                rootfeatures = arcpy.ListFeatureClasses('*')
                if len(rootfeatures) > 0:
                    tablenames['features'] = rootfeatures
                roottables = arcpy.ListTables('*')
                if len(roottables) > 0:
                    tablenames['tables'] = roottables
                datasets = arcpy.ListDatasets('*', 'Feature')
                if len(datasets) > 0:
                    tablenames['datasets'] = {}
                    for dataset in datasets:
                        datasetfeatures = arcpy.ListFeatureClasses('*', '', dataset)
                        if len(datasetfeatures) > 0:
                            tablenames['datasets'][dataset] = datasetfeatures
                # and return the list in an exception
                raise table.NeedTableError(tablenames)
            elif mode == 'w':
                raise table.NeedTableError(None)

        self.fieldattrorder = ['Name', 'Type', 'Alias', 'Domain', 'Editable',
                               'Nullable', 'Required', 'Length', 'Scale',
                               'Precision', 'Value']
        self.blankvalues = OrderedDict([('SMALLINT', 0), ('INTEGER', 0),
                                        ('SINGLE', 0.0), ('DOUBLE', 0),
                                        ('TEXT', ''), ('DATE', 0), 
                                        ('NUMERIC', 0), ('REAL', 0.0)])

        # format specific output stuff
        # used for ordering the values of output records
        self.fieldnames = []
        self.fulltablepath = os.path.join(self.filename, self.tablename)
        # connection/cursor used for insert queries, closed by self.close()
        self.conn = None
        self.cur = None
        self.namelenlimit = None

    # converts fields to universal types
    def getfields(self):
        """Get the field definitions from an input file."""
        fields = arcpy.ListFields(self.fulltablepath)
        fieldlist = []
        for curfield in fields:
            fieldattributes = OrderedDict()
            fieldattributes['alias'] = curfield.aliasName
            fieldattributes['type'] = curfield.type
            fieldattributes['domain'] = curfield.domain
            fieldattributes['editable'] = curfield.editable
            fieldattributes['nullable'] = curfield.isNullable
            fieldattributes['required'] = curfield.required
            fieldattributes['length'] = curfield.length
            fieldattributes['scale'] = curfield.scale
            fieldattributes['precision'] = curfield.precision
            newfield = field.Field(curfield.name, fieldattributes,
                                   namelen=64, dataformat='gdb')
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

    @classmethod
    def convertfield(cls, sourcefield):
        """Convert a field to sqlite format."""
        sqlitefield = sourcefield.copy()
        if sqlitefield.hasformat('sqlite'):
            sqlitefield.setformat('sqlite')
        else:
            sqlattributes = OrderedDict()
            if sqlitefield.hasattribute('type'):
                sqlattributes['type'] = sourcefield['type']
            else:
                sqlattributes['type'] = 'TEXT'
            sqlitefield.setformat('sqlite', sqlattributes)
        sqlitefield.namelenlimit = None
        sqlitefield.resetname()
        return sqlitefield

    def getfieldtypes(self):
        """return a list of field types to populate a combo box."""
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

    def backup(self):
        """Rename the table to tablename_old within the db"""
        backupcount = 1
        backupname = self.tablename + '_old'
        backupnamelen = len(backupname)
        with sqlite3.connect(self.filename) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            # get a list of the tables
            cur.execute("SELECT name FROM sqlite_master " +
                        "WHERE type='table' ORDER BY name")
            tablenames = [result[0] for result in cur.fetchall()]
            # don't overwrite existing backups, if any
            while backupname in tablenames:
                backupname = backupname[:backupnamelen] + str(backupcount)
                backupcount += 1
            cur.execute("ALTER TABLE " + self.tablename +
                        " RENAME TO " + backupname)
            conn.commit()

    def __iter__(self):
        """Get the records from an input file in sequence."""
        # connect to the database
        with sqlite3.connect(self.filename) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM " + self.tablename)
            for row in cur:
                yield row
