# """All things dealing strictly with the GUI."""
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
        self.gladefile = 'averydb.glade'
        self.builder = gtk.Builder()
        self.builder.add_from_file(self.gladefile)
        self.newobjects = {}
        self.handlerfunctions = hfuncs

        handlers = {}
        # GUI_Files
        handlers['adddatabutton_clicked_cb'] = hfuncs.selectandaddfile
        handlers['mainwindow_drag_data_received_cb'] = hfuncs.dropfiles
        handlers['tabledialog_delete_event_cb'] = hfuncs.closetabledialog
        handlers['configinputdialog_delete_event_cb'] = hfuncs.closeconfiginputdialog
        handlers['removedatabutton_clicked_cb'] = hfuncs.removefile
        handlers['targetcombo_changed_cb'] = hfuncs.changetarget
        handlers['browsetooutputbutton_clicked_cb'] = hfuncs.browsetooutput
        handlers['replacetargetcheckbox_toggled_cb'] = hfuncs.replacetargettoggle
        handlers['targetlocationcheckbox_toggled_cb'] = hfuncs.targetlocationtoggle
        # GUI_JoinConfig
        handlers['joinaliascombo_changed_cb'] = hfuncs.loadjoinfields
        handlers['targetaliascombo_changed_cb'] = hfuncs.loadtargetfields
        handlers['joinfieldcombo_changed_cb'] = hfuncs.matchtargetfield
        handlers['addjoinbutton_clicked_cb'] = hfuncs.addjoin
        handlers['removejoinbutton_clicked_cb'] = hfuncs.removejoin
        handlers['innercolumntoggle_toggled_cb'] = hfuncs.toggleinner
        # GUI_FieldToolbar
        handlers['reloadfieldsbutton_clicked_cb'] = hfuncs.reloadfields
        handlers['addfieldbutton_clicked_cb'] = hfuncs.addfield
        handlers['copyfieldbutton_clicked_cb'] = hfuncs.copyfield
        handlers['removefieldbutton_clicked_cb'] = hfuncs.removefield
        handlers['movetopbutton_clicked_cb'] = hfuncs.movetop
        handlers['moveupbutton_clicked_cb'] = hfuncs.moveup
        handlers['movedownbutton_clicked_cb'] = hfuncs.movedown
        handlers['movebottombutton_clicked_cb'] = hfuncs.movebottom
        # AveryDB
        handlers['mainwindow_destroy_cb'] = hfuncs.quitprogram
        handlers['outputtypecombo_changed_cb'] = hfuncs.setoutputfile
        handlers['executejointoggle_toggled_cb'] = hfuncs.queueexecution
        handlers['stopoutputbutton_clicked_cb'] = hfuncs.abortoutput
        # calc window
        handlers['calclibrarybutton_clicked_cb'] = hfuncs.showlibraries
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
        handlers['funcreloadbutton_clicked_cb'] = hfuncs.loadfunctiontext
        handlers['funcsavebutton_clicked_cb'] = hfuncs.savefunction
        handlers['funcsaveclosebutton_clicked_cb'] = hfuncs.saveclosefunction
        handlers['funccancelbutton_clicked_cb'] = hfuncs.hidefunceditor
        # new library dialog
        handlers['funcaddlibrarybutton_clicked_cb'] = hfuncs.getlibraryname
        handlers['newlibcreate_clicked_cb'] = hfuncs.createlibrary
        handlers['newlibcancel_clicked_cb'] = hfuncs.cancelcreatelibrary
        # keyboard shortcuts
        handlers['fieldview_key_press_event_cb'] = hfuncs.fieldskeypressed
        # menu items
        handlers['filemenupreferences_activate_cb'] = hfuncs.showoptions
        handlers['optionsbutton_clicked_cb'] = hfuncs.showoptions
        handlers['fieldlengthbutton_clicked_cb'] = hfuncs.autoadjustfieldlengths
        # options window
        handlers['optionswindow_delete_event_cb'] = hfuncs.closeoptions
        handlers['optionsavebutton_clicked_cb'] = hfuncs.saveoptions
        handlers['optionsaveclosebutton_clicked_cb'] = hfuncs.savecloseoptions
        handlers['optioncancelbutton_clicked_cb'] = hfuncs.closeoptions
        handlers['defaultoutputbrowsebutton_clicked_cb'] = hfuncs.browsedefaultoutput

        # table selection dialog
#        handlers['tableok_clicked_cb'] = hfuncs.addtables

        # experimental
        handlers['sampleoutputview_columns_changed_cb'] = hfuncs.reordercols

        self.builder.connect_signals(handlers)

        # other setup
        outputselection = self.builder.get_object('fieldview').get_selection()
        outputselection.set_mode(gtk.SELECTION_MULTIPLE)
        tableselection = self.builder.get_object('tableview').get_selection()
        tableselection.set_mode(gtk.SELECTION_MULTIPLE)
        # drag and drop file support
        mainwindow = self.builder.get_object('mainwindow')
        mainwindow.drag_dest_set(gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_HIGHLIGHT |
                               gtk.DEST_DEFAULT_DROP,
                               # 80 is the type code for a URI list
                               [('text/uri-list', 0, 80)],
                               gtk.gdk.ACTION_COPY)
        mainwindow.show_all()

    def initoutputformatcombo(self, filetypes):
        typelist = self['outputtypelist']
        typelist.clear()
        for filetype in filetypes:
            if filetype not in ['All supported', 'All files']:
                extensions = filetypes[filetype]['patterns']
                # trim the wildcard asterisk from each extension
                for i in range(len(extensions)):
                    extensions[i] = extensions[i][1:]
                typelist.append([', '.join(extensions),
                                 filetype])
        self['outputtypecombo'].set_active(0)

    @classmethod
    def filedialog(cls, filetypes, foroutput=False, folder=False):
        """Sets up and returns a file chooser dialog for the caller to run."""
        if folder:
            title = 'Choose directory...'
            action = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER
        elif foroutput:
            title = 'Save as...'
            action = gtk.FILE_CHOOSER_ACTION_SAVE
        else:
            title = 'Open...'
            action = gtk.FILE_CHOOSER_ACTION_OPEN

        dialog = gtk.FileChooserDialog(title, None, action,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        for filetype in filetypes:
            filefilter = gtk.FileFilter()
            filefilter.set_name(filetype)
            for mimetype in filetypes[filetype]['mimes']:
                filefilter.add_mime_type(mimetype)
            for pattern in filetypes[filetype]['patterns']:
                filefilter.add_pattern(pattern.upper())
                filefilter.add_pattern(pattern.lower())
            dialog.add_filter(filefilter)

        return dialog

    def tabledialog(self, tablenames):
        """Give a list of tables within a file to choose which to load."""
        dialog = self['tabledialog']
        tabletree = self['tabletree']
        tabletree.clear()
        if type(tablenames) == list:
            for tablename in tablenames:
                tabletree.append(None, [tablename, None])
        # used for gdb only, currently
        elif type(tablenames) == dict:
            # add features in datasets
            if 'datasets' in tablenames:
                datasets = tablenames['datasets'].keys()
                datasets.sort()
                for dataset in datasets:
                    parentiter = tabletree.append(None, [dataset, 'DataSet'])
                    features = tablenames['datasets'][dataset]
                    features.sort()
                    for feature in features:
                        tabletree.append(parentiter, [feature, 'Feature'])
            # add features in root
            if 'features' in tablenames:
                rootfeatures = tablenames['features']
                rootfeatures.sort()
                for feature in rootfeatures:
                    tabletree.append(None, [feature, 'Feature'])
            # add tables in root
            if 'tables' in tablenames:
                roottables = tablenames['tables']
                roottables.sort()
                for table in roottables:
                    tabletree.append(None, [table, 'Table'])

        return dialog

    @classmethod
    def messagedialog(cls, message, style='msg'):
        """Creates a simple dialog to display the provided message."""
        if style == 'yesno':
            dialog = gtk.MessageDialog(type=gtk.MESSAGE_QUESTION,
                                       buttons=gtk.BUTTONS_YES_NO)
        else:
            dialog = gtk.MessageDialog(buttons=gtk.BUTTONS_OK)
        dialog.set_markup(message)
        dialog.set_default_response(gtk.RESPONSE_OK)
        response = dialog.run()
        dialog.destroy()
        return response

    # This is used for the output field config and sample views.
    def replacecolumns(self, storename, viewname, newcolnames):
        """Replaces the columns in the output list/view with new columns."""
        # make a new liststore to use
        celltypelist = []
        for i in range(len(newcolnames)):
            celltypelist.append(gobject.TYPE_STRING)
        # __getitem__ checks newobjects so access will shift to the new store
        self.newobjects[storename] = gtk.ListStore(*celltypelist)

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
            if colname.lower() in ('type', 'affinity'):
                fieldtypelist = self['fieldtypelist']
                newcell = gtk.CellRendererCombo()
                newcell.set_property('editable', True)
                newcell.set_property('has-entry', False)
                newcell.set_property('model', fieldtypelist)
                newcell.set_property('text-column', 0)
                newcell.connect('changed',
                                self.handlerfunctions.updatefieldtype,
                                fieldtypelist, self[storename], i)
                newcolumn = gtk.TreeViewColumn(colname, newcell, text=1)
            else:
                newcell = gtk.CellRendererText()
                newcell.set_property('editable', True)
                newcell.connect('edited',
                                self.handlerfunctions.updatefieldattribute,
                                self[storename], i)
                newcolumn = gtk.TreeViewColumn(colname, newcell, text=i)
            view.append_column(newcolumn)

    def initconfiginputwindow(self, fieldnames, fieldvalues, fieldtypes):
        dialog = gtk.Dialog('Define input', self['mainwindow'],
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                             gtk.STOCK_OK, gtk.RESPONSE_OK))
        dialog.set_modal(True)
        dialog.set_default_size(500, 400)
        contentarea = dialog.get_content_area()
        dialogvbox = gtk.VBox()
        contentarea.pack_start(dialogvbox, True, True, 0)
        # label at the top
        dialoglabel = gtk.Label('Define field types')
        dialogvbox.pack_start(dialoglabel, False, False, 0)
        # scrolled window for everything else
        dialogscrolledwindow = gtk.ScrolledWindow()
        dialogvbox.pack_start(dialogscrolledwindow, True, True)
        # viewport to hold everything in the scrolled window
        dialogviewport = gtk.Viewport()
        dialogscrolledwindow.add(dialogviewport)
        # hbox to hold the stuff for each field
        scrollhbox = gtk.HBox()
        dialogviewport.add(scrollhbox)

        inputtypelist = gtk.ListStore(gobject.TYPE_STRING)
        for fieldtype in fieldtypes:
            inputtypelist.append([fieldtype])

        # store references to the comboboxes in the GUI object so their
        # values can be retrieved from gui_files
        self.typecomboboxes = []

        # for each field
        for i in range(len(fieldnames)):
            # create a box to hold everything
            inputfieldvbox = gtk.VBox()
            # store the sample values in a list
            inputfieldvaluelist = gtk.ListStore(gobject.TYPE_STRING)
            for record in fieldvalues:
                inputfieldvaluelist.append([record[i]])
            # create a view to hold the field name and a sample of values
            inputfieldview = gtk.TreeView(inputfieldvaluelist)
            # add a cell in a column to the listview to display the values
            inputfieldcell = gtk.CellRendererText()
            inputfieldcolumn = gtk.TreeViewColumn(fieldnames[i], inputfieldcell,
                                                  text=0)
            inputfieldview.append_column(inputfieldcolumn)
            # add a combobox for selecting field type
            inputfieldtypecombo = gtk.ComboBox(inputtypelist)
            inputtypecell = gtk.CellRendererText()
            inputfieldtypecombo.pack_start(inputtypecell, expand=True)
            inputfieldtypecombo.add_attribute(cell=inputtypecell,
                                              attribute='text',
                                              column=0)
            self.typecomboboxes.append(inputfieldtypecombo)
            # pack the two main objects
            inputfieldvbox.pack_start(inputfieldview, expand=True)
            inputfieldvbox.pack_start(inputfieldtypecombo, expand=False)
            # pack the box itself
            scrollhbox.pack_start(inputfieldvbox, expand=False)
        dialog.show_all()
        return dialog

    def setprogress(self, progress=-1, text='', lockgui=True):
        """Updates the progress bar immediately.

        progress: value from 0 to 1. -1 will keep the existing setting
        text: text to display on the bar
        lockgui: call setprogress during a long function with lockgui=False
        to enable gui input while the background function runs."""
        progressbar = self['progressbar']
        stopoutputbutton = self['stopoutputbutton']
        if lockgui:
            progressbar.grab_add()
            # Also check the abort button
            stopoutputbutton.grab_add()
        if progress == 'pulse':
            progressbar.pulse()
        elif progress >= 0:
            progressbar.set_fraction(progress)
        progressbar.set_text(text)
        while gtk.events_pending():
            gtk.main_iteration(False)
        if lockgui:
            progressbar.grab_remove()
            stopoutputbutton.grab_remove()

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
