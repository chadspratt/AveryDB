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
# wrapper for xlrd and xlwt libraries
from collections import OrderedDict

from filetypes.libraries import xlrd
from filetypes.libraries import xlwt

import table
import field


# GenericFile is just an interface
class ExcelData(table.Table):
    """Wraps the dbfpy library with a set of standard functions."""
    def __init__(self, filename, tablename=None, mode='r'):
        super(ExcelData, self).__init__(filename, tablename=None)
        self.namelenlimit = 255  # not sure about this

        # XXX very incomplete
#        if mode == 'r':
#            self.filehandler = dbf.Dbf(filename, readOnly=True)
#        else:
#            self.filehandler = dbf.Dbf(filename, new=True)
#        self.fieldattrorder = ['Name', 'Type', 'Length', 'Decimals', 'Value']
#        # used to convert between dbf library and sqlite types
#        self.types = {'C': 'TEXT', 'N': 'NUMERIC', 'F': 'REAL',
#                      'T': 'TIME', 'L': 'LOGICAL', 'M': 'MEMOTEXT',
#                      'D': 'DATE', 'I': 'INTEGER', 'Y': 'CURRENCY',
#                      'TEXT': 'C', 'NUMERIC': 'N', 'REAL': 'F',
#                      'TIME': 'T', 'LOGICAL': 'L', 'MEMOTEXT': 'M',
#                      'DATE': 'D', 'INTEGER': 'I', 'CURRENCY': 'C'}

    def getfields(self):
        """Returns the fields of the file as a list of Field objects"""
        fieldlist = []
        for fielddef in self.filehandler.fieldDefs:
            # use ordereddict to enable accessing attributes by index
            fieldattrs = OrderedDict([('type', self.types[fielddef.typeCode]),
                                      ('length', fielddef.length),
                                      ('decimals', fielddef.decimalCount)])
            newfield = field.Field(fielddef.name, fieldattributes=fieldattrs,
                                   dataformat='dbf', namelen=None)
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
        self.filehandler.close()

    @classmethod
    def convertfield(cls, sourcefield):
        excelfield = sourcefield.copy()
        if 'xls' in excelfield.attributesbyformat:
            excelfield.attributes = excelfield.attributesbyformat['xls'].copy()
        else:
            excelfield.attributes = OrderedDict()
            if 'type' in sourcefield.attributes:
                excelfield['type'] = sourcefield['type']
            else:
                excelfield['type'] = 'TEXT'
            if 'length' in sourcefield.attributes:
                excelfield['length'] = sourcefield['length']
            else:
                excelfield['length'] = 254
            if 'decimals' in sourcefield.attributes:
                excelfield['decimals'] = sourcefield['decimals']
            else:
                excelfield['decimals'] = 0
        excelfield.namelenlimit = None
        excelfield.resetname()
        return excelfield

    @classmethod
    def getblankvalue(cls, outputfield):
        fieldtype = outputfield['type']
        if fieldtype == 'TEXT':
            return ''
        elif fieldtype == 'NUMERIC':
            return 0
        elif fieldtype == 'REAL':
            return 0.0
        # i don't know for this one what a good nonvalue would be
        elif fieldtype == 'DATE':
            return (0, 0, 0)
        elif fieldtype == 'INTEGER':
            return 0
        elif fieldtype == 'CURRENCY':
            return 0.0
        elif fieldtype == 'LOGICAL':
            return -1
        elif fieldtype == 'MEMOTEXT':
            return " " * 10
        elif fieldtype == 'TIME':
            return None

    def getrecordcount(self):
        return self.filehandler.recordCount

    def __iter__(self):
        recordcount = self.filehandler.recordCount
        i = 0
        while i < recordcount:
            yield self.filehandler[i]
            i += 1
