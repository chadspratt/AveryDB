# -*- coding: utf-8 -*-
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
    def __init__(self, fieldname, fieldattributes={}, fieldvalue=''):
        # used this for resetting a field
        self.originalname = fieldname
        self.originalvalue = fieldvalue
        # name and value that will be used in the output
        self.name = fieldname
        self.value = fieldvalue
        # dictionary of attribute names and values
        self.attributes = fieldattributes
        self.namegen = self.namegenerator()
        
    # it yields the new name, but I'm not using that and just checking the variable directly
    def namegenerator(self, lenlimit=10):
        """Generate an alternate filename to deal with duplicates when initiating the output."""
        namelen = len(self.originalname) #store original length
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
        self.namegen.next()
            
    def resetname(self):
        self.name = self.originalname
        self.namegen = self.namegenerator()
        
    def resetvalue(self):
        self.value = self.originalvalue
            
    def copy(self):
        fieldCopy = Field(self.name, self.attributes, self.value)
        fieldCopy.originalvalue = self.originalvalue
        return fieldCopy
        
    def getattributelist(self):
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
        return self.attributes.values()[key-1]
        
    def __setitem__(self, key, value):
        if key == 'name' or key == 0:
            self.name = value
        elif key == 'value' or key == len(self.attributes) + 1:
            self.value = value
        elif key in self.attributes:
            self.attributes[key] = value
        else:
            attrname = self.attributes.keys()[key-1]
            self.attributes[attrname] = value
        