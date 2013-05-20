# -*- coding: utf-8 -*-
# handles the initialization and configuration of the output
# this just leaves dojoin(), the actual execution, needing a home

class OutputManager:
    def __init__(self):
        #place holder
        self.outputfilename = ''
        self.outputtype = 'dbf'
        self.outputfields = {}      # stores Field objects by their uppercase output name
        self.outputorder = []       # output names, stores order of the fields
        self.curfieldindex = -1
        
    def clear(self):
        self.output = ''
    
    def setoutputtype(self, outputtype):
        self.outputtype = outputtype
        
    def addfield(self, filealias, field):
        # dbf is not case sensitive (won't allow 'objectID' and 'objectid')
        # outputfields uses uppercase names to facilitate checking for duplicates
        while field.outputname.upper() in self.outputfields:
            field.createnewoutputname()
        # this format will change when a better field calculator is implemented
        field.outputvalue = filealias + '.' + field.name
        self.outputfields[field.outputname.upper()] = field
        self.outputorder.append(field.outputname)
    
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
        
    def updatefield(self, fieldname, fieldvalue, fieldtype, fieldlen, fielddec):
        field = self.outputfields[self.outputorder[self.curfieldindex].upper()]
        if fieldname != field.name:
            if fieldname.upper() in self.outputfields:
                return 'duplicate name'
            self.outputorder[self.curfieldindex] = fieldname
            del self.outputfields[field.name.upper()]
            self.outputfields[fieldname.upper()] = field
        field.outputname = fieldname
        field.value = fieldvalue
        field.type = fieldtype
        field.len = fieldlen
        field.dec = fielddec
        
    def __getitem__(self, key):
        """Retrieve a Field object by output name or by index"""
        if type(key) == str:
            return self.outputfields[key.upper()]
        elif type(key) == int:
            return self.outputfields[self.outputorder[key].upper()]