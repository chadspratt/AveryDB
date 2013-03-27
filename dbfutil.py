#! /usr/bin/python27

import re
import os
from Tkinter import *
from tkFileDialog import askopenfilename
# used for reading dbf files
import demdbf
import pickle
# used for writing dbf files
from dbfpy import dbf
import combobox

# [(fieldname, fieldtype, length, decimalplaces), ...]
fields = {}
target = ''
curjoin = ''
# used for editing output fields
oldfieldname = ''
oldfieldindex = -1
# [join_dbf_filename] = [targetindex, joinindex]
# joinfields = {}
# joinalias[alias] = join_dbf_filename, joinalis[join_dbf_filename] = alias
joinaliases = {}
# outputfields['fieldname'] = (fieldvalue, fieldtype, fieldlen, fielddec)
# fieldvalue = filename.fieldname
# fieldvalue is meant to support simple operations. 'f1.f1 + f2.f2' for example
outputfields = {}
# joins[targetfile] = [[targetfield, joinfile, joinfield], ...]
joins = {}
# fileindexes['filename'] = {joinvalue : index, ...}
fileindexes = {}

# 'select target dbf' button
def opentarget():
    global app
    global target
    target = askopenfilename()
    app.target.__setitem__('text',target)
    # don't insert duplicates. won't break anything but it'd be ugly
    if target in fields:
        return
    app.dbftargetlist.insert(END, target)
    app.dbfjoinlist.insert(END, target)
    createalias(target)
    readfields(target)

# 'add dbf' button
def openjoin():
    global app
    filename = askopenfilename()
    # don't insert duplicates.
    if filename in fields:
        return
    app.dbftargetlist.insert(END, filename)
    app.dbfjoinlist.insert(END, filename)
    createalias(filename)
    readfields(filename)

# util function used by opentarget() and openjoin()
def readfields(filename):
    global fields
    tempdbf = demdbf.dbf()
    try:
        tempdbf.open(filename)
    except TypeError:
        return # occurs if cancel is clicked or window is closed for askopenfilename()
    fields[filename] = tempdbf.fields
#    print [items[0] for items in fields[filename]]

# util function used by opentarget and add_dbf
def createalias(filename):
    global joinaliases
    filenamesplit = re.findall('[a-zA-Z0-9]+',filename)
    tempalias = filenamesplit[-2]
    duplicates = {}
    while tempalias in joinaliases:
        try:
            dupecount = duplicates[tempalias]
        except KeyError: # first duplicate, didn't have entry in duplicates{}
            dupecount = 1
        duplicates[tempalias] = dupecount + 1
        tempalias = tempalias+str(dupecount)
    joinaliases[filename] = tempalias
    joinaliases[tempalias] = filename
    return tempalias

# 'remove dbf' button
def removejoin():
    global app
    global fields
    global target
    # get filename of file selected to be removed
    selected = app.dbftargetlist.curselection()[0]
    filename = app.dbftargetlist.get(selected)
    # remove from gui list and from the fields dictionary
    app.dbftargetlist.delete(selected)
    app.dbfjoinlist.delete(selected)
    del fields[filename]
    # call recursive function to remove all joins that depend on the file
    remfromjoins(target, filename)

# starting from 'target', traverse and remove instances of 'join' and things which are joined to 'join'
def remfromjoins(target, join):
    global joins
    # if this is what we're removing...
    if target == join:
        try:
            # remove everything joined to it...
            for entry in joins[join]:
                remfromjoins(join, entry[1])
        except KeyError:
            None # there is nothing joined
        try:
            # then remove it
            joins.remove(join)
        except ValueError:
            None # there is nothing joined
        # signal that the target was removed
        return True
    # if this isn't being removed...
    else:
        try:
            # recursively check everything joined to it
            for entry in joins[target]:
                if remfromjoins(entry[1],join):
                    # then remove it from
                    joins[target].remove(entry)
        except KeyError:
            None # there is nothing joined to target
        # signal that the target was not removed
        return False

# 'config selected' button
def loadjoinchoices():
    global app
    global target
    global curjoin
#   clear the lists before adding fields of selected table and join table
    app.target_list.delete(0,END)
    app.join_list.delete(0,END)

    selectedtarget = app.dbftargetlist.curselection()
    selectedjoin = app.dbfjoinlist.curselection()
    selectedtargetname = app.dbftargetlist.get(selectedtarget)
    selectedjoinname = app.dbfjoinlist.get(selectedjoin)

    # verify that the selectedtarget is joined to the overall target
    if checkjoin(target, selectedtargetname) == False:
        print 'must join to primary target first'
    # verify that selectedtarget join ISN'T joined to selected join
    # this would create a problematic circular join
    elif checkjoin(selectedjoinname, selectedtargetname):
        print 'cannot create circular join. do one at a time'
    else:
        curjoin = (selectedtargetname, selectedjoinname)
        for field in fields[selectedtargetname]:
            app.target_list.insert(END, field[0])
        for field in fields[selectedjoinname]:
            app.join_list.insert(END, field[0])

# utility function used in loadjoinchoices()
# check that the join file is joined to the target file, by any degree
def checkjoin(target, join):
    global joins
    if target == join:
        return True
    try:
        targetjoins = joins[target]
    except KeyError:
        return False
    for entry in targetjoins:
        if checkjoin(entry[1],join):
            return True
    return False

# utility function used nowhere. untested
def printjoins(target):
    global joins
    print joins[target]
    for join in joins[target]:
        printjoins(join[1])    

# 'apply' join choice button
def savejoinchoice():
    global app
    global curjoin
    global joins
    # get join field names
    targetindex = app.target_list.curselection()[0]
    joinindex = app.join_list.curselection()[0]
    targetfield = app.target_list.get(targetindex)
    joinfield = app.join_list.get(joinindex)
    # save to joins
    if curjoin[0] not in joins:
        joins[curjoin[0]] = []
    joins[curjoin[0]].append([targetfield, curjoin[1], joinfield])
    # clear boxes to show that the join is applied
    app.target_list.delete(0,END)
    app.join_list.delete(0,END)

# 'init output' button
# populate the list of output fields with all the input fields
def initoutput():
    global app
    global target
    global joins
    global outputfields
    global fields
    global joinaliases
    duplicates = {}
    # delete any fields already entered
    outputfields.clear()
    app.output_list.delete(0,END)
    
    # create generator
    joinfiles = joinsdfs(target)

    for joinfile in joinfiles:
        filealias = joinaliases[joinfile]
        for field in fields[joinfile]:
            # ensure field names are unique. field names are not case sensitive
            fieldname = field[0].upper()
            while fieldname in outputfields:
                try:
                    dupecount = duplicates[fieldname]
                except KeyError: # first duplicate, didn't have entry in duplicates{}
                    dupecount = 1
                duplicates[fieldname] = dupecount + 1
                countlen = len(str(dupecount))
                fieldlen = len(field[0])
                # dbf files have max field name len of 10
                trimlen = 10 - countlen - fieldlen
                if trimlen < 0:
                    fieldname = fieldname[:trimlen]+str(dupecount)
                else:
                    fieldname = fieldname+str(dupecount)
            app.output_list.insert(END, fieldname)
            outputfields[fieldname] = [filealias+'.'+fieldname, field[1], field[2], field[3]]

# util function to recursively get all filenames from joins{}
# used in initoutput() and dojoin()
def joinsdfs(start):
    global joins
    yield start
    try:
        for entry in joins[start]:
            temp = joinsdfs(entry[1])
            for entry2 in temp:
                yield entry2
    except KeyError:
        None

# 'config selected field' button
def configoutput():
    global app
    global oldfieldname
    global oldfieldindex
    global outputfields
    oldfieldindex = app.output_list.curselection()[0]
    oldfieldname = app.output_list.get(oldfieldindex)
    app.outputname.delete(0,END)
    app.outputvalue.delete(1.0,END)
    app.fieldtype.delete(0,END)
    app.fieldlen.delete(0,END)
    app.fielddec.delete(0,END)
    app.outputname.insert(END, oldfieldname)
    app.outputvalue.insert(END, outputfields[oldfieldname][0])
    app.fieldtype.insert(END, outputfields[oldfieldname][1])
    app.fieldlen.insert(END, outputfields[oldfieldname][2])
    app.fielddec.insert(END, outputfields[oldfieldname][3])

# 'save field' button
def saveoutput():
    global app
    global oldfieldname
    global oldfieldindex
    global outputfields
    newfieldname = app.outputname.get().upper()
    newfieldvalue = app.outputvalue.get(1.0,END)
    newfieldtype = app.fieldtype.get().upper()
    newfieldlen = int(app.fieldlen.get())
    newfielddec = int(app.fielddec.get())
    # if the name changed, check that new name isn't already in use
    if newfieldname != oldfieldname:
        if newfieldname in outputfields:
            print 'field name already in use'
            return
    # store new field properties
    del outputfields[oldfieldname]
    outputfields[newfieldname] = (newfieldvalue, newfieldtype, int(newfieldlen), int(newfielddec))
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

# 'add field' button
def addoutput():
    global app
    global outputfields
    newfieldname = app.outputname.get().upper()
    newfieldvalue = app.outputvalue.get(1.0,END)
    newfieldtype = app.fieldtype.get().upper()
    newfieldlen = int(app.fieldlen.get())
    newfielddec = int(app.fielddec.get())
    if outputfields.has_key(newfieldname):
        print 'field name already in use'
    elif len(newfieldname) > 10:
        print 'field name limited to 10 characters'
    else:
#debateable whether this line should go in or out of the if statement
        outputfields[newfieldname] = (newfieldvalue, newfieldtype, newfieldlen, newfielddec)
        app.output_list.insert(END,newfieldname)
        oldfieldname = newfieldname
        fieldindex = app.output_list.size() - 1
        app.output_list.selection_clear(0,END)
        app.output_list.selection_set(fieldindex)
        app.output_list.see(fieldindex)
        app.outputname.delete(0,END)
        app.outputvalue.delete(1.0,END)
        app.fieldtype.delete(0,END)
        app.fieldlen.delete(0,END)
        app.fielddec.delete(0,END)

# 'del field' button
def removeoutput():
    global app
    global outputfields
    try:
        selected = app.output_list.curselection()[0]
        fieldname = app.output_list.get(selected)
        del outputfields[fieldname]
        app.output_list.delete(selected)
    except IndexError:
        None # nothing selected

# 'move up' button
def moveup():
    global app
    selected = app.output_list.curselection()[0]
    if int(selected) > 0:
        fieldname = app.output_list.get(selected)
        app.output_list.delete(selected)
        app.output_list.insert(int(selected)-1, fieldname)
        app.output_list.selection_set(int(selected)-1)
        app.output_list.see(int(selected)-2)

# 'move down' button
def movedown():
    global app
    selected = app.output_list.curselection()[0]
    if int(selected) < app.output_list.size() - 1:
        fieldname = app.output_list.get(selected)
        app.output_list.delete(selected)
        app.output_list.insert(int(selected)+1, fieldname)
        app.output_list.selection_set(int(selected)+1)
        app.output_list.see(int(selected)+2)

# 'execute join' button
def dojoin():
    global app
    global outputfields
#    global joinfields
    global joins
    global target
    global fileindexes
    global joinaliases
    joinfiles = {}

    # build indexes of the join fields and open all the join files
    buildindexes(target)
    for joinfile in joinsdfs(target):
        # not sure if this will ever hit, as it's currently coded
        if joinfile in joinfiles:
            continue
        tempdbf = demdbf.dbf()
        tempdbf.open(joinfile)
        joinfiles[joinfile] = tempdbf

    # create output file. the filename should probably be choosable
    newdbf = dbf.Dbf('output.dbf', new=True)
    # create fields
    outputfieldnames = app.output_list.get(0, END)
    for fieldname in outputfieldnames:
        curfield = outputfields[fieldname] 
        newdbf.addField((fieldname, curfield[1], curfield[2], curfield[3]))

    # loop through target file
    i = 0
    recordcount = joinfiles[target].recordCount
    while i < recordcount:
        print 'processing record: ', i, '%f%%'%(float(i)/recordcount*100)
        # process however many records before updating status
        for i in range(i, min(i+1000,recordcount)):
            # ['filename.fieldname'] = value
            inputvalues = {}
            targetrecord = joinfiles[target].read(i)
            for field in targetrecord.keys():
                inputvalues[joinaliases[target]+'.'+field] = targetrecord[field]

            # get the records that join with the current target record
            for targetfile in joinsdfs(target):
                # joins[localtarget] will give KeyError
                try:
                    for join in joins[targetfile]:
                        targetfield = join[0]
                        joinfile = join[1]
                        joinfield = join[2]
                        joinindex = join[3]
                # get the value to join on. this should always be a valid key
                        targetvalue = inputvalues[joinaliases[targetfile]+'.'+targetfield]
                        try:
                            joinrecord = joinfiles[joinfile].read(joinindex[targetvalue])
                            for field in joinrecord.keys():
                                inputvalues[joinaliases[joinfile]+'.'+field] = joinrecord[field]
                        # will result in inputvalues[] misses later
                        except KeyError:
                            print joinfield+':', targetvalue, '- not found'
                except KeyError:
                    None # nothing joined to current targetfile

            # input records gathered, ready to assemble the output record
            newrec = newdbf.newRecord()
            for field in outputfieldnames:
                # this is where calculations will go
                fieldvalue = outputfields[field][0]
                # detect expressions by looking for '+-*/' operators
                # can't do '/' until i implement aliases instead of absolute paths
                if re.search('\+|-|==', fieldvalue):
                    print 'original:',fieldvalue
                    fieldtype = outputfields[field][1]
                    # extract fields
                    fieldcomponents = re.findall('[^+\-=\n ]+', fieldvalue)
                    # number fields
                    if fieldtype == 'N':
                        for component in fieldcomponents:
                            print 'component:',component
                            print 'inputvalues[component]:',inputvalues[component]
                            try:
                                fieldvalue = re.sub(component, str(inputvalues[component]), fieldvalue)
                            except KeyError:
                                # this is a non-foolproof way of checking if we got here because of
                                # a failed join or if component is a literal like the number 2
                                # former: replace it with 0. latter, leave it alone
                                if component.split('.')[0] in joinaliases:
                                    # didn't get a join for this field. insert blank value
                                    fieldvalue = re.sub(component, '0', fieldvalue)
#                                fieldvalue = re.sub(component, component, fieldvalue)
                            print 'component subbed:',fieldvalue
                        # check if it's an integer (vs a float)
                        print 'subbed:',fieldvalue
                        if outputfields[field][3] == 0:
                            fieldvalue = int(eval(fieldvalue))
                        else:
                            fieldvalue = eval(fieldvalue)
                        print 'final:',fieldvalue
                    # character fields
                    elif fieldtype == 'C':
                        for component in fieldcomponents:
                            # check if the component is a reference to a field or a literal
                            try:
                                fieldvalue = re.sub(component, '"'+str(inputvalues[component])+'"', fieldvalue)
                            except KeyError:
                                if component.split('.')[0] in outputfieldnames:
                                    # didn't get a join for this field. insert blank value
                                    fieldvalue = re.sub(component, '""', fieldvalue)
                                fieldvalue = re.sub(component, '"'+component+'"', fieldvalue)
                        
                        fieldvalue = eval(fieldvalue)
                    # as yet unsupported fields
                    else:
                        None
                    newrec[field] = fieldvalue
                else:
                    try:
                        newrec[field] = inputvalues[fieldvalue]
                    except KeyError:
                        # didn't get a match to join this particular field
                        newrec[field] = blankvalue(outputfields[field])

            # newrec record is ready
            newrec.store()
            i = i + 1
    newdbf.close()
    for joindbf in joinfiles.values():
        joindbf.close()

# util function used in dojoin()
# building an index for each join dbf file is better than trying to sort the files
# an index is needed so that, as it goes through the target table, record by record,
# we can quickly find the correct record with the index and jump straight to it
def buildindexes(filename):
#    global joinfields
    global joins
#    global fileindexes

#    # check if the index has already been created. haven't tested how long it takes
#    # so don't know if this could actually save much time (how would we even get here?)
#    if os.path.exists(filename+'.jif'):
#        fileindexes[filename] = pickle.load(filename+'.jif')
#    else:
    try:
        for join in joins[filename]:
            joinfile = join[1]
            joinfield = join[2]
            # check if it's already built. I don't think it's possible
            if len(join) == 4:
                continue
            print 'building index: '+joinfile+'\n'
            fileindex = {}
            tempdbf = demdbf.dbf()
            tempdbf.open(joinfile)
            for i in range(tempdbf.recordCount):
                record = tempdbf.read(i)
                # store the joinfield and the index of the record
                # this doesn't check for duplicates since we can only use
                # one record when doing a join. if more than one, the last will be used
                fileindex[record[joinfield]] = i
            # storing the index IN joins is the easiest way to store an index for any
            # possible join that's been set. a.b->b.c, a.b->b.d; a.b->b.c, a.b->c.d
            # potential duplication of effort, but it'd be unusual and hard to optimise out
            join.append(fileindex)
            # recursive call to build indexes of files joined to joinfile
            buildindexes(joinfile)
#        # save the index, just in case it's needed later. wish this worked
#           pickle.dump(fileindex, filename+'.jif')
    except KeyError:
        None # nothing joined to 'filename'

# util function used in dojoin()
# this is all arbitrary
def blankvalue(field):
    fieldtype = field[1]
    if fieldtype == 'N':
        return 0
    elif fieldtype == 'F':
        return 0.0
    elif fieldtype == 'C':
        return ''
    # i don't know for this one what a good nonvalue would be
    elif fieldtype == 'D':
        return (0,0,0)
    elif fieldtype == 'I':
        return 0
    elif fieldtype == 'Y':
        return 0.0
    elif fieldtype == 'L':
        return -1
    elif fieldtype == 'M':
        return " " * 10
    elif fieldtype == 'T':
        return


class App:
    def __init__(self, master):
        frame = Frame(master)
        frame.pack()

        self.button = Button(frame, text='Select target dbf', command=opentarget)
        self.button.pack()

        self.targetframe = Frame(frame)
        self.targetframe.pack()
        self.targetlabel = Label(self.targetframe, text='Target file: ')
        self.targetlabel.pack(side=LEFT)
        self.target = Label(self.targetframe, text='')
        self.target.pack(side=RIGHT)

        self.add_dbf = Button(frame, text='add dbf', command=openjoin)
        self.add_dbf.pack()
        self.remove_dbf = Button(frame, text='remove dbf', command=removejoin)
        self.remove_dbf.pack()

        self.dbflistlabel = Label(frame, text="dbf join files")
        self.dbflistlabel.pack()
        self.dbfframe = Frame(frame)
        self.dbfframe.pack()
        self.dbftargetframe = Frame(self.dbfframe)
        self.dbftargetframe.pack(side=LEFT)
        self.dbftargetlabel = Label(self.dbftargetframe, text='target file')
        self.dbftargetlabel.pack()
        self.dbftargetyscroll = Scrollbar(self.dbftargetframe, orient=VERTICAL)
        self.dbftargetxscroll = Scrollbar(self.dbftargetframe, orient=HORIZONTAL)
        self.dbftargetlist = Listbox(self.dbftargetframe, width=50, yscrollcommand=self.dbftargetyscroll.set, xscrollcommand=self.dbftargetxscroll.set, exportselection=0)
        self.dbftargetyscroll.config(command=self.dbftargetlist.yview)
        self.dbftargetxscroll.config(command=self.dbftargetlist.xview)
        self.dbftargetyscroll.pack(side=RIGHT, fill=Y)
        self.dbftargetxscroll.pack(side=BOTTOM, fill=Y)
        self.dbftargetlist.pack(fill=BOTH, expand=Y)
        self.dbfjoinframe = Frame(self.dbfframe)
        self.dbfjoinframe.pack(side=RIGHT)
        self.dbfjoinlabel = Label(self.dbfjoinframe, text='join file')
        self.dbfjoinlabel.pack()
        self.dbfjoinyscroll = Scrollbar(self.dbfjoinframe, orient=VERTICAL)
        self.dbfjoinxscroll = Scrollbar(self.dbfjoinframe, orient=HORIZONTAL)
        self.dbfjoinlist = Listbox(self.dbfjoinframe, width=50, yscrollcommand=self.dbfjoinyscroll.set, xscrollcommand=self.dbfjoinxscroll.set, exportselection=0)
        self.dbfjoinyscroll.config(command=self.dbfjoinlist.yview)
        self.dbfjoinxscroll.config(command=self.dbfjoinlist.xview)
        self.dbfjoinyscroll.pack(side=RIGHT, fill=Y)
        self.dbfjoinxscroll.pack(side=BOTTOM, fill=Y)
        self.dbfjoinlist.pack(fill=BOTH, expand=Y)    

        self.configjoin = Button(frame, text="config selected", command=loadjoinchoices)
        self.configjoin.pack()

        self.targetjoinframe = Frame(frame)
        self.targetjoinframe.pack()
        self.targetframe = Frame(self.targetjoinframe)
        self.targetframe.pack(side=LEFT)
        self.targetlabel = Label(self.targetframe, text="target field")
        self.targetlabel.pack()
        self.target_yscroll = Scrollbar(self.targetframe, orient=VERTICAL)
        self.target_xscroll = Scrollbar(self.targetframe, orient=HORIZONTAL)
        self.target_list = Listbox(self.targetframe, width=50, yscrollcommand=self.target_yscroll.set, xscrollcommand=self.target_xscroll.set, exportselection=0)
        self.target_yscroll.config(command=self.target_list.yview)
        self.target_xscroll.config(command=self.target_list.xview)
        self.target_yscroll.pack(side=RIGHT, fill=Y)
        self.target_xscroll.pack(side=BOTTOM, fill=Y)
        self.target_list.pack(fill=BOTH, expand=1)

        self.joinframe = Frame(self.targetjoinframe)
        self.joinframe.pack(side=RIGHT)
        self.joinlabel = Label(self.joinframe, text="join field")
        self.joinlabel.pack()
        self.join_yscroll = Scrollbar(self.joinframe, orient=VERTICAL)
        self.join_xscroll = Scrollbar(self.joinframe, orient=HORIZONTAL)
        self.join_list = Listbox(self.joinframe, width=50, yscrollcommand=self.join_yscroll.set, xscrollcommand=self.join_xscroll.set, exportselection=0)
        self.join_yscroll.config(command=self.join_list.yview)
        self.join_xscroll.config(command=self.join_list.xview)
        self.join_yscroll.pack(side=RIGHT, fill=Y)
        self.join_xscroll.pack(side=BOTTOM, fill=Y)
        self.join_list.pack(fill=BOTH, expand=1)

        self.savejoin = Button(frame, text="save field selection", command=savejoinchoice)
        self.savejoin.pack()

        self.outputframe = Frame(frame)
        self.outputframe.pack()
        self.outputlabel = Label(self.outputframe, text='output fields')
        self.outputlabel.pack()

        self.outputlistframe = Frame(self.outputframe)
        self.outputlistframe.pack(side=LEFT)
        self.outputbuttonsframe = Frame(self.outputframe)
        self.outputbuttonsframe.pack(side=RIGHT)

        self.output_yscroll = Scrollbar(self.outputlistframe, orient=VERTICAL)
        self.output_xscroll = Scrollbar(self.outputlistframe, orient=HORIZONTAL)
        self.output_list = Listbox(self.outputlistframe, width=50, yscrollcommand=self.output_yscroll.set, xscrollcommand=self.output_xscroll.set, exportselection=0)
        self.output_yscroll.config(command=self.output_list.yview)
        self.output_xscroll.config(command=self.output_list.xview)
        self.output_yscroll.pack(side=RIGHT, fill=Y)
        self.output_xscroll.pack(side=BOTTOM, fill=Y)
        self.output_list.pack(fill=BOTH, expand=1)

        self.initoutput = Button(self.outputbuttonsframe, text='init output', command=initoutput)
        self.initoutput.pack()
        self.removeoutput = Button(self.outputbuttonsframe, text='del field', command=removeoutput)
        self.removeoutput.pack()
        self.moveup = Button(self.outputbuttonsframe, text='move up', command=moveup)
        self.moveup.pack()
        self.movedown = Button(self.outputbuttonsframe, text='move down', command=movedown)
        self.movedown.pack()

        self.outputbuttonframe = Frame(frame)
        self.outputbuttonframe.pack()
        self.configoutput = Button(self.outputbuttonframe, text='config selected field', command=configoutput)
        self.configoutput.pack(side=LEFT)
        self.saveoutput = Button(self.outputbuttonframe, text='save field', command=saveoutput)
        self.saveoutput.pack(side=LEFT)
        self.addoutput = Button(self.outputbuttonframe, text='add field', command=addoutput)
        self.addoutput.pack(side=LEFT)

        self.outputfieldframe = Frame(frame)
        self.outputfieldframe.pack()

        self.outputnamevalueframe = Frame(self.outputfieldframe)
        self.outputnamevalueframe.pack(side=LEFT)
        self.outputnameframe = Frame(self.outputnamevalueframe)
        self.outputnameframe.pack()
        self.outputvalueframe = Frame(self.outputnamevalueframe)
        self.outputvalueframe.pack()

        self.outputnamelabel = Label(self.outputnameframe, text='field name')
        self.outputnamelabel.pack(side=LEFT)
        self.outputname = Entry(self.outputnameframe)
        self.outputname.pack(side=RIGHT)
        self.outputvaluelabel = Label(self.outputvalueframe, text='value')
        self.outputvaluelabel.pack(side=LEFT)
        self.outputvalue = Text(self.outputvalueframe, width=30, height=4)
        self.outputvalue.pack(side=RIGHT)

        self.fieldattframe = Frame(self.outputfieldframe)
        self.fieldattframe.pack(side=RIGHT)
        self.fieldtypeframe = Frame(self.fieldattframe)
        self.fieldtypeframe.pack()
        self.fieldlenframe = Frame(self.fieldattframe)
        self.fieldlenframe.pack()
        self.fielddecframe = Frame(self.fieldattframe)
        self.fielddecframe.pack()

        self.fieldtypelabel = Label(self.fieldtypeframe, text='Type:')
        self.fieldtypelabel.pack(side=LEFT)
        self.fieldtype = Entry(self.fieldtypeframe)
        self.fieldtype.pack(side=RIGHT)
        self.fieldlenlabel = Label(self.fieldlenframe, text='Len:')
        self.fieldlenlabel.pack(side=LEFT)
        self.fieldlen = Entry(self.fieldlenframe)
        self.fieldlen.pack(side=RIGHT)
        self.fielddeclabel = Label(self.fielddecframe, text='Dec:')
        self.fielddeclabel.pack(side=LEFT)
        self.fielddec = Entry(self.fielddecframe)
        self.fielddec.pack(side=RIGHT)



        self.dojoin = Button(frame, text='execute join', command=dojoin)
        self.dojoin.pack()

root = Tk()
app = App(root)
root.mainloop()



