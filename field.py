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
    # there's something off about using the same fields for input and output
    def __init__(self, fieldname, fieldtype, fieldlen, fielddec):
        # permanent references to the field source
        self.name = fieldname
        self.outputname = fieldname
        # for input fields, this will be "!filealias.fieldname!"
        self.value = fieldname
        self.type = fieldtype
        self.len = fieldlen
        self.dec = fielddec
        self.namegen = self.namegenerator()
        
    # it yields the new name, but I'm not using that and just checking the variable directly
    def namegenerator(self, lenlimit=10):
        """Generate an alternate filename to deal with duplicates when initiating the output."""
        namelen = len(self.name) #store original length
        # append a number to create a different name
        dupecount = 1
        countlen = 1
        namelen = lenlimit - countlen
        while True:
            # append next number to original alias
            self.outputname = self.name[:namelen] + str(dupecount)
            yield self.outputname
            dupecount += 1
            countlen = len(str(dupecount))
            namelen = lenlimit - countlen
            
    def createnewoutputname(self):
        self.namegen.next()
            
    def resetname(self):
        self.namegen = self.namegenerator()
            
    def copy(self):
        fieldCopy = Field(self.name, self.type, self.len, self.dec)
        fieldCopy.outputname = self.outputname
        fieldCopy.value = self.value
        return fieldCopy
        