"""CSVFile is used to provide standard interfaces to the csv library."""
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
import csv
import re

import datafile
import field

FILETYPEEXT = '.csv'
FILETYPEDESCRIP = 'csv file'


# GenericFile is just an interface
class CSVFile(datafile.DataFile):
    """Wraps the csv library with a set of standard functions."""
    def __init__(self, filename, mode='r'):
        datafile.DataFile.__init__(self, filename)
        self.outputfile = None
        self.writer = None
        if mode == 'r':
            self.dialect = self._getdialect()
        else:
            self.dialect = None
        self.fieldattrorder = ['Name', 'Value']

    def _getdialect(self):
        """Get the dialect of the csv file."""
        with open(self.filename, 'r') as inputfile:
            return csv.Sniffer().sniff(inputfile.read(1024), '\b\t,')

    def getfields(self):
        """Get the fields from the csv file as a list of Field objects"""
        with open(self.filename, 'r') as inputfile:
            reader = csv.DictReader(inputfile, dialect=self.dialect)
            fieldnames = reader.fieldnames
            fieldtype = {}
            for fieldname in fieldnames:
                fieldtype[fieldname] = None
            # check 20 records
            for _counter in range(20):
                record = reader.next()
                for fieldname in fieldnames:
                    currenttype = fieldtype[fieldname]
                    # On each pass, fields can hold or step down in type,
                    # from integer, to real, and finally text.
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
                newfield = field.Field(fieldname, attributes, namelen=None)
                fieldlist.append(newfield)
            return fieldlist

    def setfields(self, newfields):
        """Add a field to the csv file. Used before any records are added."""
        fieldnames = [newfield.name for newfield in newfields]
        self.outputfile = open(self.filename, 'w')
        self.outputfile.truncate(0)
        self.writer = csv.DictWriter(self.outputfile, fieldnames)
        self.writer.writeheader()

    def addrecord(self, newrecord):
        """Append a new record to the csv file."""
        self.writer.writerow(newrecord)

    def close(self):
        """Close the csv file."""
        if self.outputfile:
            self.outputfile.close()

    @classmethod
    def convertfield(cls, unknownfield):
        """Convert a field of unknown type to a csv field."""
        csvfield = unknownfield.copy()
        # strip the attributes
        csvfield.attributes = {}
        return csvfield

    @classmethod
    def getblankvalue(cls, _outputfield):
        """Return an empty string as the blank value for any field."""
        return ''

    @classmethod
    def getrecordcount(cls):
        """Getting the record count for csv files isn't worthwhile."""
        return None

    # iterate through all the records
    def __iter__(self):
        with open(self.filename, 'r') as inputfile:
            reader = csv.DictReader(inputfile, dialect=self.dialect)
            for row in reader:
                yield row
