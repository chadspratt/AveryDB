"""Field stores all information about a given field.

The field object is used to represent fields from any data format and assists
with converting fields between the inputs and the output."""
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


class Field(object):
    """Stores a field definition."""
    def __init__(self, fieldname, fieldattributes=None, fieldvalue='',
                 source=None, dataformat=None, namelen=10):
        if fieldattributes is None:
            fieldattributes = {}
        # used for resetting a field
        self.originalname = fieldname
        if dataformat is not None:
        # preserves field attributes if output format is changed, changed back
            self.attributesbyformat = {dataformat: fieldattributes.copy()}
        else:
            self.attributesbyformat = {}
        self.originalvalue = fieldvalue
        # name and value that will be used in the output
        self.name = fieldname[:namelen]
        self.source = source
        self.value = fieldvalue
        # dictionary of attribute names and values, stored by file format
        self.attributes = fieldattributes
        self.namelenlimit = namelen
        self.namegen = self.namegenerator(namelen)
        # tablename_fieldname used for storage in sqlite
        # assigned by table during conversion of the data to sqlite
        self.sqlname = None

    def namegenerator(self, lenlimit):
        """Yields alternate field names for when there's a naming conflict."""
        # append a number to create a different name
        dupecount = 1
        if lenlimit is None:
            while True:
                yield self.originalname + str(dupecount)
                dupecount += 1
        # append a number and trim the name as needed to meet the limit
        else:
            namelen = len(self.originalname)  # store original length
            countlen = 1
            namelen = lenlimit - countlen
            while True:
                # append next number to original alias
                yield self.originalname[:namelen] + str(dupecount)
                dupecount += 1
                countlen = len(str(dupecount))
                namelen = lenlimit - countlen

    def getnewname(self):
        """Supplies a new unique name candidate."""
        return self.namegen.next()

    def resetname(self):
        """Resets the field name, though it will be changed if it conflicts."""
        # trim name in case length limit has changed
        self.name = self.name[:self.namelenlimit]
        # reset the name generator
        self.namegen = self.namegenerator(self.namelenlimit)

    # Not currently used
    def resetvalue(self):
        """Resets the value of a field to it's original value."""
        self.value = self.originalvalue

    def copy(self):
        """Creates a deep copy of the field."""
        fieldcopy = Field(self.name, self.attributes, self.value)
        for dataformat in self.attributesbyformat:
            fieldcopy.attributesbyformat[dataformat] = (
                self.attributesbyformat[dataformat].copy())
        fieldcopy.originalname = self.originalname
        fieldcopy.originalvalue = self.originalvalue
        fieldcopy.source = self.source
        return fieldcopy

    def hasattribute(self, attributename):
        """Check if the field has an attribute by the given name."""
        return attributename in self.attributes

    def getattribute(self, attributename):
        """Get an attribute value by name (case-insensitive)."""
        for key in self.attributes:
            if attributename.lower() == key.lower():
                return self.attributes[key]
        # If the field doesn't have the attribute, return None.
        # possible ambiguity if an attribute had the value of None
        return None

    def getattributes(self):
        """Returns all attributes (eg: name, type) of a field as a list."""
        attrlist = [self.name]
        attrlist.extend(self.attributes.values())
        attrlist.append(self.value)
        return attrlist

    def setformat(self, dataformat, newattributes=None):
        """Set new attributes for the field when the format is changed."""
        # Check if the attributes have already been defined for dataformat
        if dataformat in self.attributesbyformat:
            self.attributes = self.attributesbyformat[dataformat]
        else:
            # If the format isn't already defined, attributes are required
            if newattributes is None:
                raise ValueError('Field.setformat: ' + dataformat + ' not ' +
                                 'defined, need attribute dictionary')
            self.attributes = newattributes
            self.attributesbyformat[dataformat] = newattributes

    def hasformat(self, dataformat):
        """Check if a format is defined for this field."""
        return dataformat in self.attributesbyformat

    def __getitem__(self, key):
        if key == 'name' or key == 0:
            return self.name
        elif key == 'value' or key == len(self.attributes) + 1:
            return self.value
        elif key in self.attributes:
            return self.attributes[key]
        return self.attributes.values()[key - 1]

    def __setitem__(self, key, value):
        if key == 'name' or key == 0:
            self.name = value
        elif key == 'value' or key == len(self.attributes) + 1:
            self.value = value
        # set attribute by index
        elif type(key) == int or key.isdigit():
            attrname = self.attributes.keys()[key - 1]
            self.attributes[attrname] = value
        # set attribute by name
        else:
            self.attributes[key] = value

    def __str__(self):
        return ('name: ' + self.name + '\nattr: ' + str(self.attributes) +
                '\nvalue: ' + self.value)
