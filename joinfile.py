# -*- coding: utf-8 -*-

import re
# import all filetypes even if unreadable (arcpy)?
# test for ability to read/write gis databases with arcpy
import dbffile

class JoinFile(object):
    def __init__(self, filename='', mode='r'):
        self.filename = filename
        self.indices = {} #not reimplemented yet
        if filename != '':
            self.status = self.openfile(filename, mode=mode)
        else:
            self.status = 'not set'
            # self.fields = [Field0, Field1, ...]
        self.aliasgenerator = self._generatealias()
            
    # not inherited
    def openfile(self, filename, mode='r'):
        lc_filename = filename.lower()
        if lc_filename.endswith('dbf'):
                self.fh = dbffile.DBFFile(filename, mode=mode)
            # other cases will go here if/when other files are supported. from here it is filetype agnostic
            # read field names/types
        #this return can't happen unless selecting invalid files is allowed in the first place
        else:            
            self.status = 'invalid file type'
            return self.status
        
        self.status = 'open'
        return self.status
   
    def getfields(self):
        """Returns a list of fields. The fields are stored as dictionaries that contain their attributes."""
        return self.fh.getfields()
        
    # generate and return an alias for the file. Each time a file is opened
    def _generatealias(self):
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
    
    def generatealias(self):
            return self.aliasgenerator.next()
            
    def readrecords(self):
        return self.fh.readrecords()
        
    def addfield(self, field):
        self.fh.addfield(field)
        
    def getrecordcount(self):
        return self.fh.getrecordcount()
    
    def buildindex(self, fieldname):
            # check if it's already built. I don't think it's possible
            if fieldname in self.indices:
                return
            print 'building index: ', self.filename, ' - ', fieldname, '\n'
            fieldindex = {}
            i = 0
            for rec in self.fh.readrecords():
                # store the index of a record using the value of the specificed field as the key
                # this doesn't check for duplicates since we can only use one record when doing a join.
                # If a value appears in more than one record, the last will be used
                fieldindex[rec[fieldname]] = i
                i += 1
            
            self.indices[fieldname] = fieldindex
            
    def getjoinrecord(self, fieldname, fieldvalue):
        if fieldname in self.indices:
            if fieldvalue in self.indices[fieldname]:
                recordindex = self.indices[fieldname][fieldvalue]
                return self[recordindex]
                
    def addrecord(self, newrecord):
        return self.fh.addrecord(newrecord)
        
    def close(self):
        self.fh.close()

    def __getitem__(self, key):
        return self.fh[key]
