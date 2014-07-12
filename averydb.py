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
import re
import os

import gui
import filemanager
import joinmanager
import outputmanager
import optionsmanager
import calculator
import table  # for NeedTableError

# event handlers
from gui_files import GUI_Files
from gui_joinconfig import GUI_JoinConfig
from gui_fieldtoolbar import GUI_FieldToolbar
from gui_fieldview import GUI_FieldView
from gui_calc import GUI_Calc
from gui_functioneditor import GUI_FunctionEditor
from gui_keyboard import GUI_Keyboard
from gui_options import GUI_Options
from backgroundtasks import BackgroundTasks


class AveryDB(GUI_Files, GUI_JoinConfig, GUI_FieldToolbar, GUI_FieldView,
              GUI_Calc, GUI_FunctionEditor, GUI_Keyboard, GUI_Options,
              BackgroundTasks):

    """Main class, links GUI to the back end and also orchestrates a bit."""

    def __init__(self):
        # main program components
        self.gui = gui.creategui(self)
        self.files = filemanager.FileManager()
        self.joins = joinmanager.JoinManager()
        self.outputs = outputmanager.OutputManager()
        self.options = optionsmanager.OptionsManager()
        self.calc = calculator.Calculator()

        # load options
        self.options.loadoptions()

        # fake threading helpers
        self.joinaborted = False
        self.executejoinqueued = False
        self.tasks_to_process = []
        self.taskinprogress = False

        # records used for showing sample output
        self.samplerecords = []

        # clear the sqlite database that's used to store all the data
        sqlitefile = open('temp.db', 'w')
        sqlitefile.truncate(0)
        sqlitefile.close()

        # init the output format combobox with the data pulled from registry
        self.gui.initoutputformatcombo(self.files.filetypes)

        # needs to be last because control goes to the gui once it's called
        gui.startgui()

    def quitprogram(self, _widget, _data=None):
        """Close open files before closing the program."""
        for datafile in self.files:
            datafile.close()
        gtk.main_quit()

    def queueexecution(self, widget, _data=None):
        """Signal the program to start once background processing is done."""
        self.executejoinqueued = widget.get_active()
        self.processtasks()

    def setoutputfile(self, _widget, _data=None):
        """Converts any configured output to the new output format."""
        outputfilename = self.gui['outputfilenameentry'].get_text()
        # if the target is being replaced, parse the outputfilename to get type
        if self.gui['replacetargetcheckbox'].get_active():
            # use the extension from the filename, outputtypecombo is unused
            outputfilename, outputfiletype = outputfilename.split('.')
            outputfiletype = '.' + outputfiletype
        else:
            # check if the location is specificed or just the filename
            if not re.search(r'\\\/', outputfilename):
                if self.gui['targetlocationcheckbox'].get_active():
                    targetalias = self.joins.gettarget()
                    targetpath = self.files.filenamesbyalias[targetalias]
                    targetdir = os.path.dirname(targetpath)
                    outputfilename = os.path.join(targetdir, outputfilename)
                else:
                # if no forward or backward slash, append default output path
                    outputfilename = os.path.join(
                        self.options['default_output_dir'],
                        outputfilename)
            outputfiletype = self.gui['outputtypecombo'].get_active_text()

        if self.gui['outputtablenameentry'].get_sensitive():
            outputtablename = self.gui['outputtablenameentry'].get_text()
        else:
            outputtablename = None

        try:
            outputfile = self.files.openoutputfile(outputfilename,
                                                   outputfiletype)
            # if a table wasn't needed (no error), disable the table entry
            # it may already be disabled, but easier to be sure than to check.
            self.gui['outputtablelabel'].set_sensitive(False)
            self.gui['outputtablenameentry'].set_sensitive(False)
            self.gui['outputtablenameentry'].set_text('')
        except table.NeedTableError:
            self.gui['outputtablelabel'].set_sensitive(True)
            self.gui['outputtablenameentry'].set_sensitive(True)
            if outputtablename is None:
                # default the table name to the target alias
                outputtablename = self.joins.gettarget()
                self.gui['outputtablenameentry'].set_text(outputtablename)
            outputfile = self.files.openoutputfile(outputfilename,
                                                   outputfiletype,
                                                   outputtablename)
        # do something more here? will it ever be None?
        if outputfile is None:
            return
        self.outputs.setoutputfile(outputfile)

        # needs to go before replacecolumns so that the types will be right
        fieldtypes = outputfile.getfieldtypes()
        fieldtypelist = self.gui['fieldtypelist']
        fieldtypelist.clear()
        for fieldtype in fieldtypes:
            fieldtypelist.append([fieldtype])

        fieldattributes = outputfile.getattributenames()
        self.gui.replacecolumns('fieldlist', 'fieldview', fieldattributes)
        fieldlist = self.gui['fieldlist']
        # Field calculator window setup
        self.gui['calcoutputfieldcombo'].set_model(fieldlist)

        for outputfield in self.outputs:
            fieldlist.append(outputfield.getattributes())
            # initialize a blank value for this field in the calculator
            blankvalue = outputfile.getblankvalue(outputfield)
            self.calc.setblankvalue(outputfield, blankvalue)

    def abortoutput(self, _widget, _data=None):
        """Set a signal for the output to abort."""
        self.joinaborted = True

    # 'execute join' button
    def executejoin(self, _widget, _data=None):
        """Execute the join and output the result"""
        if len(self.outputs) == 0:
            return

        # if the target is being replaced, rename it as a backup
        if self.gui['replacetargetcheckbox'].get_active():
            if self.gui['backupcheckbox'].get_active():
                self.joins.targetdata.close()
                self.joins.targetdata.backup()

        # call this to set the filename for the output
        self.setoutputfile(None)
        outputfile = self.outputs.outputfile

        # create fields
        outputfields = [self.outputs[fn] for fn in self.outputs.outputorder]
        try:
            outputfile.setfields(outputfields)
        except table.TableExistsError:
            response = self.gui.messagedialog("Table name in use, overwrite?",
                                              style='yesno')
            if response == gtk.RESPONSE_YES:
                outputfile.setfields(outputfields, overwrite=True)
            else:
                return

        self.calc.clear()
        for field in self.outputs:
            self.calc.createoutputfunc(field)

        stopbutton = self.gui['stopoutputbutton']
        stopbutton.set_sensitive(True)
        self.joinaborted = False

        restrictjoins = self.gui['restrictjoincheckbox'].get_active()

        # sqlite setup
        joinquery = self.joins.getquery(restrictjoins=restrictjoins)
        # print joinquery
        # open the database
        conn = sqlite3.connect('temp.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # query for the joined input values
        cur.execute(joinquery)
        # restrict one-to-many joins from creating extra records
        # the ROWID of the target table with joins is checked against the
        # ROWID of the target without joins, to detect extra records.
        # rcur provides the ROWID of the unjoined target
        if restrictjoins:
            rcur = conn.cursor()
            rcur.execute(self.joins.getrestrictionquery())

        # loop through target file
        i = 0
        recordcount = self.joins.getrecordcount()
        # print 'total records:', recordcount
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
            # print progresstext
            self.gui.setprogress(progress, progresstext)

            if self.joinaborted:
                self.gui.setprogress(0, 'Output aborted')
                stopbutton.set_sensitive(False)
                outputfile.close()
                return

            # process however many records before updating progress
            for _counter in range(i, min(i + 1000, recordcount)):
                # inputvalues[filealias_fieldname] = value
                inputvalues = cur.fetchone()
                # check id of the joined record against the control query
                if restrictjoins:
                    checkvalue = rcur.fetchone()
                    # end of file reached, the current and remaining records
                    # in the main query must be duplicates
                    if checkvalue is None:
                        break
                    # if the values don't match, this is an extra record
                    while (inputvalues['restrictjoins'] !=
                           checkvalue['restrictjoins']):
                        # keep fetching until it matches
                        # XXX could optionally prompt user for choice
                        inputvalues = cur.fetchone()
                        i = i + 1
                newrec = {}
                outputvalues = self.calc.calculateoutput(inputvalues)
                for fieldname, fieldvalue in outputvalues:
                    newrec[fieldname] = fieldvalue

                outputfile.addrecord(newrec)

                i = i + 1

        outputfile.close()
        print 'processing complete'
        self.gui.setprogress(1, 'Output complete')

    def updatesample(self, refreshrecords=None, samplesize=10):
        """Update the sample of output records"""
        if len(self.outputs) == 0:
            return

        if refreshrecords is not None:
            self.samplerecords = []

        sampleoutputfields = self.outputs.outputorder
        self.gui.replacecolumns('sampleoutputlist', 'sampleoutputview',
                                sampleoutputfields)

        self.calc.clear()
        for fieldname in sampleoutputfields:
            self.calc.createoutputfunc(self.outputs[fieldname])

        # generate a selection of records to use
        if len(self.samplerecords) != samplesize:
            self.samplerecords = []
            recordcount = self.joins.getrecordcount()
            samplesize = min(samplesize, recordcount)
            sampleindices = []
            while len(sampleindices) < samplesize:
                newindex = random.randint(0, recordcount)
                if newindex not in sampleindices:
                    sampleindices.append(newindex)

            # sqlite setup
            joinquery = self.joins.getquery(sampleindices)

            # open the database
            with sqlite3.connect('temp.db') as conn:
#            conn = sqlite3.connect('temp.db')
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # create the table
                cur.execute(joinquery)
                self.samplerecords = cur.fetchall()

        for inputvalues in self.samplerecords:
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

# start the program
AVERYDB = AveryDB()
