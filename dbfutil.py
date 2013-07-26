#!/usr/bin/python
"""This utility provides an easy interface for working with database files.

To create a new, empty file, click the refresh button on the middle toolbar to
initialize the list. Then click the + to add fields you can define.

To modify an existing file, load the file, click the refresh button, and then
modify the fields.

To join and modify multiple files, load the files, configure how they will join
together, click refresh to load the fields, then adjust the fields.
"""
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
# callback functions for the gui
import gtk
import time
import random
import sqlite3

import gui
import filemanager
import tablemanager
import joinmanager
import outputmanager
import calculator


class DBFUtil(object):

    """Main class, links GUI to the back end and also orchestrates a bit."""

    def __init__(self):
        self.gui = gui.creategui(self)
        self.files = filemanager.FileManager()
        self.tables = tablemanager.TableManager()
        self.joins = joinmanager.JoinManager()
        self.outputs = outputmanager.OutputManager()
        self.calc = calculator.Calculator()

        # fake threading helpers
        self.joinaborted = False
        self.executejoinqueued = False
        self.tasks_to_process = []
        self.taskinprogress = False

        # indices of the records used for showing sample output
        self.sampleindices = []

        # needs to be last because control goes to the gui once it's called
        gui.startgui()

    def quitprogram(self, _widget, _data=None):
        """Close open files before closing the program."""
        for datafile in self.files:
            datafile.close()
        gtk.main_quit()

    def addfile(self, _widget, _data=None):
        """Open a new file for joining to the target."""
        addfiledialog = self.gui.filedialog(self.files.filetypes)
        response = addfiledialog.run()
        # check that a file was selected
        if response == gtk.RESPONSE_OK:
            newfilename = addfiledialog.get_filename()
            newfilealias = self.files.addfile(newfilename)
            sqlconverter = self.tables.addtable(newfilealias,
                                                self.files[newfilealias])
            self.queuetask(('sqlite', (newfilealias, sqlconverter)))
            # add to the file list
            aliaslist = self.gui['aliaslist']
            newrow = aliaslist.append([newfilealias])

            # set as target if no target is set
            if self.joins.gettarget() == '':
                self.joins.settarget(newfilealias)
                self.gui['targetcombo'].set_active_iter(newrow)
        addfiledialog.destroy()
        self.processtasks()

    def removefile(self, _widget, _data=None):
        """Close a file and remove all joins that depend on it."""
        # get the selection from the list of files
        selection = self.gui['fileview'].get_selection()
        (aliaslist, selectedpath) = selection.get_selected()
        if selectedpath:
            filealias = aliaslist.get_value(selectedpath, 0)

            # remove joins that depend on the file
            self.joins.removealias(filealias)
            # remove the file
            self.files.removealias(filealias)

            # remove from gui list and from the fields dictionary
            aliaslist.remove(selectedpath)
            selection.unselect_all()

            # Update the target if the old one was removed
            if self.joins.gettarget() == '':
                if len(aliaslist) > 0:
                    newtargetiter = aliaslist.get_iter(0)
                    self.gui['targetcombo'].set_active_iter(newtargetiter)

            # refresh join lists in case the removed file was in one of them
            self.refreshjoinlists()
            # want to check outputs for fields that now have broken references.
            # if not remove them, show some sort of alert

    def changetarget(self, _widget, _data=None):
        """Set an open file as the main target for joining."""
        newtarget = self.gui['targetcombo'].get_active_text()
        self.joins.settarget(newtarget)
        self.refreshjoinlists()

    def refreshjoinlists(self):
        """Update when a join is added/removed or main target is changed."""
        # refresh the target alias combobox list
        targetaliaslist = self.gui['targetaliaslist']
        targetcombo = self.gui['targetaliascombo']
        # save the current selection
        activealias = targetcombo.get_active_text()
        # refresh the list of valid targets
        targetaliaslist.clear()
        for alias in self.joins.joinedaliases:
            targetaliaslist.append([alias])
        # reselect the previous selection, if it's still there
        for row in targetaliaslist:
            if activealias in row:
                targetcombo.set_active_iter(row.iter)

        # refresh the list of joins
        self.gui['jointree'].clear()
        # add the main target
        targetalias = self.joins.gettarget()
        targetiter = self.gui['jointree'].append(None, [targetalias,
                                                        '', ''])
        # add all the joins
        for childjoin in self.joins[targetalias]:
            self.rebuildjointree(targetiter, childjoin)
        self.gui['joinview'].expand_all()

    # recursive function to fill jointree from
    def rebuildjointree(self, parentiter, join):
        """Update the join tree store by reading from the JoinManager."""
        newparent = self.gui['jointree'].append(parentiter, [join.joinalias,
                                                             join.joinfield,
                                                             join.targetfield])
        for childjoin in self.joins[join.joinalias]:
            self.rebuildjointree(newparent, childjoin)

    def loadjoinfields(self, _widget, _data=None):
        """Update the join field combo when the join alias combo changes."""
        # clear the liststore and add the new items
        joinfieldlist = self.gui['joinfieldlist']
        joinfieldlist.clear()

        # get the selected file alias
        joinalias = self.gui['joinaliascombo'].get_active_text()
        if joinalias is not None:
            joinfields = self.files[joinalias].getfields()
            for joinfield in joinfields:
                joinfieldlist.append([joinfield.name])

    def loadtargetfields(self, _widget, _data=None):
        """Update target field combo when target alias combo changes."""
        # clear the liststore and add the new items
        targetfieldlist = self.gui['targetfieldlist']
        targetfieldlist.clear()

        # get the selected file alias
        targetalias = self.gui['targetaliascombo'].get_active_text()
        if targetalias is not None:
            targetfields = self.files[targetalias].getfields()
            for targetfield in targetfields:
                targetfieldlist.append([targetfield.name])

    def matchtargetfield(self, widget, _data=None):
        """Sets the target field if there is one with a matching name."""
        value = widget.get_active_text()
        targetfieldlist = self.gui['targetfieldlist']
        for row in targetfieldlist:
            if value in row:
                self.gui['targetfieldcombo'].set_active_iter(row.iter)
                return

    # 'apply' join choice button
    def addjoin(self, _widget, _data=None):
        """Save join using the selected fields in the gui."""
        # get combobox selections
        joinalias = self.gui['joinaliascombo'].get_active_text()
        joinfield = self.gui['joinfieldcombo'].get_active_text()
        targetalias = self.gui['targetaliascombo'].get_active_text()
        targetfield = self.gui['targetfieldcombo'].get_active_text()

        if joinfield is not None and targetfield is not None:
            # save to joins
            result = self.joins.addjoin(joinalias, joinfield,
                                        targetalias, targetfield)
            # check if the result is an error message
            if type(result) == str:
                self.gui.messagedialog(result)
            # otherwise result is the new Join
            else:
                self.refreshjoinlists()
                self.queuetask(('index', result))
                self.queuetask(('sample', None))
                self.processtasks()

    def queuetask(self, task=None):
        if task:
            self.tasks_to_process.append(task)

    def processtasks(self, task=None):
        """Build indices and update sample output in the "background"."""
        if task:
            self.tasks_to_process.append(task)
        if not self.taskinprogress:
            self.taskinprogress = True
            while self.tasks_to_process:
                tasktype, taskdata = self.tasks_to_process.pop(0)
                if tasktype == 'index':
                    self.buildindex(taskdata)
                    self.updatesample()
                elif tasktype == 'sample':
                    self.updatesample()
                elif tasktype == 'sqlite':
                    filealias, dataconverter = taskdata
                    self.converttosql(filealias, dataconverter)
        # This has to go after indexing too. The execute toggle button can be
        # used to cancel the output while the indices are still building.
            if self.executejoinqueued:
                self.gui['executejointoggle'].set_active(False)
                self.executejoin(None)
            self.taskinprogress = False

    def queueexecution(self, widget, _data=None):
        """Signal the program to start once background processing is done."""
        self.executejoinqueued = widget.get_active()
        self.processtasks()

    def buildindex(self, join):
        """Build index in the background"""
        indexalias = join.joinalias
        indexfield = join.joinfield
        self.tables.buildsqlindex(indexalias, indexfield)

    def converttosql(self, filealias, dataconverter):
        progresstext = 'Converting to sqlite: ' + filealias
        self.gui.setprogress(0, progresstext)
        # Run the generator until it's finished. It yields % progress.
        for progress in dataconverter:
            # this progress update lets the GUI function
            self.gui.setprogress(progress, progresstext, lockgui=False)
        self.gui.setprogress(0, '')

    def removejoin(self, _widget, _data=None):
        """Removes the selected joins and any child joins dependent on it."""
        selection = self.gui['joinview'].get_selection()
        (outputlist, selectedrow) = selection.get_selected()
        joinalias = outputlist[selectedrow][0]
        self.joins.removealias(joinalias)
        self.refreshjoinlists()

    def changeoutputformat(self, _widget, _data=None):
        """Converts any configured output to the new output format."""
        typeiter = self.gui['outputtypecombo'].get_active_iter()
        newtype = self.gui['outputtypelist'][typeiter]
        if newtype is not None and newtype != self.outputs.getoutputtype():
            self.outputs.setoutputtype(newtype)

    # populate the list of output fields with all the input fields
    def initoutput(self, _widget, _data=None):
        """Populate the list view of output fields and the OutputManager."""
        fieldattributes = self.outputs.fieldattr
        self.gui.replacecolumns('outputlist', 'outputview', fieldattributes)
        outputlist = self.gui['outputlist']
        # Field calculator window setup
        self.gui['calcoutputfieldcombo'].set_model(outputlist)
        inputlist = self.gui['inputlist']
        inputlist.clear()

        self.outputs.clear()
        # check that a target file has been opened
        if self.joins.targetalias:
            # add all the fields from the target and everything joined to it
            for filealias in self.joins.getjoinedaliases():
                for field in self.files[filealias].getfields():
                    newfield = self.outputs.addfield(field, filealias)
                    outputlist.append(newfield.getattributelist())
                    inputlist.append([newfield['value']])
                    # XXX not the ideal place for this, but most convenient
                    self.calc.addblankvalue(filealias, field)
        self.processtasks(('sample', None))

    def updatefieldattribute(self, _cell, row, new_value, outputlist, column):
        """Update data when an outputview cell is edited."""
        # Update output manager if the field name was changed
        if column == 0:
            self.outputs.updatename(row, new_value)
        # update the view
        outputlist[row][column] = new_value
        # update the field
        self.outputs[row][column] = new_value
        # update the output sample
        self.processtasks(('sample', None))

    # 'add field' button
    def addoutput(self, _widget, _data=None):
        """Add a new field after the last selected. Append if none selected."""
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
        newfield = self.outputs.addnewfield(fieldindex=insertindex)
        outputlist.insert(insertindex, newfield.getattributelist())

        selection.unselect_all()
        selection.select_path(insertindex)
        self.gui['outputview'].scroll_to_cell(insertindex)
        self.processtasks(('sample', None))

    # 'save field' button
    def copyoutput(self, _widget, _data=None):
        """Create a copy of the selected field[s]."""
        selection = self.gui['outputview'].get_selection()
        # (model, [(path0,), (path1,), ...])
        (outputlist, selectedrows) = selection.get_selected_rows()
        if selectedrows:
            selection.unselect_all()
            # reverse it so indices won't get shifted as items are added
            selectedrows.reverse()
            for row in selectedrows:
                insertindex = row[0] + 1
                fieldcopy = self.outputs[row[0]].copy()
                self.outputs.addfield(fieldcopy, fieldindex=insertindex)
                outputlist.insert(insertindex, fieldcopy.getattributelist())
                selection.select_path(insertindex)
            self.gui['outputview'].scroll_to_cell(insertindex)
        self.processtasks(('sample', None))

    # 'del field' button
    def removeoutput(self, _widget, _data=None):
        """Remove fields from the output."""
        selection = self.gui['outputview'].get_selection()
        # (model, [(path0,), (path1,), ...])
        (outputlist, selectedrows) = selection.get_selected_rows()
        if selectedrows:
            selection.unselect_all()
            # reverse it so indices won't get shifted as items are removed
            selectedrows.reverse()
            for row in selectedrows:
                outputlist.remove(outputlist.get_iter(row))
                self.outputs.removefield(row[0])
        self.processtasks(('sample', None))

    # 'move up' button
    def movetop(self, _widget, _data=None):
        """Move the selected items to the top of the list of output fields."""
        selection = self.gui['outputview'].get_selection()
        # (model, [(path0,), (path1,), ...])
        (outputlist, selectedrows) = selection.get_selected_rows()
        if selectedrows:
            selectedcount = selection.count_selected_rows()
            selection.unselect_all()
            moveindex = 0
            for row in selectedrows:
                outputlist.move_before(outputlist.get_iter(row),
                                       outputlist.get_iter(moveindex))
                self.outputs.movefield(row[0], moveindex)
                moveindex += 1
            selection.select_range(0, selectedcount - 1)
            self.gui['outputview'].scroll_to_cell(0)
        self.processtasks(('sample', None))

    # 'move up' button
    def moveup(self, _widget, _data=None):
        """Move the selected items up in the list of output fields."""
        selection = self.gui['outputview'].get_selection()
        # (model, [(path0,), (path1,), ...])
        (outputlist, selectedrows) = selection.get_selected_rows()
        if selectedrows:
            selection.unselect_all()
            # don't move items past end of the list, or other selected items
            startindex = 0
            for row in selectedrows:
                # check if the field is already as far up as possible
                if row[0] > startindex:
                    outputlist.swap(outputlist.get_iter(row),
                                    outputlist.get_iter(row[0] - 1))
                    self.outputs.movefield(row[0], row[0] - 1)
                    selection.select_path(row[0] - 1)
                else:
                    selection.select_path(row[0])
                startindex += 1
            self.gui['outputview'].scroll_to_cell(max(selectedrows[0][0] - 1,
                                                      0))
        self.processtasks(('sample', None))

    # 'move down' button
    def movedown(self, _widget, _data=None):
        """Move the selected items down in the list of output fields."""
        selection = self.gui['outputview'].get_selection()
        # (model, [(path0,), (path1,), ...])
        (outputlist, selectedrows) = selection.get_selected_rows()
        if selectedrows:
            selectedrows.reverse()
            selection.unselect_all()
            # don't move items past end of the list, or other selected items
            endindex = len(self.outputs.outputfields) - 1
            # scroll the view now since the right values to use are available
            self.gui['outputview'].scroll_to_cell(min(selectedrows[0][0] + 1,
                                                      endindex))
            for row in selectedrows:
                # check if the field is already as far down as possible
                if row[0] < endindex:
                    outputlist.swap(outputlist.get_iter(row),
                                    outputlist.get_iter(row[0] + 1))
                    self.outputs.movefield(row[0], row[0] + 1)
                    selection.select_path(row[0] + 1)
                else:
                    selection.select_path(row[0])
                endindex -= 1
        self.processtasks(('sample', None))

    # 'move down' button
    def movebottom(self, _widget, _data=None):
        """Move the selected items to the end of the list of output fields."""
        selection = self.gui['outputview'].get_selection()
        # (model, [(path0,), (path1,), ...])
        (outputlist, selectedrows) = selection.get_selected_rows()
        if selectedrows:
            selectedrows.reverse()
            selection.unselect_all()
            endindex = len(self.outputs.outputfields) - 1
            moveindex = endindex
            for row in selectedrows:
                outputlist.move_after(outputlist.get_iter(row),
                                      outputlist.get_iter(moveindex))
                self.outputs.movefield(row[0], moveindex)
                moveindex -= 1
            selection.select_range(moveindex + 1, endindex)
            self.gui['outputview'].scroll_to_cell(endindex)
        self.processtasks(('sample', None))

    def abortjoin(self, _widget, _data=None):
        """Set a signal for the output to abort."""
        self.joinaborted = True

    # 'execute join' button
    def executejoin(self, _widget, _data=None):
        """Execute the join and output the result"""
        if len(self.outputs) == 0:
            return

        targetalias = self.joins.gettarget()
        targetfile = self.files[targetalias]

        # create the output file
        outputfilename = (self.gui['outputfilenameentry'].get_text() +
                          self.gui['outputtypecombo'].get_active_text())
        outputfile = self.files.openoutputfile(outputfilename)

        # create fields
        outputfields = [self.outputs[fn] for fn in self.outputs.outputorder]
        outputfile.setfields(outputfields)

        self.calc.clear()
        for field in self.outputs:
            self.calc.createoutputfunc(field)

        stopbutton = self.gui['stopjoinbutton']
        stopbutton.set_sensitive(True)
        self.joinaborted = False

        # sqlite setup
        fieldnames = self.files.getallfields()
        joinquery = self.joins.getquery()
        print joinquery
        # open the database
        conn = sqlite3.connect('temp.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # create the table
        cur.execute(joinquery)

        # loop through target file
        i = 0
        recordcount = targetfile.getrecordcount()
        print 'total records:', recordcount
        starttime = time.time()
        while i < recordcount:
            # calculate and update the progress
            progress = float(i + 1) / recordcount
            timeelapsed = time.time() - starttime
            timetotal = timeelapsed / progress
            timeremaining = timetotal - timeelapsed
            timeend = time.localtime(starttime + timetotal)
            progresstext = ' '.join(['%f%%' % (progress * 100), '-',
                                     'Time Elapsed/Remaining/Total/ETA - ',
                                     self.timetostring(timeelapsed), '/',
                                     self.timetostring(timeremaining), '/',
                                     self.timetostring(timetotal),  '/',
                                     time.strftime('%I:%M %p', timeend)])
            print progresstext
            self.gui.setprogress(progress, progresstext)
            if self.joinaborted:
                self.gui.setprogress(0, 'Output aborted')
                stopbutton.set_sensitive(False)
                outputfile.close()
                return

            # process however many records before updating progress
            for i in range(i, min(i + 1000, recordcount)):
                # inputvalues[filealias_fieldname] = value
                inputvalues = cur.fetchone()
                newrec = {}
                outputvalues = self.calc.calculateoutput(inputvalues)
                for fieldname, fieldvalue in outputvalues:
                    newrec[fieldname] = fieldvalue

                outputfile.addrecord(newrec)

                i = i + 1

        outputfile.close()
        print 'processing complete'
        self.gui.setprogress(1, 'Output complete')

    def updatesample(self, samplesize=10):
        """Update the sample of output records"""
        if len(self.outputs) == 0:
            return

        targetalias = self.joins.gettarget()
        targetfile = self.files[targetalias]

        sampleoutputfields = self.outputs.outputorder
        self.gui.replacecolumns('sampleoutputlist', 'sampleoutputview',
                                sampleoutputfields)

        self.calc.clear()
        for fieldname in sampleoutputfields:
            self.calc.createoutputfunc(self.outputs[fieldname])

        # generate a selection of records to use
        if len(self.sampleindices) != samplesize:
            recordcount = targetfile.getrecordcount()
            self.sampleindices = []
            while len(self.sampleindices) < samplesize:
                newindex = random.randint(0, recordcount)
                if newindex not in self.sampleindices:
                    self.sampleindices.append(newindex)

        # sqlite setup
        fieldnames = self.files.getallfields()
        joinquery = self.joins.getquery(self.sampleindices)

        # open the database
        conn = sqlite3.connect('temp.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # create the table
        cur.execute(joinquery)

        # process however many records before updating progress
        for sampleindex in self.sampleindices:
            inputvalues = cur.fetchone()
            outputrecord = []
            outputvalues = self.calc.calculateoutput(inputvalues)
            for _fieldname, fieldvalue in outputvalues:
                outputrecord.append(fieldvalue)
            self.gui['sampleoutputlist'].append(outputrecord)

    @classmethod
    def timetostring(cls, inputtime):
        """Convert a number of seconds into a human readable duration."""
        outputstr = ''
        inputtime = int(inputtime)
        seconds = inputtime % 60
        if inputtime > seconds:
            inputtime /= 60
            minutes = inputtime % 60
            if inputtime > minutes:
                inputtime /= 60
                hours = inputtime % 24
                if inputtime > hours:
                    days = inputtime / 24
                    outputstr += str(days) + 'd'
                outputstr += str(hours) + 'h'
            outputstr += str(minutes) + 'm'
        outputstr += str(seconds) + 's'
        return outputstr

    def showcalculator(self, _widget, _data=None):
        """Show the calculator window when the Calc button is clicked."""
        # get the selected row from the output list
        selection = self.gui['outputview'].get_selection()
        # (model, [(path0,), (path1,), ...])
        (outputlist, selectedrows) = selection.get_selected_rows()
        if selectedrows:
            lastindex = selectedrows[-1]
            lastfield = outputlist.get_value(outputlist.get_iter(lastindex), 0)
            # select the field in the calc window
#            outputlist = self.gui['outputlist']
            for row in outputlist:
                if lastfield in row:
                    # this will trigger changecalcfield
                    self.gui['calcoutputfieldcombo'].set_active_iter(row.iter)
                    break
#        elif outputlist.get_iter_first():
#            self.gui['calcoutputfieldcombo'].set_active(-1)

        # init the list of available libraries in the combobox
        librarylist = self.gui['librarylist']
        librarylist.clear()
        for libname in self.calc.getlibs():
            if not libname.startswith('_'):
                librarylist.append([libname])
        # display the calculator window
        self.gui['calcwindow'].show_all()

    def hidecalculator(self, _widget, _data=None):
        """Hide the calculator window in response to a destroy event."""
        self.gui['calcwindow'].hide()
        return True

    def changecalcfield(self, widget, _data=None):
        """Update calc value box when the calc output field combo changes."""
        newfield = widget.get_active_text()
        if newfield is not None:
            newvalue = self.outputs[newfield]['value']
            self.gui['calcvaluelabel'].set_text(newvalue[1:-1] + ' =')
            valuebuffer = self.gui['calcvalueview'].get_buffer()
            valuebuffer.set_text(newvalue)

    def loadfunctionlist(self, widget, _data=None):
        """List the functions when a new library is entered or selected."""
        newlib = widget.get_active_text()
        functionlist = self.gui['functionlist']
        functionlist.clear()
        if newlib:
            try:
                for funcname, funcdoc in self.calc.getfuncs(newlib):
                    functionlist.append([funcname, funcdoc])
            except ImportError:
                # this will get called for every letter typed into the box
                # many failed imports are to be expected
                pass

    def insertfieldvalue(self, _widget, path, _view_column):
        """Insert a double-clicked value where the cursor or highlight is."""
        inputlist = self.gui['inputlist']
        insertvalue = inputlist.get_value(inputlist.get_iter(path), 0)
        valuebuffer = self.gui['calcvalueview'].get_buffer()
        # if something is highlighted, delete it
        valuebuffer.delete_selection(True, True)
        # insert the double-clicked value
        valuebuffer.insert_at_cursor(insertvalue)
        self.gui['calcvalueview'].grab_focus()

    def insertfunccall(self, _widget, path, _view_column):
        """Insert a function call at the cursor or around highlighted text."""
        modulename = self.gui['calclibrarycomboentry'].get_active_text()
        # Get the function name
        functionlist = self.gui['functionlist']
        functionname = functionlist.get_value(functionlist.get_iter(path), 0)
        # Append the module name for everything not in these two modules
        if modulename not in ['builtins', 'default']:
            functionname = modulename + '.' + functionname
        # Get any selected text
        valuebuffer = self.gui['calcvalueview'].get_buffer()
        if valuebuffer.get_has_selection():
            selectionbounds = valuebuffer.get_selection_bounds()
            selectedtext = valuebuffer.get_text(selectionbounds[0],
                                                selectionbounds[1])
        else:
            selectedtext = ''
        # Delete any selected text and reinsert it wrapped in the function
        valuebuffer.delete_selection(True, True)
        inserttext = functionname + '(' + selectedtext + ')'
        valuebuffer.insert_at_cursor(inserttext)
        self.gui['calcvalueview'].grab_focus()

    def savecalcvalue(self, _widget, _data=None):
        """Save the value back to the field."""
        outputcombo = self.gui['calcoutputfieldcombo']
        fieldname = outputcombo.get_active_text()
        valuebuffer = self.gui['calcvalueview'].get_buffer()
        fieldvalue = valuebuffer.get_text(valuebuffer.get_start_iter(),
                                          valuebuffer.get_end_iter())
        # update the value in the output manager and the output table
        self.outputs[fieldname]['value'] = fieldvalue
        self.gui['outputlist'][outputcombo.get_active_iter()][-1] = fieldvalue
        self.processtasks(('sample', None))

    # XXX dragging dropping columns to reorder attributes, incomplete
    def reordercols(self, widget):
        """Update the column order when they are drug around in the GUI."""
        columns = widget.get_columns()
        columnnames = [col.get_title() for col in columns]
        outputlist = self.gui['outputlist']
        for i in range(len(columnnames)):
            pass

    def showfunceditor(self, _widget, _data=None):
        """Initialize and show the function editor window."""
        # get the selected lib from the combobox
        selectedlibname = self.gui['calclibrarycomboentry'].get_active_text()
        # get the selected function name from the function list
        selection = self.gui['calcfunctionview'].get_selection()
        (functionlist, selectedpath) = selection.get_selected()
        if selectedpath:
            selectedfuncname = functionlist.get_value(selectedpath, 0)
        else:
            selectedfuncname = None
        customlibs = self.calc.getcustomlibs()
        customlibrarylist = self.gui['customlibrarylist']
        customlibrarylist.clear()
        for customlib in customlibs:
            rowiter = customlibrarylist.append([customlib])
            if customlib == selectedlibname:
                # this would call changefunclibrary but on init it needs
                # to use the selected function from the calc window
                funclibcombo = self.gui['funclibrarycombo']
                funclibcombo.handler_block_by_func(self.loadlibraryfunctions)
                funclibcombo.set_active_iter(rowiter)
                funclibcombo.handler_unblock_by_func(self.loadlibraryfunctions)
        # if the lib was custom, load its functions
        if self.gui['funclibrarycombo'].get_active_iter():
            libfunctions = self.calc.getfuncs(selectedlibname)
            customfunctionlist = self.gui['customfunctionlist']
            customfunctionlist.clear()
            for libname, _libdoc in libfunctions:
                rowiter = customfunctionlist.append([libname])
                if libname == selectedfuncname:
                    # this will trigger changefuncfunction to init the text
                    self.gui['funcfunctioncombo'].set_active_iter(rowiter)
        self.gui['funcwindow'].show_all()

    def hidefunceditor(self, _widget, _data=None):
        """Hide the function editor in response to a destroy event."""
        self.gui['funcwindow'].hide()
        return True

    def getlibraryname(self, _widget, _data=None):
        """Show a dialog to ask for a new function name."""
        self.gui['newlibentry'].set_text('')
        self.gui['newlibdialog'].show()

    def createlibrary(self, _widget, _data=None):
        """Create a new library file with the user-provided library name."""
        libname = self.gui['newlibentry'].get_text()
        self.calc.createlib(libname)
        self.gui['newlibdialog'].hide()
        # refresh the different library lists
        self.showfunceditor(None)
        self.showcalculator(None)

    def cancelcreatelibrary(self, _widget, _data=None):
        """Hide the library name dialog without creating anything."""
        self.gui['newlibdialog'].hide()

    def loadlibraryfunctions(self, widget, _data=None):
        """Update calc value box when the calc output field combo changes."""
        libname = widget.get_active_text()
        if libname is not None:
            libfunctions = self.calc.getfuncs(libname)
            customfunctionlist = self.gui['customfunctionlist']
            customfunctionlist.clear()
            for funcname, _funcdoc in libfunctions:
                customfunctionlist.append([funcname])

    def loadfunctiontext(self, _widget, _data=None):
        """Update calc value box when the calc output field combo changes."""
        libname = self.gui['funclibrarycombo'].get_active_text()
        funcname = self.gui['funcfunctioncombo'].get_active_text()
        if funcname:
            functext = self.calc.getfunctext(libname, funcname)
            valuebuffer = self.gui['funceditingtextview'].get_buffer()
            valuebuffer.set_text(functext)

    def savefunction(self, _widget, _data=None):
        """Write the contents of the editor to the selected library.

        Whatever is in the text editing area will be written to the library
        selected in the combobox at the top of the function editor window.
        If the function alread exists it will be overwritten. If the input is
        not a function it will probably cause problems and the file will need
        to be opened in an external editor and cleaned."""
        libname = self.gui['funclibrarycombo'].get_active_text()
        funcbuffer = self.gui['funceditingtextview'].get_buffer()
        functext = funcbuffer.get_text(funcbuffer.get_start_iter(),
                                       funcbuffer.get_end_iter())
        self.calc.writefunctext(libname, functext)
        self.loadfunctiontext(None)

    def saveclosefunction(self, _widget, _data=None):
        """Save the contents of the editor and close the function editor."""
        self.savefunction(None)
        self.hidefunceditor(None)

DBFUTIL = DBFUtil()
