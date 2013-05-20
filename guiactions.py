# -*- coding: utf-8 -*-
# methods that respond to and update the GUI and pass the rest off as much as possible
# I'm also going to try to limit access to App's allfiles and targetfile attributes

#import Tkinter #imported via gui via filemanager
#import re #imported via gui via filemanager
import Tkinter
import gui
import filemanager
import joinmanager
import outputmanager
#import joinfile #imported via gui via filemanager

class DBFUtil:
    def __init__(self):
        self.app = gui.initapp(self)
        self.files = filemanager.FileManager()
        self.joins = joinmanager.JoinManager()
        self.outputs = outputmanager.OutputManager()

    # 'add dbf' button
    def openjoin(self):
        """Open a new file for joining to the target."""
        newfilealias = self.files.addfile()
        # checks that a file was selected
        if newfilealias:
            # check if file is in the lists already
            if newfilealias not in self.app.dbftargetlist.get(0, Tkinter.END):
                self.app.dbftargetlist.insert(Tkinter.END, newfilealias)
                self.app.dbfjoinlist.insert(Tkinter.END, newfilealias)
        return newfilealias
    
    # 'select target dbf' button. remove opening a new file and instead just set it to an already open file?
    def opentarget(self):
        """Open a new file or set an already open file as the target for joining."""
        newfilealias = self.openjoin()
        if newfilealias:
            # set target
            self.joins.settarget(newfilealias)
            # set the gui label for showing the full path to the target
            self.app.target.__setitem__('text',newfilealias)
    
    # 'remove dbf' button
    def removejoin(self):
        """Close a file and remove all joins that depend on it."""
        # get filename of file selected to be removed
        selected = self.app.dbftargetlist.curselection()[0]
        filename =self. app.dbftargetlist.get(selected)
        
        # remove file
        self.files.removefile(filename)
        # remove joins that depend on the file
        self.joins.removefile(self.files[filename].alias)
        
        # remove from gui list and from the fields dictionary
        self.app.dbftargetlist.delete(selected)
        self.app.dbfjoinlist.delete(selected)
        
    # 'config selected' button
    def loadjoinchoices(self):
        """Populate the second set of listboxes with the fields from the selected files."""
        target = self.files.gettarget()
    #   clear the lists before adding fields of selected table and join table
        self.app.target_list.delete(0,Tkinter.END)
        self.app.join_list.delete(0,Tkinter.END)
    
        targetindex = self.app.dbftargetlist.curselection()
        joinindex = self.app.dbfjoinlist.curselection()
        targetalias = self.app.dbftargetlist.get(targetindex)
        joinalias = self.app.dbfjoinlist.get(joinindex)
    
        # verify that the selectedtarget is joined to the overall target
        if self.joins.checkjoin(target, targetalias) == False:
            print 'Join to the global target first.'
        # Check that selected target  ISN'T joined to selected join
        # this would create a problematic circular join. 
        # If it needs to be done, open the file again to get another alias and use that
        elif self.joins.checkjoin(joinalias, targetalias):
            print 'Cannot create circular join. Reopen the file to use a different alias.'
        else:
            self.joins.curtarget = targetalias
            self.joins.curjoin = joinalias
            for field in self.files[targetalias].getfields():
                self.app.target_list.insert(Tkinter.END, field.name)
            for field in self.files[joinalias].getfields():
                self.app.join_list.insert(Tkinter.END, field.name)
                
    # 'apply' join choice button
    def savejoinchoice(self):
        """Save join using the selected fields in the gui."""
        # get join field names
        targetindex = self.app.target_list.curselection()[0]
        joinindex = self.app.join_list.curselection()[0]
        targetfield = self.app.target_list.get(targetindex)
        joinfield = self.app.join_list.get(joinindex)
    
        # save to joins
        self.joins.addjoin(targetfield, joinfield)
    
        # clear boxes to show that the join is applied
        self.app.target_list.delete(0,Tkinter.END)
        self.app.join_list.delete(0,Tkinter.END)

    # 'init output' button
    # populate the list of output fields with all the input fields
    def initoutput(self):
        """Initialize the list of output fields and add all fields to the OutputManager."""
        # delete any fields already entered
        self.outputs.clear()
        self.app.output_list.delete(0,Tkinter.END)
        
        # get the aliases of all files that are set up to be used
        joinaliases = self.joins.getjoinedaliases()
    
        # add all the fields in those files
        for alias in joinaliases:
            for field in self.files[alias].getfields():
                self.outputs.addfield(alias, field)
                self.app.output_list.insert(Tkinter.END, field.outputname)

    # 'del field' button
    def removeoutput(self):
        """Remove a field from the output."""
        # get the indices of the selected fields
        selected = [int(item) for item in self.app.output_list.curselection()]
        selectednames = [self.app.output_list.get(i) for i in selected]
        
        self.outputs.removefields(selectednames)
        
        # reverse the list to delete from the back so the indices don't get messed  up as we go
        selected.reverse()
        for index in selected:
            self.app.output_list.delete(index)

    # 'move up' button
    def moveup(self):
        """Move the selected items up in the list of output fields."""
        # get the indices of the selected fields
        selected = [int(item) for item in self.app.output_list.curselection()]
        
        neworder = self.outputs.movefieldsup(selected)

        # update gui list with new order
        self.app.output_list.delete(0,Tkinter.END)
        for fieldname in neworder:
            self.app.output_list.insert(Tkinter.END, fieldname)
        
        # keep the same entiries in the list highlighted after moving them
        # I don't understand why this works. It seems like it should run the indices past the end of the list
        new_selection = [x-1 for x in selected]
        for entry in new_selection:
            self.app.output_list.selection_set(entry)
        self.app.output_list.see(int(selected[0])-2)

    # 'move down' button
    def movedown(self):
        """Move the selected items up in the list of output fields."""
        # get the indices of the selected fields
        selected = [int(item) for item in self.app.output_list.curselection()]
        
        neworder = self.outputs.movefieldsdown(selected)
        
        # update gui list with new order
        self.app.output_list.delete(0,Tkinter.END)
        for fieldname in neworder:
            self.app.output_list.insert(Tkinter.END, fieldname)
                
        # keep the same entiries in the list highlighted after moving them
        new_selection = [x-1 for x in selected]
        for entry in new_selection:
            self.app.output_list.selection_set(entry)
        self.app.output_list.see(int(selected[0])-2)
        

    # 'config selected field' button
    def configoutput(self):
        """Load field data into the GUI for editing."""
        # save the pos of the first selected field, which will be the one loaded for editing
        self.outputs.curfieldindex = self.app.output_list.curselection()[0]
        curfield = self.outputs[self.outputs.curfieldindex]
        
        # Clear then load the GUI field with the values
        self.app.outputname.delete(0,Tkinter.END)
        self.app.outputvalue.delete(1.0,Tkinter.END)
        self.app.fieldtype.delete(0,Tkinter.END)
        self.app.fieldlen.delete(0,Tkinter.END)
        self.app.fielddec.delete(0,Tkinter.END)
        self.app.outputname.insert(Tkinter.END, curfield.outputname)
        self.app.outputvalue.insert(Tkinter.END, curfield.value)
        self.app.fieldtype.insert(Tkinter.END, curfield.type)
        self.app.fieldlen.insert(Tkinter.END, curfield.len)
        self.app.fielddec.insert(Tkinter.END, curfield.dec)
        
    # 'save field' button
    def saveoutput(self):
        """Save the modified attributes of a field."""
        newfieldname = self.app.outputname.get()
        # don't remember why this call is different, i guess because it gets parsed and calculated
        newfieldvalue = self.app.outputvalue.get(1.0,Tkinter.END).strip()
        newfieldtype = self.app.fieldtype.get().upper()
        newfieldlen = int(self.app.fieldlen.get())
        newfielddec = int(self.app.fielddec.get())
        # if the name changed, check that new name isn't already in use
        result = self.outputs.updatefield(newfieldname, newfieldvalue, newfieldtype, newfieldlen, newfielddec)
        if result == 'duplicate name':
            print 'field name already in use'
            return
        if newfieldname != oldfieldname:
            if newfieldname in outputfields:
                return
                
        app.output_list.delete(oldfieldindex)
        app.output_list.insert(oldfieldindex,newfieldname)
        app.output_list.selection_clear(0,END)
        app.output_list.selection_set(oldfieldindex)
        app.output_list.see(oldfieldindex)
        app.outputname.delete(0,END)
        app.outputvalue.delete(1.0,END)
        app.fieldtype.delete(0,END)
        app.fieldlen.delete(0,END)
        app.fielddec.delete(0,END)
        
dbfUtil = DBFUtil()



