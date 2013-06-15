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

class OutputManager(object):
    def __init__(self):
        #place holder
        self.outputfilename = ''
        self.outputtype = 'dbf'
        self.fieldtypes = ['C','N','F','I','Y','L','M','D','T']
        self.outputfields = {}      # stores Field objects by their uppercase output name
        self.outputorder = []       # output names, stores order of the fields
        self.editField = ''
        
    def clear(self):
        self.outputfields = {}
        self.outputorder = []
    
    def setoutputtype(self, outputtype):
        """Sets the format of the output. Only dbf is supported right now."""
        self.outputtype = outputtype
        
    # existing fields will come with a filealias. new fields may come with an index
    def addfield(self, field, filealias = None, index = 'end'):
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
        while newField.outputname.upper() in self.outputfields:
            newField.createnewoutputname()

        self.outputfields[newField.outputname.upper()] = newField
        # inserts after the first selected item in the gui list. if nothing is selected, it goes to the end
        if index == 'end':
            self.outputorder.append(newField.outputname)
        else:
            self.outputorder.insert(index, newField.outputname)
            
        return newField
            
    def addnewfield(self, fieldname, fieldvalue, fieldtype, fieldlen, fielddec, fieldindex):
        """Takes field attributes and adds a field to the output."""
        newField = field.Field(fieldname, fieldtype, fieldlen, fielddec)
        newField.value = fieldvalue
        self.addfield(newField, index=fieldindex)
        return newField.outputname
    
    def removefields(self, fieldnames):
        """Takes a list of field names and removes them from the output."""
        if self.editField:
            editname = self.editField.outputname
        for fn in fieldnames:
            del self.outputfields[fn.upper()]
            self.outputorder.remove(fn)
            if fn == editname:
                self.editField = ''
            
    def movefieldsup(self, fieldindices):
        """Takes a list of sorted field indices and moves each of the fields up one spot in the order."""
        newindices = []
        top = 0
        for fi in fieldindices:
            if fi > top:
                fieldname = self.outputorder[fi]
                self.outputorder.remove(fieldname)
                self.outputorder.insert(fi-1, fieldname)
                newindices.append(fi-1)
            else:
                top = fi + 1
                newindices.append(fi)
        return newindices
        
    def movefieldsdown(self, fieldindices):
        """Takes a list of sorted field indices and moves each of the fields down one spot in the order."""
        fieldindices.reverse()
        newindices = []
        bottom = len(self.outputorder) - 1
        for fi in fieldindices:
            if fi < bottom:
                fieldname = self.outputorder[fi]
                self.outputorder.remove(fieldname)
                self.outputorder.insert(fi+1, fieldname)
                newindices.append(fi+1)
            else:
                bottom = fi - 1
                newindices.append(fi)
        return newindices
        
    def seteditfield(self, fieldindex):
        self.editField = self[fieldindex]
        
    def saveeditfield(self, fieldname, fieldvalue, fieldtype, fieldlen, fielddec):
        """Takes field attributes and overwrites the attributes of the field being edited"""
        returnval = 'ok'
        if self.editField:
            if fieldname != self.editField.outputname:
                if fieldname.upper() in self.outputfields:
                    return 'duplicate name'
                editindex = self.getindex(self.editField)
                self.outputorder[editindex] = fieldname
                del self.outputfields[self.editField.outputname.upper()]
                self.outputfields[fieldname.upper()] = self.editField
            self.editField.outputname = fieldname
            self.editField.value = fieldvalue
            self.editField.type = fieldtype
            self.editField.len = fieldlen
            self.editField.dec = fielddec
            self.editField = ''
        else:
            return 'no field loaded'
        return returnval
            
    def getindex(self, field):
        return self.outputorder.index(field.outputname)
    
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
        