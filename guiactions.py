# -*- coding: utf-8 -*-
# methods that respond to and update the GUI and pass the rest off as much as possible
# I'm also going to try to limit access to App's allfiles and targetfile attributes

#import Tkinter #imported via gui via filemanager
#import re #imported via gui via filemanager
import gui
import Tkinter
#import joinfile #imported via gui via filemanager

# GLOBALS
# gui window
app = gui.initapp()


        
# 'add dbf' button
def openjoin():
    """Open a new file for joining to the target."""
    global app
    newfilealias = app.files.addfile()
    # checks that a file was selected
    if newfilealias:
        # check if file is in the lists already
        if newfilealias not in app.dbftargetlist.get(0, Tkinter.END):
            app.dbftargetlist.insert(Tkinter.END, newfilealias)
            app.dbfjoinlist.insert(Tkinter.END, newfilealias)
    return newfilealias

# 'select target dbf' button. remove opening a new file and instead just set it to an already open file?
def opentarget():
    """Open a new file or set an already open file as the target for joining."""
    global app          #gui.App
    newfilealias = openjoin()
    if newfilealias:
        # set target
        app.joins.settarget(newfilealias)
        # set the gui label for showing the full path to the target
        app.target.__setitem__('text',newfilealias)

# 'remove dbf' button
def removejoin():
    """Close a file and remove all joins that depend on it."""
    global app
    # get filename of file selected to be removed
    selected = app.dbftargetlist.curselection()[0]
    filename = app.dbftargetlist.get(selected)
    
    # remove file
    app.files.removefile(filename)
    # remove joins that depend on the file
    app.joins.removefile(app.files[filename].alias)
    
    # remove from gui list and from the fields dictionary
    app.dbftargetlist.delete(selected)
    app.dbfjoinlist.delete(selected)
    
# 'config selected' button
def loadjoinchoices():
    """Populate the second set of listboxes with the fields from the selected files"""
    global app
    target = app.files.gettarget()
#   clear the lists before adding fields of selected table and join table
    app.target_list.delete(0,Tkinter.END)
    app.join_list.delete(0,Tkinter.END)

    targetindex = app.dbftargetlist.curselection()
    joinindex = app.dbfjoinlist.curselection()
    targetalias = app.dbftargetlist.get(targetindex)
    joinalias = app.dbfjoinlist.get(joinindex)

    # verify that the selectedtarget is joined to the overall target
    if app.joins.checkjoin(target, targetalias) == False:
        print 'Join to the global target first.'
    # Check that selected target  ISN'T joined to selected join
    # this would create a problematic circular join. 
    # If it needs to be done, open the file again to get another alias and use that
    elif app.joins.checkjoin(joinalias, targetalias):
        print 'Cannot create circular join. Reopen the file to use a different alias.'
    else:
        app.joins.curtarget = targetalias
        app.joins.curjoin = joinalias
        for field in app.files[targetalias].getfields():
            app.target_list.insert(Tkinter.END, field.name)
        for field in app.files[joinalias].getfields():
            app.join_list.insert(Tkinter.END, field.name)
            
# 'apply' join choice button
def savejoinchoice():
    global app
    # get join field names
    targetindex = app.target_list.curselection()[0]
    joinindex = app.join_list.curselection()[0]
    targetfield = app.target_list.get(targetindex)
    joinfield = app.join_list.get(joinindex)

    # save to joins
    app.joins.addjoin(targetfield, joinfield)

    # clear boxes to show that the join is applied
    app.target_list.delete(0,Tkinter.END)
    app.join_list.delete(0,Tkinter.END)
    
    
    
    
    
    
    
    
    
    