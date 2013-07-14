"""All things dealing strictly with the GUI."""
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
# GUI window config
import re

import gtk
import gobject


class GUI(object):
    """Initializes the GUI from the Glade file and provides widget access.

    This class:
    * builds the Glade file
    * gives access to all the widgets by name via __getitem__
    * provides convenient message and file dialogs
    * helps replace the columns in the output field store/view
    * updates the progress bar which can also be used to keep the interface
    responsive during background processing
    """
    def __init__(self, hfuncs):
        self.gladefile = 'dbfutil.glade'
        self.builder = gtk.Builder()
        self.builder.add_from_file(self.gladefile)
        self.newobjects = {}
        self.handlerfunctions = hfuncs

        handlers = {}
        handlers['mainwindow_destroy_cb'] = hfuncs.quitprogram
        handlers['addfilebutton_clicked_cb'] = hfuncs.addfile
        handlers['removefilebutton_clicked_cb'] = hfuncs.removefile
        handlers['targetcombo_changed_cb'] = hfuncs.changetarget
        handlers['joinaliascombo_changed_cb'] = hfuncs.loadjoinfields
        handlers['targetaliascombo_changed_cb'] = hfuncs.loadtargetfields
        handlers['joinfieldcombo_changed_cb'] = hfuncs.matchtargetfield
        handlers['addjoinbutton_clicked_cb'] = hfuncs.addjoin
        handlers['outputformatcombo_changed_cb'] = hfuncs.changeoutputformat
        handlers['movetopbutton_clicked_cb'] = hfuncs.movetop
        handlers['moveupbutton_clicked_cb'] = hfuncs.moveup
        handlers['movedownbutton_clicked_cb'] = hfuncs.movedown
        handlers['movebottombutton_clicked_cb'] = hfuncs.movebottom
        handlers['initoutputbutton_clicked_cb'] = hfuncs.initoutput
        handlers['addoutputbutton_clicked_cb'] = hfuncs.addoutput
        handlers['copyoutputbutton_clicked_cb'] = hfuncs.copyoutput
        handlers['removeoutputbutton_clicked_cb'] = hfuncs.removeoutput
        handlers['executejointoggle_toggled_cb'] = hfuncs.queueexecution
        handlers['removejoinbutton_clicked_cb'] = hfuncs.removejoin
        handlers['stopjoinbutton_clicked_cb'] = hfuncs.abortjoin
        # calc window
        handlers['opencalcbutton_clicked_cb'] = hfuncs.showcalculator
        handlers['calcwindow_delete_event_cb'] = hfuncs.hidecalculator
        handlers['calcoutputfieldcombo_changed_cb'] = hfuncs.changecalcfield
        handlers['calcinputview_row_activated_cb'] = hfuncs.insertfieldvalue
        handlers['calcsavevaluebutton_clicked_cb'] = hfuncs.savecalcvalue
        handlers['calclibrarycomboentry_changed_cb'] = hfuncs.loadfunctionlist
        handlers['calcfunctionview_row_activated_cb'] = hfuncs.insertfunccall
        # function window
        handlers['calcopenfuncbutton_clicked_cb'] = hfuncs.showfunceditor
        handlers['funcwindow_delete_event_cb'] = hfuncs.hidefunceditor
        handlers['funclibrarycombo_changed_cb'] = hfuncs.loadlibraryfunctions
        handlers['funcfunctioncombo_changed_cb'] = hfuncs.loadfunctiontext
        handlers['funcsavebutton_clicked_cb'] = hfuncs.savefunction
#        handlers['functiontextbuffer_changed_cb'] = hfuncs.checkfunctionname

        # experimental
        handlers['sampleoutputview_columns_changed_cb'] = hfuncs.reordercols

        self.builder.connect_signals(handlers)

        # other setup
        outputselection = self.builder.get_object('outputview').get_selection()
        outputselection.set_mode(gtk.SELECTION_MULTIPLE)

        self.mainwindow = self.builder.get_object('mainwindow')
        self.mainwindow.show_all()

    @classmethod
    def filedialog(cls, filetypes):
        """Sets up and returns a file chooser dialog for the caller to run."""
        dialog = gtk.FileChooserDialog("Open..",
                                       None,
                                       gtk.FILE_CHOOSER_ACTION_OPEN,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        for filetype in filetypes:
            filefilter = gtk.FileFilter()
            filefilter.set_name(filetype)
            for mimetype in filetypes[filetype]['mimes']:
                filefilter.add_mime_type(mimetype)
            for pattern in filetypes[filetype]['patterns']:
                filefilter.add_pattern(pattern)
            dialog.add_filter(filefilter)

        return dialog

    @classmethod
    def messagedialog(cls, message):
        """Creates a simple dialog to display the provided message."""
        dialog = gtk.MessageDialog(buttons=gtk.BUTTONS_OK,)
        dialog.set_markup(message)
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.run()
        dialog.destroy()

    # This is used for the output field config and sample views.
    def replacecolumns(self, storename, viewname, newcolnames):
        """Replaces the columns in the output list/view with new columns."""
        # make a new liststore to use
        typelist = []
        for i in range(len(newcolnames)):
            typelist.append(gobject.TYPE_STRING)
        # __getitem__ checks newobjects so access will shift to the new store
        self.newobjects[storename] = gtk.ListStore(*typelist)

        # update the listview
        view = self[viewname]
        view.set_model(self[storename])
        # remove the old columns
        for col in view.get_columns():
            view.remove_column(col)
        # add the new columns
        for i in range(len(newcolnames)):
            # treeviews need double underscores to display single underscores
            colname = re.sub(r'_', '__', newcolnames[i])
            newcell = gtk.CellRendererText()
            newcell.set_property('editable', True)
            newcell.connect('edited',
                            self.handlerfunctions.updatefieldattribute,
                            self[storename], i)
            newcolumn = gtk.TreeViewColumn(colname, newcell, text=i)
            view.append_column(newcolumn)

    def setprogress(self, progress=-1, text='', lockgui=True):
        """Updates the progress bar immediately.

        progress: value from 0 to 1. -1 will keep the existing setting
        text: text to display on the bar
        lockgui: call setprogress during a long function with lockgui=False
        to enable gui input while the background function runs."""
        progressbar = self['progressbar']
        stopjoinbutton = self['stopjoinbutton']
        if lockgui:
            progressbar.grab_add()
            # Also check the abort button
            stopjoinbutton.grab_add()
        if progress == 'pulse':
            progressbar.pulse()
        elif progress >= 0:
            progressbar.set_fraction(progress)
        progressbar.set_text(text)
        while gtk.events_pending():
            gtk.main_iteration(False)
        if lockgui:
            progressbar.grab_remove()
            stopjoinbutton.grab_remove()

    def __getitem__(self, objname):
        if objname in self.newobjects:
            return self.newobjects[objname]
        return self.builder.get_object(objname)


def creategui(handlerfunctions):
    """Initializes and returns the gui."""
    gui = GUI(handlerfunctions)
#    root.title('DBF Utility')
    return gui


def startgui():
    """Starts the gtk main loop."""
    gtk.main()
