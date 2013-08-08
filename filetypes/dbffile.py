"""DBFFile is used to provide standard interfaces to the dbfpy library."""
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

from filetypes.libraries.dbfpy import dbf
import datafile
import field

FILETYPEEXT = '.dbf'
FILETYPEDESCRIP = 'dbase file'


# GenericFile is just an interface
class DBFFile(datafile.DataFile):
    """Wraps the dbfpy library with a set of standard functions."""
    def __init__(self, filename, mode='r'):
        datafile.DataFile.__init__(self, filename)
        if mode == 'r':
            self.filehandler = dbf.Dbf(filename, readOnly=True)
        else:
            self.filehandler = dbf.Dbf(filename, new=True)
        self.fieldattrorder = ['Name', 'Type', 'Length', 'Decimals', 'Value']
        # used to convert between dbf library and sqlite types
        self.types = {'C': 'TEXT', 'N': 'NUMERIC', 'F': 'REAL',
                      'T': 'TIME', 'L': 'LOGICAL', 'M': 'MEMOTEXT',
                      'D': 'DATE', 'I': 'INTEGER', 'Y': 'CURRENCY',
                      'TEXT': 'C', 'NUMERIC': 'N', 'REAL': 'F',
                      'TIME': 'T', 'LOGICAL': 'L', 'MEMOTEXT': 'M',
                      'DATE': 'D', 'INTEGER': 'I', 'CURRENCY': 'C'}
        self.blankvalues = {'TEXT': '', 'NUMERIC': 0, 'REAL': 0.0,
                            'TIME': None, 'LOGICAL': -1, 'MEMOTEXT': '     ',
                            'DATE': (0, 0, 0), 'INTEGER': 0, 'CURRENCY': 0.0}

    def getfields(self):
        """Returns the fields of the file as a list of Field objects"""
        fieldlist = []
        for fielddef in self.filehandler.fieldDefs:
            # use ordereddict to enable accessing attributes by index
            fieldattrs = OrderedDict([('type', self.types[fielddef.typeCode]),
                                      ('length', fielddef.length),
                                      ('decimals', fielddef.decimalCount)])
            newfield = field.Field(fielddef.name, fieldattributes=fieldattrs,
                                   dataformat='dbf')
            fieldlist.append(newfield)
        return fieldlist

    def setfields(self, fields):
        """Set the field definitions. Used before any records are added."""
        for genericfield in fields:
            dbffield = self.convertfield(genericfield)
            self.filehandler.addField((dbffield['name'],
                                       self.types[dbffield['type']],
                                       dbffield['length'],
                                       dbffield['decimals']))

    def addrecord(self, newrecord):
        """Append a new record to an output dbf file."""
        rec = self.filehandler.newRecord()
        for fieldname in newrecord:
            rec[fieldname] = newrecord[fieldname]
        rec.store()

    def close(self):
        """Close the dbf file handler."""
        self.filehandler.close()

    @classmethod
    def convertfield(cls, unknownfield):
        """Convert a field of unknown type to a dbf field."""
        dbffield = unknownfield.copy()
        if dbffield.hasformat('dbf'):
            dbffield.setformat('dbf')
        else:
            dbfattributes = OrderedDict()
            if unknownfield.hasattribute('type'):
                dbfattributes['type'] = unknownfield['type']
            else:
                dbfattributes['type'] = 'TEXT'
            if unknownfield.hasattribute('length'):
                dbfattributes['length'] = unknownfield['length']
            else:
                dbfattributes['length'] = 254
            if unknownfield.hasattribute('decimals'):
                dbfattributes['decimals'] = unknownfield['decimals']
            else:
                dbfattributes['decimals'] = 0
            dbffield.setformat('dbf', dbfattributes)
        return dbffield

    def getblankvalue(self, outputfield):
        """Get a blank value that matches the type of a field."""
        return self.blankvalues[outputfield['type']]

    def getrecordcount(self):
        """Return the number of records in the file."""
        return self.filehandler.recordCount

    def __iter__(self):
        """Iterate through all the records in the file."""
        recordcount = self.filehandler.recordCount
        i = 0
        while i < recordcount:
            yield self.filehandler[i]
            i += 1
