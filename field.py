# -*- coding: utf-8 -*-

class Field:
    def __init__(self, fieldname, fieldtype, fieldlen, fielddec):
        # permanent references to the field source
        self.name = fieldname
        self.outputname = fieldname
        self.value = fieldname
        self.type = fieldtype
        self.len = fieldlen
        self.dec = fielddec
        
    def createnewoutputname(self, lenlimit=10):
        """Generate an alternate filename to deal with duplicates when initiating the output."""
        namelen = len(self.name) #store original length
        # append a number to create a different name
        dupecount = 1
        countlen = 1
        trimamount = namelen + countlen - lenlimit
        while True:
            # append next number to original alias
            self.outputname = self.name[:trimamount] + str(dupecount)
            yield self.outputname
            dupecount += 1
            countlen = len(str(dupecount))
            trimamount = namelen + countlen - lenlimit