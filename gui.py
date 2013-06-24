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
import sys
import gtk
import gobject
#try:
#    import gtk
#except:
#    sys.exit(1)

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
        handlers['targetcombo_changed_cb'] = main.changetarget
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
#class GUI(object):
#    def delete_event(widget, event, data=None):
#        return False
#    def destroy(widget, data=None):
#        gtk.main_quit()
#    def main(self):
#        gtk.main()
#        
#    def __init__(self, main):        
#        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
#        self.window.set_title('DBF Util')
#        self.window.connect('delete_event', self.delete_event)
#        self.window.connect('destroy', self.destroy)
#        
#        self.filebox = gtk.VBox()
#        
#        self.filebuttonsbox = gtk.HBox()
#        self.targetbutton = gtk.Button('Select target dbf')
#        self.add_dbf = gtk.Button('add dbf')
#        self.remove_dbf = gtk.Button('remove dbf')
#        self.targetbutton.connect('clicked', main.opentarget)
#        self.add_dbf.connect('clicked', main.openjoin)
#        self.remove_dbf.connect('clicked', main.removejoin)
#        self.filebuttonsbox.pack_start(self.targetbutton)
#        self.filebuttonsbox.pack_start(self.add_dbf)
#        self.filebuttonsbox.pack_start(self.remove_dbf)
#        self.targetbutton.show()
#        self.add_dbf.show()
#        self.remove_dbf.show()
#        self.filebox.pack_start(self.filebuttonsbox)
#        self.filebuttonsbox.show()
#        
#        self.filelistbox =  gtk.ScrolledWindow()
#        self.outputfieldview.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
#        self.outputfieldmodel = gtk.ListStore(str)
#        self.outputfieldtable = gtk.TreeView(self.outputfieldmodel)
#        self.namecolumn = gtk.TreeViewColumn('Name')
#        self.valuecolumn = gtk.TreeViewColumn('Value')
#        self.typecolumn = gtk.TreeViewColumn('Type')
#        self.lencolumn = gtk.TreeViewColumn('Len')
#        self.deccolumn = gtk.TreeViewColumn('Dec')
#        self.outputfieldtable.append_column(self.namecolumn)
#        self.outputfieldtable.append_column(self.valuecolumn)
#        self.outputfieldtable.append_column(self.typecolumn)
#        self.outputfieldtable.append_column(self.lencolumn)
#        self.outputfieldtable.append_column(self.deccolumn)
#        self.namecell = gtk.CellRendererText()
#        self.valuecell = gtk.CellRendererText()
#        self.typecell = gtk.CellRendererText()
#        self.lencell = gtk.CellRendererText()
#        self.deccell = gtk.CellRendererText()
#        self.namecell.set_property('editable', True)
#        self.valuecell.set_property('editable', True)
#        self.typecell.set_property('editable', True)
#        self.lencell.set_property('editable', True)
#        self.deccell.set_property('editable', True)
#        self.namecell.connect('edited', main.fieldedited, (self.outputfieldmodel, 0))
#        self.valuecell.connect('edited', main.fieldedited, (self.outputfieldmodel, 1))
#        self.typecell.connect('edited', main.fieldedited, (self.outputfieldmodel, 2))
#        self.lencell.connect('edited', main.fieldedited, (self.outputfieldmodel, 3))
#        self.deccell.connect('edited', main.fieldedited, (self.outputfieldmodel, 4))
#        self.namecolumn.pack_start(self.namecell, True)
#        self.valuecolumn.pack_start(self.valuecell, True)
#        self.typecolumn.pack_start(self.typecell, True)
#        self.lencolumn.pack_start(self.lencell, True)
#        self.deccolumn.pack_start(self.deccell, True)
#        self.namecolumn.add_attribute(self.namecell, 'text', 0)
#        self.valuecolumn.add_attribute(self.valuecell, 'text', 1)
#        self.typecolumn.add_attribute(self.typecell, 'text', 2)
#        self.lencolumn.add_attribute(self.lencell, 'text', 3)
#        self.deccolumn.add_attribute(self.deccell, 'text', 4)
#        self.outputfieldtable.set_reorderable(True)
#        self.outputfieldview.add_with_viewport(self.outputfieldtable)
#        self.outputfieldtable.show()
#        
#        self.targetbox = gtk.HBox()
#        self.targetdescrip = gtk.Label('Primary target file: ')
#        self.targetlabel = gtk.Label()
#        self.targetbox.pack_start(self.targetdescrip)
#        self.targetbox.pack_start(self.targetlabel)
#        self.targetdescrip.show()
#        self.targetlabel.show()
#        self.window.add(self.targetbox)
#        self.targetbox.show()
#        
#        self.createjoinaliasbox = gtk.HBox()
#        self.jblabel0 = gtk.Label('Join')
#        self.joinaliascombo = gtk.ComboBox()
#        self.jblabel1 = gtk.Label('to')
#        self.targetaliascombo = gtk.ComboBox()
#        self.joinaliascombo.connect('changed', main.joinaliaschanged)
#        self.targetaliascombo.connect('changed', main.targetaliaschanged)
#        self.createjoinaliasbox.pack_start(self.jblabel0)
#        self.createjoinaliasbox.pack_start(self.joinaliascombo)
#        self.createjoinaliasbox.pack_start(self.jblabel1)
#        self.createjoinaliasbox.pack_start(self.targetaliascombo)
#        self.jblabel0.show()
#        self.joinaliascombo.show()
#        self.jblabel1.show()
#        self.targetaliascombo.show()
#        self.window.add(self.createjoinaliasbox)
#        self.createjoinaliasbox.show()
#        
#        self.createjoinfieldbox = gtk.HBox()
#        self.jblabel2 = gtk.Label('where')
#        self.joinfieldcombo = gtk.ComboBox()
#        self.jblabel3 = gtk.Label('equals')
#        self.targetfieldcombo = gtk.ComboBox()
#        self.createjoinfieldbox.pack_start(self.jblabel2)
#        self.createjoinfieldbox.pack_start(self.joinfieldcombo)
#        self.createjoinfieldbox.pack_start(self.jblabel3)
#        self.createjoinfieldbox.pack_start(self.targetfieldcombo)
#        self.jblabel2.show()
#        self.joinfieldcombo.show()
#        self.jblabel3.show()
#        self.targetfieldcombo.show()
#        self.window.add(self.createjoinfieldbox)
#        self.createjoinfieldbox.show()
#        
#        self.createjoinbutton = gtk.Button('Create Join')
#        self.createjoinbutton.connect('clicked', main.createjoin)
#        self.window.add(self.createjoinbutton)
#        self.createjoinbutton.show()
#        
#        self.outputbox = gtk.HBox()
#        
#        self.movefieldsbox = gtk.VBox()
#        self.movetopbutton = gtk.Button('top')
#        self.moveupbutton = gtk.Button('up')
#        self.movedownbutton = gtk.Button('down')
#        self.movebottombutton = gtk.Button('bottom')
#        self.movetopbutton.connect('clicked', main.movetop)
#        self.moveupbutton.connect('clicked', main.moveup)
#        self.movedownbutton.connect('clicked', main.movedown)
#        self.movebottombutton.connect('clicked', main.movebottom)
#        self.movefieldsbox.pack_start(self.movetopbutton)
#        self.movefieldsbox.pack_start(self.moveupbutton)
#        self.movefieldsbox.pack_start(self.movedownbutton)
#        self.movefieldsbox.pack_start(self.movebottombutton)
#        self.movetopbutton.show()
#        self.moveupbutton.show()
#        self.movedownbutton.show()
#        self.movebottombutton.show()
#        
#        self.outputfieldview = gtk.ScrolledWindow()
#        self.outputfieldview.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
#        self.outputfieldmodel = gtk.ListStore(str)
#        self.outputfieldtable = gtk.TreeView(self.outputfieldmodel)
#        self.namecolumn = gtk.TreeViewColumn('Name')
#        self.valuecolumn = gtk.TreeViewColumn('Value')
#        self.typecolumn = gtk.TreeViewColumn('Type')
#        self.lencolumn = gtk.TreeViewColumn('Len')
#        self.deccolumn = gtk.TreeViewColumn('Dec')
#        self.outputfieldtable.append_column(self.namecolumn)
#        self.outputfieldtable.append_column(self.valuecolumn)
#        self.outputfieldtable.append_column(self.typecolumn)
#        self.outputfieldtable.append_column(self.lencolumn)
#        self.outputfieldtable.append_column(self.deccolumn)
#        self.namecell = gtk.CellRendererText()
#        self.valuecell = gtk.CellRendererText()
#        self.typecell = gtk.CellRendererText()
#        self.lencell = gtk.CellRendererText()
#        self.deccell = gtk.CellRendererText()
#        self.namecell.set_property('editable', True)
#        self.valuecell.set_property('editable', True)
#        self.typecell.set_property('editable', True)
#        self.lencell.set_property('editable', True)
#        self.deccell.set_property('editable', True)
#        self.namecell.connect('edited', main.fieldedited, (self.outputfieldmodel, 0))
#        self.valuecell.connect('edited', main.fieldedited, (self.outputfieldmodel, 1))
#        self.typecell.connect('edited', main.fieldedited, (self.outputfieldmodel, 2))
#        self.lencell.connect('edited', main.fieldedited, (self.outputfieldmodel, 3))
#        self.deccell.connect('edited', main.fieldedited, (self.outputfieldmodel, 4))
#        self.namecolumn.pack_start(self.namecell, True)
#        self.valuecolumn.pack_start(self.valuecell, True)
#        self.typecolumn.pack_start(self.typecell, True)
#        self.lencolumn.pack_start(self.lencell, True)
#        self.deccolumn.pack_start(self.deccell, True)
#        self.namecolumn.add_attribute(self.namecell, 'text', 0)
#        self.valuecolumn.add_attribute(self.valuecell, 'text', 1)
#        self.typecolumn.add_attribute(self.typecell, 'text', 2)
#        self.lencolumn.add_attribute(self.lencell, 'text', 3)
#        self.deccolumn.add_attribute(self.deccell, 'text', 4)
#        self.outputfieldtable.set_reorderable(True)
#        self.outputfieldview.add_with_viewport(self.outputfieldtable)
#        self.outputfieldtable.show()
#        
#        self.morefieldbuttonsbox = gtk.VBox()
#        self.initoutputbutton = gtk.Button('init output')
#        self.removeoutputbutton = gtk.Button('del field')
#        self.configoutputbutton = gtk.Button('config selected')
#        self.saveoutputbutton = gtk.Button('save field')
#        self.addoutputbutton = gtk.Button('add field')
#        self.initoutputbutton.connect('clicked', main.initoutput)
#        self.removeoutputbutton.connect('clicked', main.removeoutput)
#        self.configoutputbutton.connect('clicked', main.configoutput)
#        self.saveoutputbutton.connect('clicked', main.saveoutput)
#        self.addoutputbutton.connect('clicked', main.addoutput)
#        self.morefieldbuttonsbox.pack_start(self.initoutputbutton)
#        self.morefieldbuttonsbox.pack_start(self.removeoutputbutton)
#        self.morefieldbuttonsbox.pack_start(self.configoutputbutton)
#        self.morefieldbuttonsbox.pack_start(self.saveoutputbutton)
#        self.morefieldbuttonsbox.pack_start(self.addoutputbutton)
#        self.initoutputbutton.show()
#        self.removeoutputbutton.show()
#        self.configoutputbutton.show()
#        self.saveoutputbutton.show()
#        self.addoutputbutton.show()
#        
#        self.outputbox.pack_start(self.movefieldsbox)
#        self.outputbox.pack_start(self.outputfieldview)
#        self.outputbox.pack_start(self.morefieldbuttonsbox)
#        self.movefieldsbox.show()
#        self.outputfieldview.show()
#        self.morefieldbuttonsbox.show()
#        
#        self.window.add(self.outputbox)
#        self.outputbox.show()
#        
#        self.outputfilenamebox = gtk.HBox()
#        self.outputfilenamelabel = gtk.Label('Output filename:')
#        self.outputfilenameentry = gtk.Entry()
#        self.executejoinbutton = gtk.Button('Execute Join')
#        self.outputfilenameentry.set_text('output.dbf')
#        self.executejoinbutton.connect('clicked', main.dojoin)
#        self.outputfilenamebox.pack_start(self.outputfilenamelabel)
#        self.outputfilenamebox.pack_start(self.outputfilenameentry)
#        self.outputfilenamebox.pack_start(self.executejoinbutton)
#        self.outputfilenamelabel.show()
#        self.outputfilenameentry.show()
#        self.executejoinbutton.show()
#        self.window.add(self.outputfilenamebox)
#        self.outputfilenamebox.show()
#        
#        self.window.show()

def creategui(main):
    gui = GUI(main)
#    root.title('DBF Utility')
    return gui
    
def startgui(gui):
    gui.main()
    