# -*- coding: utf-8 -*-

import re
# import all filetypes even if unreadable (arcpy)?
# test for ability to read/write gis databases with arcpy
import genericfile
import dbffile
import field

class JoinFile(genericfile.GenericFile):
    def __init__(self, filename=''):
        self.filename = filename
        self.indices = {} #not reimplemented yet
        if filename != '':
            self.status = self.openfile(filename)
        else:
            self.status = 'not set'
            # self.fields = [Field0, Field1, ...]
            self.fields = []
            
    # not inherited
    def openfile(self, filename):
        filetype = filename.split('.')[-1].lower()
        if filetype == 'dbf':
                self.fh = dbffile.DBFFile(filename)
            # other cases will go here if/when other files are supported. from here it is filetype agnostic
            # read field names/types
            #this return can't happen unless selecting invalid files is allowed in the first place
        else:            
            self.status = 'invalid file type'
            return self.status
            
        self.fields = self.fh.getfields()
        
        self.status = 'open'
        return self.status
   
    def getfields(self):
        return self.fields
        
    # generate and return an alias for the file. Each time a file is opened
    def getalias(self):
        """Create an alias for a file. Allows more complex joining and a shorter name"""
        filenamesplit = re.findall('[a-zA-Z0-9]+',self.filename)
        alias = filenamesplit[-2]
        # start with just the filename
        yield alias
        # append a number for successive alias requests
        dupecount = 1
        aliaslen = len(alias) #store original length
        while True:
            # append next number to original alias
            alias = alias[:aliaslen] + str(dupecount)
            yield alias
            dupecount += 1