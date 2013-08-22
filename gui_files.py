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
import gtk


class GUI_Files(object):
    def addfile(self, _widget, _data=None):
        """Open a new file for joining to the target."""
        addfiledialog = self.gui.filedialog(self.files.filetypes)
        response = addfiledialog.run()
        # check that a file was selected
        if response == gtk.RESPONSE_OK:
            newfilename = addfiledialog.get_filename()
            newfilealias = self.files.addfile(newfilename)
            if type(newfilealias) is list:
                addfiledialog.destroy()
                self.addtables(newfilename, newfilealias)
            # will be None if data was already added
            elif newfilealias is not None:
                newfile = self.files[newfilealias]
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
        addfiledialog.destroy()
        # dbfutil.py, handles "background" processing
        self.processtasks()

    # needed for formats which contain multiple tables
    def addtables(self, filename, tablelist):
        tabledialog = self.gui.tabledialog(tablelist)
        response = tabledialog.run()
        if response == 1:
            selection = self.gui['tableview'].get_selection()
            (tablelist, selectedrows) = selection.get_selected_rows()
            for row in selectedrows:
                tablename = tablelist.get_value(tablelist.get_iter(row), 0)
                newfilealias = self.files.addfile(filename, tablename)
                newfile = self.files[newfilealias]
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
        self.refreshjoinlists()
