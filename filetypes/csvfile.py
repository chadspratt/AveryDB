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
import csv
import re

import field

FILETYPEEXT = '.csv'
FILETYPEDESCRIP = 'csv file'


# GenericFile is just an interface
class CSVFile(object):
    """Wraps the dbfpy library with a set of standard functions."""
    def __init__(self, filename, mode='r'):
        self.filename = filename
        self.outputfile = None
        self.writer = None
        if mode == 'r':
            self.dialect = self._getdialect()
        else:
            self.dialect = None
        self.fieldattrorder = ['Name', 'Value']

    def _getdialect(self):
        with open(self.filename, 'r') as inputfile:
            return csv.Sniffer().sniff(inputfile.read(1024), '\b\t,')

    def getfields(self):
        """Returns the fields of the file as a list of Field objects"""
        with open(self.filename, 'r') as inputfile:
            reader = csv.DictReader(inputfile, dialect=self.dialect)
            fieldnames = reader.fieldnames
            fieldtype = {}
            for fieldname in fieldnames:
                fieldtype[fieldname] = None
            for i in range(20):
                record = reader.next()
                for fieldname in fieldnames:
                    currenttype = fieldtype[fieldname]
                    if (currenttype in ['INTEGER', None] and
                            re.search('^[0-9]+$', record[fieldname])):
                        fieldtype[fieldname] = 'INTEGER'
                    elif (currenttype in ['REAL', 'INTEGER', 'NONE'] and
                          re.search('^[.0-9]+$', record[fieldname])):
                        fieldtype[fieldname] = 'REAL'
                    else:
                        fieldtype[fieldname] = 'TEXT'
            fieldlist = []
            for fieldname in fieldnames:
                attributes = {'type': fieldtype[fieldname]}
                newfield = field.Field(fieldname, attributes)
                fieldlist.append(newfield)
            return fieldlist

    def setfields(self, newfields):
        """Add a field to an output file. Used before any records are added."""
        fieldnames = [field.name for field in newfields]
        self.outputfile = open(self.filename, 'w')
        self.outputfile.truncate(0)
        self.writer = csv.DictWriter(self.outputfile, fieldnames)
        self.writer.writeheader()

    def addrecord(self, newrecord):
        """Append a new record to an output dbf file."""
        self.writer.writerow(newrecord)

    def close(self):
        if self.outputfile:
            self.outputfile.close()

    @classmethod
    def convertfield(cls, sourcefield):
        csvfield = sourcefield.copy()
        csvfield.attributes = {}
        return csvfield

    @classmethod
    def getblankvalue(cls, _outputfield):
        return ''

    @classmethod
    def getrecordcount(cls):
        return None

    # iterate through all the records
    def __iter__(self):
        with open(self.filename, 'r') as inputfile:
            reader = csv.DictReader(inputfile, dialect=self.dialect)
            for row in reader:
                yield row
