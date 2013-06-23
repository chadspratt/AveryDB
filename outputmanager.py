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
# handles the initialization and configuration of the output
# this just leaves dojoin(), the actual execution, needing a home

import field
from filetypes import dbffile

class OutputManager(object):
    def __init__(self):
        # hard-coded for dbf for now
        self.outputfilename = ''
        self.outputtype = 'dbf'
        self.fieldtypes = ['C','N','F','I','Y','L','M','D','T']
        self.outputfields = {}      # stores Field objects by their uppercase output name
        self.outputorder = []       # output names, stores order of the fields
        self.editField = ''
        self.fieldattr = ['Name', 'Type', 'Length', 'Decimals', 'Value']
        self.fieldattrorder = ['type', 'length', 'decimals']
        
    def clear(self):
        self.outputfields = {}
        self.outputorder = []
    
    def setoutputtype(self, outputtype):
        """Sets the format of the output. Only dbf is supported right now."""
        self.outputtype = outputtype
        
    def setoutputfile(self, outputfile):
        self.outputfile = outputfile
        
    # existing fields will come with a filealias. new fields may come with an index
    # could use better design
    def addfield(self, field, filealias = None, fieldindex = 'end'):
        """Takes a field object and adds it to the output."""
        # if field is being created from an input field, make a copy to use for the output field
        if filealias:            
            newField = field.copy()
            newField.value = '!' + filealias + '.' + newField.name + '!'
        # if it is a new field, just use the one passed as an argument
        else:
            newField = field
            
        # dbf is not case sensitive (won't allow 'objectID' and 'objectid')
        # outputfields uses uppercase names to facilitate checking for duplicates
        while newField.name.upper() in self.outputfields:
            newField.createnewname()

        self.outputfields[newField.name.upper()] = newField
        # inserts after the first selected item in the gui list. if nothing is selected, it goes to the end
        if fieldindex == 'end':
            self.outputorder.append(newField.name)
        else:
            self.outputorder.insert(fieldindex, newField.name)
            
        return newField
            
    def addnewfield(self, fieldname = 'newfield',
                                 fieldattributes = {'type' : 'C', 'length' : 254, 'decimals' : 0},
                                 fieldvalue = '', fieldindex = 'end'):
        """Takes field attributes and adds a field to the output."""
        newField = field.Field(fieldname, fieldattributes, fieldvalue)
        self.addfield(newField, fieldindex=fieldindex)
        # inconsistent, should return newField instead
        return newField
    
    def removefield(self, fieldindex):
        """Takes a field index and removes the field in that postion from the output."""
        fieldname = self.outputorder[fieldindex]
        del self.outputfields[fieldname.upper()]
        self.outputorder.remove(fieldname)
        
    def movefield(self, fieldindex, newfieldindex):
        if newfieldindex == 'start':
            newfieldindex = 0
        elif newfieldindex == 'end':
            newfieldindex = len(self.outputorder)
        self.outputorder.insert(newfieldindex, self.outputorder.pop(fieldindex))
            
    def getindex(self, field):
        return self.outputorder.index(field.name)
    
    def __getitem__(self, key):
        """Retrieve a Field object by index or by output name"""
        # since field names can't be just a number, interpret all numbers as indices
        if isinstance(key, int) or key.isdigit():
            return self.outputfields[self.outputorder[int(key)].upper()]
        else:
            return self.outputfields[key.upper()]
            
    def __iter__(self):
        """Return all output fields in order"""
        for fieldname in self.outputorder:
            yield self.outputfields[fieldname.upper()]
            
    def __len__(self):
        return len(self.outputfields)
        