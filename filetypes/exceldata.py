"""ExcelData is used to provide a standardized interface to excel files."""
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
import os
from datetime import datetime
from datetime import time


from filetypes.libraries import xlrd
from filetypes.libraries import xlwt

import table
import field


# GenericFile is just an interface
class ExcelData(table.Table):
    """Wraps the x library with a set of standard functions."""
    def __init__(self, filename, tablename=None, mode='r', fieldtypes=None):
        super(ExcelData, self).__init__(filename, tablename)

        # If no table name was passed
        if tablename is None:
            # open the workbook
            if mode == 'r':
                with xlrd.open_workbook(filename) as book:
                    tablenames = book.sheet_names()
                    # and return the list of sheet names in an exception
                    raise table.NeedTableError(tablenames)
            else:
                raise table.NeedTableError([])

        # check that the data opens
        if mode == 'r':
            with xlrd.open_workbook(self.filename, on_demand=True) as book:
                if fieldtypes is None:
                    sheet = book.sheet_by_name(self.tablename)
                    fieldnames = sheet.row_values(0)
                    fieldvalues = []
                    for i in range(1, 10):
                        try:
                            fieldvalues.append(sheet.row_values(i))
                        # fewer than 9 records in the file
                        except IndexError:
                            break
                    fieldtypes = ['Text', 'Numeric', 'Date', 'Logical']
                    raise table.AmbiguousFieldTypesError(fieldnames,
                                                         fieldvalues,
                                                         fieldtypes)

        self.fieldattrorder = ['Name', 'Value']
        self.types = {0: 'EMPTY', 1: 'TEXT', 2: 'NUMERIC', 3: 'DATE',
                      4: 'LOGICAL', 5: 'ERROR', 6: 'BLANK',
                      'EMPTY': 0, 'TEXT': 1, 'NUMERIC': 2, 'DATE': 3,
                      'LOGICAL': 4, 'ERROR': 5, 'BLANK': 6}
        self.blankvalues = OrderedDict([('TEXT', ''), ('NUMERIC', 0),
                                        ('DATE', (0, 0, 0)), ('LOGICAL', -1)])
        self.namelenlimit = 255 # for Excel 2003

        self.book = None
        self.fieldtypes = fieldtypes

    def getfields(self):
        """Get the fields from the csv file as a list of Field objects"""
        with xlrd.open_workbook(self.filename, on_demand=True) as book:
            # print 'self.tablename:', self.tablename
            sheet = book.sheet_by_name(self.tablename)
            # get column names from first row, hope they're unique
            fieldnames = sheet.row_values(0)

            # fieldcandidates = {}
            fieldlist = []
            for fieldindex in xrange(len(fieldnames)):
                fieldname = fieldnames[fieldindex]
                attributes = {'type': self.fieldtypes[fieldindex].upper()}
                newfield = field.Field(fieldname, attributes, namelen=self.namelenlimit)
                fieldlist.append(newfield)
            return fieldlist

    def setfields(self, fields):
        """Set the field definitions. Used before any records are added."""
        self.book = xlwt.Workbook()
        self.sheet = self.book.add_sheet(self.tablename)
        for i in xrange(len(fields)):
            fieldname = fields[i]['name']
            # store field name for use in addrecord()
            self.fields[fieldname] = None
            self.sheet.row(0).write(i, fieldname)
        self.currow = 1

    def addrecord(self, newrecord):
        """Append a new record to an output dbf file."""
        curcol = 0
        for fieldname in self.fields:
            self.sheet.write(self.currow, curcol, newrecord[fieldname])
            curcol += 1
        self.currow += 1

    def close(self):
        """Close output file, if this was an output file"""
        if self.book is not None:
            self.book.save(self.filename)

    def convertfield(self, sourcefield):
        """Convert a field to excel format."""
        excelfield = sourcefield.copy()
        # strip the attributes
        excelfield.attributes = {}
        excelfield.namelenlimit = self.namelenlimit
        excelfield.resetname()
        return excelfield

    def getfieldtypes(self):
        """Return a list of field types to populate a combo box."""
        return self.blankvalues.keys()

    @classmethod
    def getblankvalue(cls, outputfield):
        """Get a blank value that matches the type of a field."""
        return ''

    def getrecordcount(self):
        with xlrd.open_workbook(self.filename, on_demand=True) as book:
            sheet = book.sheet_by_name(self.tablename)
            return sheet.nrows

    def backup(self):
        """Rename the Excel file to filename.xls.old (or xlsx)"""
        backupcount = 1
        backupname = self.filename + '.old'
        backupnamelen = len(backupname)
        # don't overwrite existing backups, if any
        while os.path.isfile(backupname):
            backupname = backupname[:backupnamelen] + str(backupcount)
            backupcount += 1
        os.rename(self.filename, backupname)

    def __iter__(self):
        with xlrd.open_workbook(self.filename, on_demand=True) as book:
            sheet = book.sheet_by_name(self.tablename)
            # get column names from first row, hope they're unique
            colnames = sheet.row_values(0)
            # get values for a "record"
            for i in xrange(1, sheet.nrows):
                rowvalues = sheet.row_values(i)
                # convert dates to a date tuple, then to a str
                for fieldindex in range(len(rowvalues)):
                    if self.fieldtypes[fieldindex] == 'Date':
                        fieldval = rowvalues[fieldindex]
                        try:
                            fieldval = xlrd.xldate_as_tuple(rowvalues[fieldindex],
                                                            book.datemode)
                        except xlrd.xldate.XLDateAmbiguous:
                            pass
                        try:
                            rowvalues[fieldindex] = str(datetime(*fieldval))
                        except ValueError:
                            rowvalues[fieldindex] = str(time(*fieldval[3:]))
                    elif self.fieldtypes[fieldindex] == 'Logical':
                        rowvalues[fieldindex] = rowvalues[fieldindex] == 1
                # create a dictionary of the column names and values
                yield dict(zip(colnames, rowvalues))
