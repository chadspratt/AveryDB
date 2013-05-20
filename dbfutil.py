#! /usr/bin/python27

## fix the hack of casting all values to float on line 250 of fields.py

import re
from Tkinter import Tk
from gui import App
# used for writing dbf files
from dbfpy import dbf
#import combobox
from join import Join

# fields[filename] = [(fieldname, fieldtype, length, decimalplaces), ...]
fields = {}
target = Join()
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





# utility function used nowhere. untested
def printjoins(target):
    global joins
    print joins[target]
    for join in joins[target]:
        printjoins(join[1])    






# 'add field' button
def addoutput():
    global app
    global outputfields
    newfieldname = app.outputname.get().upper()
    newfieldvalue = app.outputvalue.get(1.0,END).strip()
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
        fieldindex = app.output_list.size() - 1
        app.output_list.selection_clear(0,END)
        app.output_list.selection_set(fieldindex)
        app.output_list.see(fieldindex)
        app.outputname.delete(0,END)
        app.outputvalue.delete(1.0,END)
        app.fieldtype.delete(0,END)
        app.fieldlen.delete(0,END)
        app.fielddec.delete(0,END)



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
        tempdbf = dbf.Dbf(joinfile, True)
        joinfiles[joinfile] = tempdbf

    # create output file. I think it will cleanly overwrite the file if it already exists
    outputfilename = app.outputfilename.get()
    newdbf = dbf.Dbf(outputfilename, new=True)
    # create fields
    outputfieldnames = app.output_list.get(0, END)
    for fieldname in outputfieldnames:
        curfield = outputfields[fieldname] 
        newdbf.addField((fieldname, curfield[1], int(curfield[2]), int(curfield[3])))

    # loop through target file
    i = 0
    recordcount = joinfiles[target].recordCount
    print 'total records:', recordcount
    while i < recordcount:
        print 'processing record: ', i, '%f%%'%(float(i)/recordcount*100)
        # process however many records before updating status
        for i in range(i, min(i+1000,recordcount)):
            # ['filename.fieldname'] = value
            inputvalues = {}
            targetrecord = joinfiles[target][i]
            for field in targetrecord.dbf.fieldNames:
                inputvalues[joinaliases[target]+'.'+field.upper()] = targetrecord[field]
            #print inputvalues

            # get the records that join with the current target record
            for targetfile in joinsdfs(target):
                # joins[localtarget] will give KeyError
                if targetfile in joins:
                    for join in joins[targetfile]:
                        targetfield = join[0]
                        joinfile = join[1]
                        joinfield = join[2]
                        joinindex = join[3]
                        # get the value to join on. this will not exist for secondary joins when the primary didn't join
                        if joinaliases[targetfile]+'.'+targetfield in inputvalues:
                            targetvalue = inputvalues[joinaliases[targetfile]+'.'+targetfield]
                            if targetvalue in joinindex:
                                joinrecord = joinfiles[joinfile][joinindex[targetvalue]] # this is completely opaque shit
                                for field in joinrecord.dbf.fieldNames:
                                    inputvalues[joinaliases[joinfile]+'.'+field.upper()] = joinrecord[field]
                            # will result in inputvalues[] misses later
                            else:
                                print joinfield+':', targetvalue, '- not found'

            # input records gathered, ready to assemble the output record
            newrec = newdbf.newRecord()
            for field in outputfieldnames:
                # this is where calculations will go
                fieldvalue = outputfields[field][0]
                # detect expressions by looking for '+-*/' operators
                # can't do '/' until i implement aliases instead of absolute paths
                if re.search('\+|-|==', fieldvalue):
                    #print 'original:',fieldvalue
                    fieldtype = outputfields[field][1]
                    # extract fields
                    fieldcomponents = re.findall('[^+\-=\n ]+', fieldvalue)
                    # number fields
                    if fieldtype == 'N' or fieldtype == 'F':
                        for component in fieldcomponents:
                            #print 'component:',component
                            #print 'inputvalues[component]:',inputvalues[component]
                            if component in inputvalues:
                                fieldvalue = re.sub(component, str(inputvalues[component]), fieldvalue)
                            else:
                                # this is a non-foolproof way of checking if we got here because of
                                # a failed join or if component is a literal like the number 2
                                # former: replace it with 0. latter, leave it alone
                                if component.split('.')[0] in joinaliases:
                                    # didn't get a join for this field. insert blank value
                                    fieldvalue = re.sub(component, '0', fieldvalue)
#                                fieldvalue = re.sub(component, component, fieldvalue)
                            #print 'component subbed:',fieldvalue
                        # check if it's an integer (vs a float)
                        #print 'subbed:',fieldvalue
                        if outputfields[field][3] == 0:
                            fieldvalue = int(eval(fieldvalue))
                        else:
                            fieldvalue = eval(fieldvalue)
                        #print 'final:',fieldvalue
                    # character fields
                    elif fieldtype == 'C':
                        for component in fieldcomponents:
                            # check if the component is a reference to a field or a literal
                            if component in inputvalues:
                                fieldvalue = re.sub(component, '"'+str(inputvalues[component])+'"', fieldvalue)
                            else:
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
                    if fieldvalue in inputvalues:
                        newrec[field] = inputvalues[fieldvalue]
                    else:
                        newrec[field] = blankvalue(outputfields[field])

            # newrec record is ready
            newrec.store()
            i = i + 1
    newdbf.close()
    print 'processing complete'
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
    if filename in joins:
        for join in joins[filename]:
            joinfile = join[1]
            joinfield = join[2]
            # check if it's already built. I don't think it's possible
            if len(join) == 4:
                continue
            print 'building index: '+joinfile+'\n'
            fileindex = {}
            tempdbf = dbf.Dbf(joinfile, readOnly=True)
            i = 0
            for rec in tempdbf:
                # store the joinfield and the index of the record
                # this doesn't check for duplicates since we can only use
                # one record when doing a join. if more than one, the last will be used
                fileindex[rec[joinfield]] = i
                i += 1
            # storing the index IN joins is the easiest way to store an index for any
            # possible join that's been set. a.b->b.c, a.b->b.d; a.b->b.c, a.b->c.d
            # potential duplication of effort, but it'd be unusual and hard to optimise out
            join.append(fileindex)
            # recursive call to build indexes of files joined to joinfile
            buildindexes(joinfile)
#        # save the index, just in case it's needed later. wish this worked
#           pickle.dump(fileindex, filename+'.jif')

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



