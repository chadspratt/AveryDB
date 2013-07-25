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
# wrapper for dbfpy utility
from collections import OrderedDict

from filetypes.libraries.dbfpy import dbf

import genericfile
import field

FILETYPEEXT = '.dbf'
FILETYPEDESCRIP = 'dbase file'


# GenericFile is just an interface
class DBFFile(genericfile.GenericFile):
    """Wraps the dbfpy library with a set of standard functions."""
    def __init__(self, filename, mode='r'):
        self.filename = filename
        if mode == 'r':
            self.filehandler = dbf.Dbf(filename, readOnly=True)
        else:
            self.filehandler = dbf.Dbf(filename, new=True)
        # not used from here, but I'd like for it to be
        self.fieldtypes = ['C', 'N', 'F', 'I', 'Y', 'L', 'M', 'D', 'T']
        self.fieldattrorder = ['type', 'length', 'decimals']

    def getfields(self):
        """Returns the fields of the file as a list of Field objects"""
        fieldlist = []
        for fielddef in self.filehandler.fieldDefs:
            # use ordereddict to enable accessing attributes by index
            fieldattrs = OrderedDict([('type', fielddef.typeCode),
                                      ('length', fielddef.length),
                                      ('decimals', fielddef.decimalCount)])
            newfield = field.Field(fielddef.name, fieldattributes=fieldattrs)
            fieldlist.append(newfield)
        return fieldlist

    def addfield(self, newfield):
        """Add a field to an output file. Used before any records are added."""
        self.filehandler.addField((newfield['name'], newfield['type'],
                                   newfield['length'], newfield['decimals']))

    def getrecordcount(self):
        """Returns the number of records in the file."""
        return self.filehandler.recordCount

    def addrecord(self, newrecord):
        """Append a new record to an output dbf file."""
        rec = self.filehandler.newRecord()
        for fieldname in newrecord:
            rec[fieldname] = newrecord[fieldname]
        rec.store()

    def close(self):
        self.filehandler.close()

    # returns record at given index as a dictionary of field name:value
#    def __getitem__(self, index):
#        return self.filehandler[index].asDict()

    def __iter__(self):
        recordcount = self.getrecordcount()
        i = 0
        while i < recordcount:
            yield self.filehandler[i]
            i += 1
