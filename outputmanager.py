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


class OutputManager(object):
    """Manages all creation and organization of the output fields."""
    def __init__(self):
        self.outputfile = None
        self.outputfields = {}  # Field objects stored by uppercase field name
        self.outputorder = []   # field names, stores the order of the fields

    def clear(self):
        """Clears the output fields."""
        self.outputfields = {}
        self.outputorder = []

    # When output format is changed a file handler for that type is passed so
    # that fields can be converted.
    def setoutputfile(self, filehandler):
        """Update the output file with one of [possibly] a new format."""
        if self.outputfile is not None:
            self.outputfile.close()
        self.outputfile = filehandler
        for fieldname in self.outputfields:
            newfield = filehandler.convertfield(self.outputfields[fieldname])
            self.outputfields[fieldname] = newfield

    def getoutputtype(self):
        """Returns the output file format."""
        return self.outputtype

    def addfield(self, newfield, fieldindex='end', fieldsource=None,):
        """Takes a field object and adds it to the output."""
        outputfield = self.outputfile.convertfield(newfield)
        outputfield.source = fieldsource

        # Check uppercase name to prevent case-insensitive duplicates
        # outputfields uses uppercase names to help check for duplicates
        fieldname = outputfield.name
        while fieldname.upper() in self.outputfields:
            fieldname = outputfield.getnewname()
        outputfield.name = fieldname

        self.outputfields[outputfield.name.upper()] = outputfield
        if fieldindex == 'end':
            self.outputorder.append(outputfield.name)
        else:
            self.outputorder.insert(fieldindex, outputfield.name)

        return outputfield

    def addnewfield(self, fieldname='newfield', fieldattributes=None,
                    fieldvalue='', fieldindex='end'):
        """Takes field attributes and adds a field to the output."""
        newfield = field.Field(fieldname, fieldattributes, fieldvalue)
        return self.addfield(newfield, fieldindex=fieldindex)

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
        """Supplies a unique variation on a field name."""
        tempfield = field.Field(fieldname,
                                namelen=self.outputfile.namelenlimit)
        uniquename = tempfield.name
        while uniquename.upper() in self.outputfields:
            uniquename = tempfield.getnewname()
        return uniquename

    def updatename(self, fieldpos, newname):
        # Check that the name was changed
        fieldindex = int(fieldpos)
        oldname = self.outputorder[fieldindex]
        if self.outputfile.namelenlimit is not None:
            # trim front or back?
            newname = newname[:self.outputfile.namelenlimit]
        if oldname.upper() != newname.upper():
            # Check if the name is already in use.
            if newname.upper() in self.outputfields:
                newname = self.getuniquename(newname)
            # Apply the updated name
            self.outputorder[fieldindex] = newname
            self.outputfields[newname.upper()] = (
                self.outputfields[oldname.upper()])
            del self.outputfields[oldname.upper()]
        # case of some letters may have changed
        else:
            self.outputorder[fieldindex] = newname
        return newname

    def __getitem__(self, key):
        """Retrieve a Field object by index or by output name"""
        # Interpret all numbers as indices
        if isinstance(key, int) or key.isdigit():
            return self.outputfields[self.outputorder[int(key)].upper()]
        else:
            return self.outputfields[key.upper()]

    # def __setitem__(self, key, value):
    #     """Set a field or a property of a field

    def __iter__(self):
        """Return all output fields in order"""
        for fieldname in self.outputorder:
            yield self.outputfields[fieldname.upper()]

    def __len__(self):
        return len(self.outputfields)

    def __contains__(self, fieldname):
        return fieldname.upper() in self.outputfields
