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

import gui
import filemanager
import joinmanager
import outputmanager
import calculator
#import joinfile #imported via gui via filemanager


class DBFUtil(object):

    """Main class, links GUI to the back end and also orchestrates a bit."""

    def __init__(self):
        self.gui = gui.creategui(self)
        self.files = filemanager.FileManager()
        self.joins = joinmanager.JoinManager()
        self.outputs = outputmanager.OutputManager()
        self.calc = calculator.Calculator()

        # fake threading helpers
        self.joinaborted = False
        self.indicestobuild = []
        self.indexinprogress = False

        # needs to be last because control goes to the gui once it's called
        gui.startgui()

    def quitprogram(self, _widget, _data=None):
        """Close open files before closing the program."""
        for joinfile in self.files:
            joinfile.close()
        gtk.main_quit()

    def addfile(self, _widget, _data=None):
        """Open a new file for joining to the target."""
        addfiledialog = self.gui.filedialog(self.files.filetypes)
        response = addfiledialog.run()
        # check that a file was selected
        if response == gtk.RESPONSE_OK:
            newfilename = addfiledialog.get_filename()
            newfilealias = self.files.addfile(newfilename)
            # add to the file list
            aliaslist = self.gui['aliaslist']
            newrow = aliaslist.append([newfilealias])

            # set as target if no target is set
            if self.joins.gettarget() == '':
                self.joins.settarget(newfilealias)
                self.gui['targetcombo'].set_active_iter(newrow)
        addfiledialog.destroy()

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

    def targetchanged(self, _widget, _data=None):
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

    def joinaliaschanged(self, _widget, _data=None):
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

    def targetaliaschanged(self, _widget, _data=None):
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

    def joinfieldchanged(self, widget, _data=None):
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
                self.buildindices(result)

    def buildindices(self, join):
        """Build indices in the background as joins are added."""
        self.indicestobuild.append(join)
        # Check if an index is already being built
        if not self.indexinprogress:
            self.indexinprogress = True
            while self.indicestobuild:
                nextjoin = self.indicestobuild.pop(0)
                indexfile = nextjoin.joinalias
                indexfield = nextjoin.joinfield
                progresstext = ' '.join(['Building index:', indexfile,
                                         '-', indexfield])
                self.gui.setprogress(0, progresstext)
                # Create a generator that calculates some records then yields
                indexbuilder = self.files[indexfile].buildindex(indexfield)
                # Run the generator until it's finished. It yields % progress.
                for progress in indexbuilder:
                    # this progress update lets the GUI function
                    self.gui.setprogress(progress,
                                         (str(int(progress * 100)) + '% - '
                                         + progresstext),
                                         lockgui=False)
            self.indexinprogress = False
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

        self.outputs.clear()
        # check that a target file has been opened
        if self.joins.targetalias:
            # add all the fields from the target and everything joined to it
            for filealias in self.joins.getjoinedaliases():
                for field in self.files[filealias].getfields():
                    newfield = self.outputs.addfield(field, filealias)
                    outputlist.append(newfield.getattributelist())
                    # not the ideal place for this, but most convenient
                    self.calc.addblankvalue(filealias, field)

    def updatefieldattribute(self, _cell, row, new_value, outputlist, column):
        """Update data when an outputview cell is edited."""
        # If the field name was updated, change the user input if necessary to
        # make it unique.
        # If it's in the field name column
        if column == 0:
            # and the field name is already in use
            if new_value in self.outputs:
                # by a different field than the one being edited
                if self.outputs[row]['name'].upper() != new_value.upper():
                    # then modify new_value to be unique
                    new_value = self.outputs.getuniquename(new_value)
        outputlist[row][column] = new_value
        self.outputs[row][column] = new_value

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

    def abortjoin(self, _widget, _data=None):
        """Set a signal for the output to abort."""
        self.joinaborted = True

    # 'execute join' button
    def executejoin(self, _widget, _data=None):
        """Execute the join and output the result"""
        if len(self.outputs) == 0:
            return
        # XXX it would be better to have it auto start when indexing is done
        if self.indexinprogress:
            return

        targetalias = self.joins.gettarget()
        targetfile = self.files[targetalias]

        # create the output file
        outputfilename = (self.gui['outputfilenameentry'].get_text() +
                          self.gui['outputtypecombo'].get_active_text())
        outputfile = self.files.openoutputfile(outputfilename)

        # create fields
        for fieldname in self.outputs.outputorder:
            outputfile.addfield(self.outputs[fieldname])

        for field in self.outputs:
            self.calc.createoutputfunc(field)

        stopbutton = self.gui['stopjoinbutton']
        stopbutton.set_sensitive(True)
        self.joinaborted = False
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
                # inputvalues[filealias][fieldname] = value
                inputvalues = {}
                inputvalues[targetalias] = targetfile[i]

                for joinlist in self.joins:
                    for join in joinlist:
                        # no good way to make this line shorter
                        joinvalue = inputvalues[join.targetalias][join.targetfield]
                        joinfile = self.files[join.joinalias]
                        # Will be None if there isn't a matching record to join
                        temprecord = joinfile.getjoinrecord(join.joinfield,
                                                            joinvalue)
                        if temprecord is None:
                            print join.joinfield + ':', joinvalue, ' not found'
                        else:
                            inputvalues[join.joinalias] = temprecord

                newrec = {}
                outputvalues = self.calc.calculateoutput(inputvalues)
                for fieldname, fieldvalue in outputvalues:
                    newrec[fieldname] = fieldvalue

                outputfile.addrecord(newrec)

                i = i + 1

        outputfile.close()
        print 'processing complete'
        self.gui.setprogress(1, 'Output complete')

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

DBFUTIL = DBFUtil()
