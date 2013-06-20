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
# wrapper for dbfpy utility
from collections import OrderedDict

from libraries.dbfpy import dbf

import genericfile
import field

FILETYPEEXT = '.dbf'
FILETYPEDESCRIP = 'dbase file'

class DBFFile(genericfile.GenericFile):
    def __init__(self, filename, mode='r'):
        self.filename = filename
        if mode == 'r':
            self.fh = dbf.Dbf(filename, readOnly=True)
        else:
            self.fh = dbf.Dbf(filename, new=True)
        # not used from here, but I'd like for it to be
        self.fieldtypes = ['C','N','F','I','Y','L','M','D','T']
        self.fieldattrorder = ['type', 'length', 'decimals']
        
    def getfields(self):
        """Returns the fields of the file as a list of Field objects"""
        fieldlist = []
        for f in self.fh.fieldDefs:
            # use ordereddict to enable accessing attributes by index
            fieldattrs = OrderedDict({'type' : f.typeCode,
                                'length' : f.length,
                                'decimals' : f.decimalCount})
            newField = field.Field(f.name, fieldattributes=fieldattrs)
            fieldlist.append(newField)
        return fieldlist
         
    # poor man's iterator for records in the file
    def readrecords(self):
        for record in self.fh:
            yield record
            
    def addfield(self, field):
        self.fh.addField((field.name, field['type'], field['length'], field['decimals']))
        
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
        