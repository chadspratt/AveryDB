"""ExampleFile contains the methods every format needs to implement.

The functions in this class must all be defined by a data format class.
The bodies of the functions are examples meant to show the format of values
that get passed, values that get returned, and suggestions on how to implement
each function.

The only required attributes is
    self.fieldattrorder = ['Name', 'Type', 'Length', 'Decimals', 'Value'].
    Extra functions can be defined as needed."""
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

# if a format has extra attributes for fields (beyond a field name), they
# need to be stored in an OrderedDict, so that the order will be consistent
from collections import OrderedDict
import re

import table
# Every format needs to create Field objects in getfields()
import field


class ExampleData(table.Table):
    """Handle all input and output for "example" files (not a real format)."""
    def __init__(self, filename, tablename=None, mode='r'):
        # must call this, which handles the filename/alias and sql table
        super(ExampleData, self).__init__(filename, tablename=None)
        ##
        # This attribute is required. It is only used to give the column names
        # for the output field list in the gui, so the names don't need to
        # match any internally used name. Name should be first, Value, last,
        # and in between should be the field attributes in the order that
        # getfields() puts them in
        ##
        self.fieldattrorder = ['Name', 'Type', 'Length', 'Decimals', 'Value']

        # filehandler would be opened using a library for that format
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
