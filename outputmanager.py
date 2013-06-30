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
# handles the initialization and configuration of the output

import field
#from filetypes import dbffile


class OutputManager(object):
    """Manages all creation and organization of the output fields."""
    def __init__(self):
        # hard-coded for dbf for now
        self.outputfilename = ''
        self.outputtype = 'dbf'
        self.fieldtypes = ['C', 'N', 'F', 'I', 'Y', 'L', 'M', 'D', 'T']
        self.outputfields = {}  # Field objects stored by uppercase field name
        self.outputorder = []   # field names, stores the order of the fields
        self.fieldattr = ['Name', 'Type', 'Length', 'Decimals', 'Value']

    def clear(self):
        """Clears the output fields."""
        self.outputfields = {}
        self.outputorder = []

    # This function will need to update fieldtypes and fieldattr.
    # It should also convert any existing outputfields to the new format
    def setoutputtype(self, outputtype):
        """Sets the format of the output. Only dbf is supported right now."""
        self.outputtype = outputtype

    def getoutputtype(self):
        """Returns the output file format."""
        return self.outputtype

    # XXX could use better design
    def addfield(self, outputfield, filealias=None, fieldindex='end'):
        """Takes a field object and adds it to the output."""
        # filealias will be passed with fields that are taken from files
        # Make a copy of these fields to use for the output field.
        if filealias:
            newfield = outputfield.copy()
            newfield.value = '!' + filealias + '.' + newfield.name + '!'
        # If it is a new field, just use the one passed as an argument.
        else:
            newfield = outputfield

        # dbf is not case sensitive (won't allow 'objectID' and 'objectid')
        # outputfields uses uppercase names to help check for duplicates
        while newfield.name.upper() in self.outputfields:
            newfield.createnewname()

        self.outputfields[newfield.name.upper()] = newfield
        if fieldindex == 'end':
            self.outputorder.append(newfield.name)
        else:
            self.outputorder.insert(fieldindex, newfield.name)

        return newfield

    def addnewfield(self, fieldname='newfield', fieldattributes=None,
                    fieldvalue='', fieldindex='end'):
        """Takes field attributes and adds a field to the output."""
        if fieldattributes is None:
            fieldattributes = {'type': 'C', 'length': 254, 'decimals': 0}
        newfield = field.Field(fieldname, fieldattributes, fieldvalue)
        self.addfield(newfield, fieldindex=fieldindex)
        return newfield

    def removefield(self, fieldindex):
        """Removes the field at the specified index."""
        fieldname = self.outputorder[fieldindex]
        del self.outputfields[fieldname.upper()]
        self.outputorder.remove(fieldname)

    def movefield(self, fieldindex, newfieldindex):
        """Moves the field at position fieldindex to newfieldindex."""
        if newfieldindex == 'start':
            newfieldindex = 0
        elif newfieldindex == 'end':
            newfieldindex = len(self.outputorder)
        field = self.outputorder.pop(fieldindex)
        self.outputorder.insert(newfieldindex, field)

    def getindex(self, outputfield):
        """Returns the position of a field."""
        return self.outputorder.index(outputfield.name)

    def getuniquename(self, fieldname):
        """Supplies a unique version of a field name."""
        tempfield = field.Field(fieldname)
        while tempfield['name'].upper() in self.outputfields:
            tempfield.createnewname()
        return tempfield['name']

    def __getitem__(self, key):
        """Retrieve a Field object by index or by output name"""
        # Interpret all numbers as indices
        if isinstance(key, int) or key.isdigit():
            return self.outputfields[self.outputorder[int(key)].upper()]
        else:
            return self.outputfields[key.upper()]

    def __iter__(self):
        """Return all output fields in order"""
        for fieldname in self.outputorder:
            yield self.outputfields[fieldname.upper()]

    def __len__(self):
        return len(self.outputfields)

    def __contains__(self, fieldname):
        return fieldname.upper() in self.outputfields
