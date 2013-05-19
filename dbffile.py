# -*- coding: utf-8 -*-
# wrapper for dbfpy utility

import dbfpy
import genericfile
import field

class DBFFile(genericfile.GenericFile):
    def __init__(self, filename):
        self.filename = filename
        self.fh = dbfpy.dbf.Dbf(filename, readOnly=True)
        
    def getfields(self):
        fieldlist = []
        for f in self.fh.fieldDefs:
            # use a simpler field object for storing the relevant attributes
            newField = field.Field(f.name, f.typeCode, f.length, f.decimalCount)
            fieldlist.append(newField)
        return fieldlist
         
    def close(self):
        self.fh.close()