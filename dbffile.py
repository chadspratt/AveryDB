# -*- coding: utf-8 -*-
# wrapper for dbfpy utility

from dbfpy import dbf

import genericfile
import field

class DBFFile(genericfile.GenericFile):
    def __init__(self, filename):
        self.filename = filename
        self.fh = dbf.Dbf(filename, readOnly=True)
        
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
        self.fh.addField((field.name, field.type, field.len, field.dec))
        
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