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
    def __init__(self, fieldname, fieldattributes=None, fieldvalue=''):
        if fieldattributes is None:
            fieldattributes = {}
        # used this for resetting a field
        self.originalname = fieldname
        self.originalvalue = fieldvalue
        # name and value that will be used in the output
        self.name = fieldname
        self.value = fieldvalue
        # dictionary of attribute names and values
        self.attributes = fieldattributes
        self.namegen = self.namegenerator()

    # it yields the new name, but it isn't used. Field.name is checked directly
    def namegenerator(self, lenlimit=10):
        """Yields alternate field names for when there's a naming conflict."""
        namelen = len(self.originalname)  # store original length
        # append a number to create a different name
        dupecount = 1
        countlen = 1
        namelen = lenlimit - countlen
        while True:
            # append next number to original alias
            self.name = self.originalname[:namelen] + str(dupecount)
            yield self.name
            dupecount += 1
            countlen = len(str(dupecount))
            namelen = lenlimit - countlen

    def createnewname(self):
        """Supplies a new unique name candidate."""
        self.namegen.next()

    def resetname(self):
        """Resets the field name, though it will be changed if it conflicts."""
        self.name = self.originalname
        self.namegen = self.namegenerator()

    # Not currently used
    def resetvalue(self):
        """Resets the value of a field to it's original value."""
        self.value = self.originalvalue

    def copy(self):
        """Creates a deep copy of the field."""
        fieldcopy = Field(self.name, self.attributes, self.value)
        fieldcopy.originalvalue = self.originalvalue
        return fieldcopy

    def getattributelist(self):
        """Returns all attributes (eg: name, type) of a field as a list."""
        attrlist = [self.name]
        attrlist.extend(self.attributes.values())
        attrlist.append(self.value)
        return attrlist

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
        elif key in self.attributes:
            self.attributes[key] = value
        else:
            attrname = self.attributes.keys()[key - 1]
            self.attributes[attrname] = value
