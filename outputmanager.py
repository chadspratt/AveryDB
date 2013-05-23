# -*- coding: utf-8 -*-
# handles the initialization and configuration of the output
# this just leaves dojoin(), the actual execution, needing a home

import field

class OutputManager(object):
    def __init__(self):
        #place holder
        self.outputfilename = ''
        self.outputtype = 'dbf'
        self.outputfields = {}      # stores Field objects by their uppercase output name
        self.outputorder = []       # output names, stores order of the fields
        self.editindex = -1
        self.editField = ''
        
    def clear(self):
        self.output = ''
    
    def setoutputtype(self, outputtype):
        self.outputtype = outputtype
        
    # existing fields will come with a filealias. new fields may come with an index
    def addfield(self, field, filealias = None, index = -1):
        """Add an existing field from a file or field created in this program"""
        # dbf is not case sensitive (won't allow 'objectID' and 'objectid')
        # outputfields uses uppercase names to facilitate checking for duplicates
        while field.outputname.upper() in self.outputfields:
            field.createnewoutputname()
        # this format will change when a better field calculator is implemented
        if filealias:
            field.value = filealias + '.' + field.name
        self.outputfields[field.outputname.upper()] = field
        if index > 0:
            self.outputorder.insert(index, field.outputname)
        else:
            self.outputorder.append(field.outputname)
#    
#    def addnewfield(self, field, index):
#        while field.outputname.upper() in self.outputfields:
#            field.createnewoutputname()
#        self.outputfields[field.outputname.upper()] = field
    
    def removefields(self, fieldnames):
        for fn in fieldnames:
            del self.outputfields[fn.upper()]
            self.outputorder.remove(fn)
            
    def movefieldsup(self, fieldindices):
        top = 0
        for fi in fieldindices:
            if fi > top:
                fieldname = self.outputorder[fi]
                self.outputorder.remove(fieldname)
                self.outputorder.insert(fi-1, fieldname)
            else:
                top = fi + 1
        return self.outputorder
        
    def movefieldsdown(self, fieldindices):
        fieldindices.reverse()
        bottom = len(self.outputorder) - 1
        for fi in fieldindices:
            if fi < bottom:
                fieldname = self.outputorder[fi]
                self.outputorder.remove(fieldname)
                self.outputorder.insert(fi+1, fieldname)
            else:
                bottom = fi - 1
        return self.outputorder
        
    def loadfield(self, fieldindex):
        self.editindex = fieldindex
        self.editField = self[fieldindex]
        
    def savefield(self, fieldname, fieldvalue, fieldtype, fieldlen, fielddec):
        returnval = 'ok'
        if self.editField:
            if fieldname != self.editField.outputname:
                if fieldname.upper() in self.outputfields:
                    return 'duplicate name'
                self.outputorder[self.curfieldindex] = fieldname
                del self.outputfields[self.editField.name.upper()]
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
        
    def createfield(self, fieldname, fieldvalue, fieldtype, fieldlen, fielddec, fieldindex):
        newfield = field.Field(fieldname, fieldtype, fieldlen, fielddec)
        newfield.value = fieldvalue
        if fieldindex > 0:
            self.addfield(newfield, index=fieldindex)
        else:
            self.addfield(newfield)
            
    def getindex(self, field):
        return self.outputorder.index(field.outputname)
    
    def __getitem__(self, key):
        """Retrieve a Field object by output name or by index"""
        if type(key) == str:
            return self.outputfields[key.upper()]
        elif type(key) == int:
            return self.outputfields[self.outputorder[key].upper()]
            
    def __iter__(self):
        """Return all output fields in order"""
        for fieldname in self.outputorder:
            yield self.outputfields[fieldname.upper()]