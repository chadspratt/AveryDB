# -*- coding: utf-8 -*-

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
        