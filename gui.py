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
# GUI window config
import gtk
import gobject

class GUI(object):
    def main(self):
        gtk.main()
        
    def __init__(self, main):
        self.gladefile = 'dbfutil.glade'
        self.builder = gtk.Builder()
        self.builder.add_from_file(self.gladefile)
        self.newobjects = {}
        self.hfuncs = main
            
        handlers = {}
        handlers['mainwindow_destroy_cb'] = main.quitprogram
        handlers['addfilebutton_clicked_cb'] = main.addfile
        handlers['removefilebutton_clicked_cb'] = main.removefile
        handlers['targetcombo_changed_cb'] = main.targetchanged
        handlers['joinaliascombo_changed_cb'] = main.joinaliaschanged
        handlers['targetaliascombo_changed_cb'] = main.targetaliaschanged
        handlers['joinfieldcombo_changed_cb'] = main.joinfieldchanged
        handlers['addjoinbutton_clicked_cb'] = main.addjoin
        handlers['outputformatcombo_changed_cb'] = main.changeoutputformat 
        handlers['movetopbutton_clicked_cb'] = main.movetop
        handlers['moveupbutton_clicked_cb'] = main.moveup
        handlers['movedownbutton_clicked_cb'] = main.movedown
        handlers['movebottombutton_clicked_cb'] = main.movebottom
        handlers['initoutputbutton_clicked_cb'] = main.initoutput
        handlers['addoutputbutton_clicked_cb'] = main.addoutput
        handlers['copyoutputbutton_clicked_cb'] = main.copyoutput
        handlers['removeoutputbutton_clicked_cb'] = main.removeoutput
        handlers['executejoinbutton_clicked_cb'] = main.executejoin
        handlers['removejoinbutton_clicked_cb'] = main.removejoin
        handlers['stopjoinbutton_clicked_cb'] = main.abortjoin

        self.builder.connect_signals(handlers)
        
        # other setup
        outputselection = self.builder.get_object('outputview').get_selection()
        outputselection.set_mode(gtk.SELECTION_MULTIPLE)
        
        self.window = self.builder.get_object('mainwindow')
        self.window.show_all()
        
    def filedialog(self, filetypes):
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
        
    def messagedialog(self, message):
        dialog = gtk.MessageDialog(buttons=gtk.BUTTONS_OK,)
        dialog.set_markup(message)
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.run()
        dialog.destroy()
        
    def replacecolumns(self, storename, viewname, newcolnames):
        # make a new liststore to use
        typelist = []
        for i in range(len(newcolnames)):
            typelist.append(gobject.TYPE_STRING)
        # __getitem__ checks newobjects, so this will seamlessly shift access to the new store
        self.newobjects[storename] = gtk.ListStore(*typelist)
        
        # update the listview
        view = self[viewname]
        view.set_model(self[storename])
        # remove the old columns
        for col in view.get_columns():
            view.remove_column(col)
        # add the new columns
        for i in range(len(newcolnames)):
             newcell = gtk.CellRendererText()
             newcell.set_property('editable', True)
             newcell.connect('edited', self.hfuncs.updatefieldattribute, self[storename], i)
             newcolumn = gtk.TreeViewColumn(newcolnames[i], newcell, text=i)
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

def creategui(main):
    gui = GUI(main)
#    root.title('DBF Utility')
    return gui
    
def startgui(gui):
    gui.main()
    