"""Event handlers for adding and removing files."""
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
import urllib

import gtk


class GUI_Files(object):
    def selectandaddfile(self, _widget, _data=None):
        """Open a new file for joining to the target."""
        addfiledialog = self.gui.filedialog(self.files.filetypes)
        response = addfiledialog.run()
        # check that a file was selected
        if response == gtk.RESPONSE_OK:
            newfilename = addfiledialog.get_filename()
            addfiledialog.destroy()
            self.addfile(newfilename)
        else:
            addfiledialog.destroy()
        # task is queued by addfile
        self.processtasks()

    def addfile(self, filename):
        newfilealias = self.files.addfile(filename)
        if type(newfilealias) is list:
            self.addtables(filename, newfilealias)
        # will be None if data was already added or the data isn't readable
        elif newfilealias is not None:
            newfile = self.files[newfilealias]
            newfile.initfields()
            sqlconverter = newfile.convertdata(newfilealias)
            self.queuetask(('sqlite', (newfilealias, sqlconverter)))
            # add to the file list
            aliaslist = self.gui['aliaslist']
            newrow = aliaslist.append([newfilealias])

            # set as target if no target is set
            if self.joins.gettarget() == '':
                # this will trigger self.changetarget() which will do the rest
                self.gui['targetcombo'].set_active_iter(newrow)

    # taken from the pygtk faq 23.31
    def get_file_path_from_dnd_dropped_uri(self, uri):
        # get the path to file
        path = ""
        if uri.startswith('file:\\\\\\'):  # windows
            path = uri[8:]  # 8 is len('file:///')
        elif uri.startswith('file://'):  # nautilus, rox
            path = uri[7:]  # 7 is len('file://')
        elif uri.startswith('file:'):  # xffm
            path = uri[5:]  # 5 is len('file:')

        path = urllib.url2pathname(path)  # escape special chars
        path = path.strip('\r\n\x00')  # remove \r\n and NULL

        return path

    def dropfiles(self, widget, context, x, y, selection, target_type, time, data=None):
        # 80 is the type for a URI list
        if target_type == 80:
            uri = selection.data.strip('\r\n\x00')
            # print 'uri', uri
            uri_splitted = uri.split()
            for uri in uri_splitted:
                path = self.get_file_path_from_dnd_dropped_uri(uri)
                # print 'path to open', path
                self.addfile(path)
        # task is queued by addfile
        self.processtasks()

    # needed for formats which contain multiple tables
    def addtables(self, filename, tablelist):
        """Prompt user for tables to import from selected file."""
        tabledialog = self.gui.tabledialog(tablelist)
        response = tabledialog.run()
        if response == 1:
            selection = self.gui['tableview'].get_selection()
            (tablelist, selectedrows) = selection.get_selected_rows()
            for row in selectedrows:
                tablename = tablelist.get_value(tablelist.get_iter(row), 0)
                newfilealias = self.files.addfile(filename, tablename)
                newfile = self.files[newfilealias]
                newfile.initfields()
                sqlconverter = newfile.convertdata(newfilealias)
                self.queuetask(('sqlite', (newfilealias, sqlconverter)))
                # add to the file list
                aliaslist = self.gui['aliaslist']
                newrow = aliaslist.append([newfilealias])

                # set as target if no target is set
                if self.joins.gettarget() == '':
                    self.joins.settarget(newfilealias, newfile)
                    self.gui['targetcombo'].set_active_iter(newrow)
                    # set the default output filename to the target alias
                    self.gui['outputfilenameentry'].set_text(newfilealias)
                    self.reloadfields(None)
        tabledialog.hide()
        self.processtasks()

    def removefile(self, _widget, _data=None):
        """Close a file and remove all joins that depend on it."""
        # get the selection from the list of files
        selection = self.gui['dataview'].get_selection()
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
        self.joins.settarget(newtarget, self.files[newtarget])
        # update the output file parts of the gui
        self.replacetargettoggle(None)
        self.refreshjoinlists()
        self.reloadfields(None)

    def browsetooutput(self, _widget, _data=None):
        setoutputdialog = self.gui.filedialog(self.files.filetypes, foroutput=True)
        response = setoutputdialog.run()
        # check that a file was selected
        if response == gtk.RESPONSE_OK:
            newfilename = setoutputdialog.get_filename()
            self.gui['outputfilenameentry'].set_text(newfilename)
        setoutputdialog.destroy()

    def replacetargettoggle(self, _widget, _data=None):
        """Updates the file and table name entries, depending on the replace target checkbox."""
        replacetargetcheckbox = self.gui['replacetargetcheckbox']
        targetalias = self.joins.gettarget()
        print 'targetalias:', targetalias

        # check if a target is set
        if targetalias == '':
            targetpath = ''
            tablename = ''
        else:
            targetpath = self.files.filenamesbyalias[targetalias]
            # XXX using _table_ as a separator is breakable
            splitpath = targetpath.split('_table_')
            if len(splitpath) > 1:
                targetpath = splitpath[0]
                tablename = splitpath[1]
            else:
                tablename = ''
        if replacetargetcheckbox.get_active():
            self.gui['backupcheckbox'].set_sensitive(True)
            self.gui['outputfilenameentry'].set_text(targetpath)
            self.gui['outputtablenameentry'].set_text(tablename)
            self.gui['outputfilenameentry'].set_editable(False)
            self.gui['browsetooutputbutton'].set_sensitive(False)
            self.gui['outputtablenameentry'].set_editable(False)
            self.gui['outputtypecombo'].set_sensitive(False)
        else:
            self.gui['backupcheckbox'].set_sensitive(False)
            self.gui['outputfilenameentry'].set_text(targetalias)
            self.gui['outputtablenameentry'].set_text(tablename)
            self.gui['outputfilenameentry'].set_editable(True)
            self.gui['browsetooutputbutton'].set_sensitive(True)
            self.gui['outputtablenameentry'].set_editable(True)
            self.gui['outputtypecombo'].set_sensitive(True)
        # call this to reopen an output file and sort out whether
        # the table entry box should be sensitive
        if targetalias != '':
            self.setoutputfile(None)
