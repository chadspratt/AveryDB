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
# methods that respond to and update the GUI and pass the rest off as much as possible
import re
import gtk

import gui
import filemanager
import joinmanager
import outputmanager
import calculator
#import joinfile #imported via gui via filemanager

class DBFUtil(object):
    def __init__(self):
        self.gui = gui.creategui(self)
        self.files = filemanager.FileManager()
        self.joins = joinmanager.JoinManager()
        self.outputs = outputmanager.OutputManager()
        self.calc = calculator.Calculator()
            
        # needs to be last because control goes to the gui once it's called
        gui.startgui(self.gui)

    def addfile(self, widget, data=None):
        """Open a new file for joining to the target."""
        addfiledialog = self.gui.filedialog(self.files.filetypes)
        response = addfiledialog.run()
        # check that a file was selected
        if response == gtk.RESPONSE_OK:
            newfilename = addfiledialog.get_filename()
            newfilealias = self.files.addfile(newfilename)
            # add to the file list
            filelist = self.gui['filelist']
            newrow = filelist.append([newfilealias])
            
            # set as target if no target is set
            if self.joins.gettarget() == '':
                self.joins.settarget(newfilealias)
                self.gui['targetcombo'].set_active_iter(newrow)
#                self.refreshjoinlists() # setting the combobox active item will cause this to get called
        addfiledialog.destroy()
    
    def removefile(self, widget, data=None):
        """Close a file and remove all joins that depend on it."""
        # get the selection from the list of files
        fileselection = self.gui['fileview'].get_selection()
        (filelist, selected) = fileselection.get_selected()
        if selected:
            filealias = filelist.get_value(selected, 0)
            
            # remove joins that depend on the file
            self.joins.removefile(filealias)
            # remove the file
            self.files.removefile(filealias)
            
            # remove from gui list and from the fields dictionary
            filelist.remove(selected)
            fileselection.unselect_all()
                        
            # check if target was cleared and default it to the first file remaining in the list, if any
            if self.joins.gettarget() == '':
                if len(filelist) > 0:
                    newtargetiter = filelist.get_iter(0)
                    self.gui['targetcombo'].set_active_iter(newtargetiter)
                    
            # refresh join lists in case the removed file was in one of them
            self.refreshjoinlists()
            # want to check the outputs for fields that now have broken references.
            # if not remove them, show some sort of alert
            
    def changetarget(self, widget, data=None):
        """Open a new file or set an already open file as the target for joining."""
        newtarget = self.gui['targetcombo'].get_active_text()
        self.joins.settarget(newtarget)
        self.refreshjoinlists()
        
    def refreshjoinlists(self):
        # refresh the target alias combobox list
        targetfilelist = self.gui['targetfilelist']
        targetfilelist.clear()
        
        for alias in self.joins.getjoinedaliases():
            targetfilelist.append([alias])
                    
        # refresh the list of joins
        self.gui['jointree'].clear()
        self.rebuildjointree(None, self.joins.gettarget())
        self.gui['joinview'].expand_all()
        
    # recursive function to fill jointree from
    def rebuildjointree(self, parentiter, alias):
        newparent = self.gui['jointree'].append(parentiter, [alias])
        for childjoin in self.joins[alias]:
            self.rebuildjointree(newparent, childjoin.joinalias)
            
    def joinaliaschanged(self, widget, data=None):
        """Populate the second set of listboxes with the fields from the selected files."""
        # clear the liststore and add the new items
        joinfieldlist = self.gui['joinfieldlist']
        joinfieldlist.clear()
        
        # get the selected file alias
        joinalias = self.gui['joinaliascombo'].get_active_text()
        if joinalias != None:            
            # Add the fields from the file to the joinfieldcombo's model (joinfieldlist).
            joinfields = self.files[joinalias].getfields()
            for joinfield in joinfields:
                joinfieldlist.append([joinfield.name])
                    
    def targetaliaschanged(self, widget, data=None):
        """Populate the second set of listboxes with the fields from the selected files."""
        # clear the liststore and add the new items
        targetfieldlist = self.gui['targetfieldlist']
        targetfieldlist.clear()
        
        # get the selected file alias
        targetalias = self.gui['targetaliascombo'].get_active_text()
        if targetalias != None:
            # Add the fields from the file to the joinfieldcombo's model (joinfieldlist).
            targetfields = self.files[targetalias].getfields()
            for targetfield in targetfields:
                targetfieldlist.append([targetfield.name])

                    
    # 'apply' join choice button
    def addjoin(self, widget, data=None):
        """Save join using the selected fields in the gui."""
        # get combobox selections
        joinalias = self.gui['joinaliascombo'].get_active_text()
        joinfield = self.gui['joinfieldcombo'].get_active_text()
        targetalias = self.gui['targetaliascombo'].get_active_text()
        targetfield = self.gui['targetfieldcombo'].get_active_text()
        
        if joinfield != None and targetfield != None:
            # save to joins
            result = self.joins.addjoin(joinalias, joinfield, targetalias, targetfield)
            if result:
                self.gui.messagedialog(result)
            else:
                self.refreshjoinlists()
            
    # non-critical, write later
    def removejoin(self, widget, data=None):
        self.gui.messagedialog('removing a join not implemented yet, low priority')
            
    def changeoutputformat(self, widget, data=None):
        self.gui.messagedialog('changing output format not implemented yet, low priority')

    # populate the list of output fields with all the input fields
    def initoutput(self, widget, data=None):
        """Initialize the list of output fields and add all fields to the OutputManager."""
        self.outputs.setoutputfile(self.files.openoutputfile)
        outputfieldattributes = self.outputs.fieldattr
        self.gui.replacecolumns('outputlist', 'outputview', outputfieldattributes)
        outputlist = self.gui['outputlist']
        
        self.outputs.clear()
        # check that a target file has been opened
        if self.joins.targetalias:
            # add all the fields from the target and everything joined to it
            for filealias in self.joins.getjoinedaliases():
                for field in self.files[filealias].getfields():
                    newField = self.outputs.addfield(field, filealias)
                    outputlist.append(newField.getattributelist(self.outputs.fieldattrorder))
                    
    def updatefieldattribute(self, cell, row, new_value, outputlist, column):
        outputlist[row][column] = new_value
        # magic happens
        self.outputs[row][column] = new_value
        
    # 'add field' button
    def addoutput(self, widget, data=None):
        # get the selected row from the output list
        selection = self.gui['outputview'].get_selection()
        # (model, [(path0,), (path1,), ...])
        (outputlist, selectedrows) = selection.get_selected_rows()
        if selectedrows:
            lastselectedindex = selectedrows[-1][0]
            insertindex = lastselectedindex + 1
        else:
            insertindex = len(self.gui['outputlist'])
        
        # add an empty row after the last selected
        newField = self.outputs.addnewfield(fieldindex=insertindex)
        outputlist.insert(insertindex, newField.getattributelist(self.outputs.fieldattrorder))
                                             
        selection.unselect_all()
        selection.select_path(insertindex)
        self.gui['outputview'].scroll_to_cell(insertindex)

    # 'save field' button
    def copyoutput(self, widget, data=None):
        """Create a copy of the selected field[s]."""
        selection = self.gui['outputview'].get_selection()
        # (model, [(path0,), (path1,), ...])
        (outputlist, selectedrows) = selection.get_selected_rows()
        if selectedrows:
            selection.unselect_all()
            # reverse the list so that the indices won't get messed up as items are added
            selectedrows.reverse()
            for row in selectedrows:
                insertindex = row[0] + 1
                fieldCopy = self.outputs[row[0]].copy()
                self.outputs.addfield(fieldCopy, fieldindex=insertindex)
                outputlist.insert(insertindex, fieldCopy.getattributelist(self.outputs.fieldattrorder))
                selection.select_path(insertindex)
                self.gui['outputview'].scroll_to_cell(insertindex)
        
##                                                ##
# Everything above here is "done" #
##                                                ##
        
    # 'del field' button
    def removeoutput(self, widget, data=None):
        """Remove fields from the output."""
        selection = self.gui['outputview'].get_selection()
        # (model, [(path0,), (path1,), ...])
        (outputlist, selectedrows) = selection.get_selected_rows()
        if selectedrows:
            selection.unselect_all()
            # sort the list in reverse so that deletions won't affect the remaining indices
            selectedrows.sort(reverse=True)
            for row in selectedrows:
                outputlist.remove(outputlist.get_iter(row))
                self.outputs.removefield(row[0])
    
#        # get the indices of the selected fields
#        selected = [int(item) for item in self.gui.output_list.curselection()]
#        selectednames = [self.gui.output_list.get(i) for i in selected]
#
#        ef = self.outputs.editField
#        self.outputs.removefields(selectednames)
#        
#        # clear the fields if the field loaded for editing was just removed
#        if ef and not self.outputs.editField:
#            self.gui.outputname.delete(0,Tkinter.END)
#            self.gui.outputvalue.delete(1.0,Tkinter.END)
#            self.gui.fieldtype.delete(0,Tkinter.END)
#            self.gui.fieldlen.delete(0,Tkinter.END)
#            self.gui.fielddec.delete(0,Tkinter.END)
#        
#        # reverse the list to delete from the back so the indices don't get messed up as we go
#        selected.reverse()
#        for index in selected:
#            self.gui.output_list.delete(index)

    # 'move up' button
    def movetop(self, widget, data=None):
        """Move the selected items up in the list of output fields."""
        # get the indices of the selected fields
        selected = [int(item) for item in self.gui.output_list.curselection()]
        if len(selected) > 0:
            newselection = self.outputs.movefieldsup(selected)
    
            # update gui list with new order
            self.gui.output_list.delete(0,Tkinter.END)
            for field in self.outputs:
                self.gui.output_list.insert(Tkinter.END, field.outputname)
            
            # keep the same entiries in the list highlighted after moving them
            self.gui.output_list.selection_clear(0, Tkinter.END)
            for index in newselection:
                self.gui.output_list.selection_set(index)
            self.gui.output_list.see(newselection[0]-1)
            
    # 'move up' button
    def moveup(self, widget, data=None):
        """Move the selected items up in the list of output fields."""
        # get the indices of the selected fields
        selected = [int(item) for item in self.gui.output_list.curselection()]
        if len(selected) > 0:
            newselection = self.outputs.movefieldsup(selected)
    
            # update gui list with new order
            self.gui.output_list.delete(0,Tkinter.END)
            for field in self.outputs:
                self.gui.output_list.insert(Tkinter.END, field.outputname)
            
            # keep the same entiries in the list highlighted after moving them
            self.gui.output_list.selection_clear(0, Tkinter.END)
            for index in newselection:
                self.gui.output_list.selection_set(index)
            self.gui.output_list.see(newselection[0]-1)

    # 'move down' button
    def movedown(self, widget, data=None):
        """Move the selected items up in the list of output fields."""
        # get the indices of the selected fields
        selected = [int(item) for item in self.gui.output_list.curselection()]
        if len(selected) > 0:
            newselection = self.outputs.movefieldsdown(selected)
            
            # update gui list with new order
            self.gui.output_list.delete(0,Tkinter.END)
            for field in self.outputs:
                self.gui.output_list.insert(Tkinter.END, field.outputname)
                    
            # keep the same entiries in the list highlighted after moving them
            self.gui.output_list.selection_clear(0, Tkinter.END)
            for index in newselection:
                self.gui.output_list.selection_set(index)
            self.gui.output_list.see(newselection[-1]+1)
            
    # 'move down' button
    def movebottom(self, widget, data=None):
        """Move the selected items up in the list of output fields."""
        # get the indices of the selected fields
        selected = [int(item) for item in self.gui.output_list.curselection()]
        if len(selected) > 0:
            newselection = self.outputs.movefieldsdown(selected)
            
            # update gui list with new order
            self.gui.output_list.delete(0,Tkinter.END)
            for field in self.outputs:
                self.gui.output_list.insert(Tkinter.END, field.outputname)
                    
            # keep the same entiries in the list highlighted after moving them
            self.gui.output_list.selection_clear(0, Tkinter.END)
            for index in newselection:
                self.gui.output_list.selection_set(index)
            self.gui.output_list.see(newselection[-1]+1)

    # 'execute join' button
    def executejoin(self, widget, data=None):
        """Execute the join and output the result"""
        if len(self.outputs) == 0:
            return
        # build indexes of the join fields
        self.buildindexes()
    
        targetalias = self.joins.gettarget()
        targetfile = self.files[targetalias]
        
        # create output file. I think it will cleanly overwrite the file if it already exists
        outputfilename = self.gui.outputfilename.get()
        outputfile = self.files.openoutputfile(outputfilename)
        
        # create fields
        for fieldname in self.outputs.outputorder:
            outputfile.addfield(self.outputs[fieldname])
    
        # loop through target file
        i = 0
        recordcount = targetfile.getrecordcount()
        print 'total records:', recordcount
        while i < recordcount:
            print 'processing record: ', i, '%f%%'%(float(i)/recordcount*100)
            # process however many records before updating status
            for i in range(i, min(i+1000,recordcount)):
                # inputvalues[filealias][fieldname] = value
                inputvalues = {}
                inputvalues[targetalias] = targetfile[i]
                
                for joinlist in self.joins:
                    for join in joinlist:
                        joinvalue = inputvalues[join.targetalias][join.targetfield]
                        joinFile = self.files[join.joinalias]
                        # Will be None if there isn't a matching record to join
                        temprecord = joinFile.getjoinrecord(join.joinfield, joinvalue)
                        if temprecord is None:                            
                            print join.joinfield+':', joinvalue, '- not found'
                        else:
                            inputvalues[join.joinalias] = temprecord
    
#                print 'inputvalues', inputvalues
                newrec = {}
                for field in self.outputs:
                    # field.value ex: '!file0.field0! + !file1.field1!'
                    fieldrefs = re.findall('!([^!]+)!', field.value)
                    fieldvalue = str(field.value)
                    # Replace eacy file.field reference with the actual value
                    for fieldref in fieldrefs:
                        filealias, fieldname = fieldref.split('.')
#                        print refsplit
                        # check that each referenced file was successfully joined
                        if filealias in inputvalues:
                            refvalue = inputvalues[filealias][fieldname]
                            fieldvalue = re.sub('!'+fieldref+'!', str(refvalue), fieldvalue)
                        # if it didn't join, use a blank value
                        else:
                            # insert a blank value for the reference that matches the type of the output field
                            # with more effort, it could match the type of the field that didn't get joined
                            fieldvalue = re.sub('!'+fieldref+'!', str(self.blankvalue(field)), fieldvalue)
                        
                    # Apply any calculating. Want to make compatible with the arcmap field calculator.
                    # That is extra functionality, with a second input field for the code block
                    try:
                        newrec[field.outputname] = eval(fieldvalue)
                    except NameError:
                        newrec[field.outputname] = fieldvalue
                    except SyntaxError:
                        newrec[field.outputname] = fieldvalue
                    except TypeError:
                        newrec[field.outputname] = fieldvalue
                
                outputfile.addrecord(newrec)
                                
                i = i + 1
                
        outputfile.close()
        print 'processing complete'
#        for joinfile in self.files:
#            print joinfile
#            joinfile.close()
        
    # util function used in dojoin()
    # building an index for each join dbf file is better than trying to sort the files
    # an index is needed so that, as it goes through the target table, record by record,
    # we can quickly find the correct record with the index and jump straight to it
    def buildindexes(self):
        for filealias in self.joins.getjoinedaliases():
            if filealias in self.joins:
                for join in self.joins[filealias]:
                    self.files[join.joinalias].buildindex(join.joinfield)

    # util function used in dojoin()
    # this is all arbitrary
    def blankvalue(self, field):
        if field.type == 'N':
            return 0
        elif field.type == 'F':
            return 0.0
        elif field.type == 'C':
            return ''
        # i don't know for this one what a good nonvalue would be
        elif field.type == 'D':
            return (0,0,0)
        elif field.type == 'I':
            return 0
        elif field.type == 'Y':
            return 0.0
        elif field.type == 'L':
            return -1
        elif field.type == 'M':
            return " " * 10
        elif field.type == 'T':
            return

dbfUtil = DBFUtil()



