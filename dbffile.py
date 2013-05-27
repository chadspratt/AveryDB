# -*- coding: utf-8 -*-
# wrapper for dbfpy utility

from dbfpy import dbf

import genericfile
import field

class DBFFile(genericfile.GenericFile):
    def __init__(self, filename, mode='r'):
        self.filename = filename
        if mode == 'r':
            self.fh = dbf.Dbf(filename, readOnly=True)
        else:
            self.fh = dbf.Dbf(filename, new=True)
        # not used from here, but I'd like for it to be
        self.fieldtypes = ['C','N','F','I','Y','L','M','D','T']
        
    def getfields(self):
        fieldlist = []
        for f in self.fh.fieldDefs:
            # use a simpler field object for storing the relevant attributes
            newField = field.Field(f.name, f.typeCode, f.length, f.decimalCount)
            fieldlist.append(newField)
        return fieldlist
         
    # poor man's iterator for records in the file
    def readrecords(self):
        for record in self.fh:
            yield record
            
    def addfield(self, field):
        self.fh.addField((field.outputname, field.type, field.len, field.dec))
        
    def getrecordcount(self):
        return self.fh.recordCount
        
    def addrecord(self, newrecord):
        rec = self.fh.newRecord()
        for field in newrecord:
            rec[field] = newrecord[field]
        rec.store()
            
    def close(self):
        self.fh.close()
    
    # returns record at given index as a dictionary of field name:value
    def __getitem__(self, index):
        return self.fh[index].asDict()
        