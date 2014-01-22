"""Event handlers for the output fields toolbar."""
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


class GUI_FieldToolbar(object):
    # populate the list of output fields with all the input fields
    def reloadfields(self, _widget, _data=None):
        """Populate the list view of output fields and the OutputManager."""
        # create the output file
        outputfilename = self.gui['outputfilenameentry'].get_text()
        if self.gui['replacetargetcheckbox'].get_active():
            print 'target changed:', outputfilename
            outputfilename, outputfiletype = outputfilename.split('.')
            outputfiletype = '.' + outputfiletype
        else:
            outputfiletype = self.gui['outputtypecombo'].get_active_text()
        tableentry = self.gui['outputtablenameentry']
        if tableentry.get_sensitive():
            tablename = tableentry.get_text()
        else:
            tablename = None
        outputfile = self.files.openoutputfile(outputfilename, outputfiletype,
                                               tablename)
        self.outputs.setoutputfile(outputfile)

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
        inputlist = self.gui['inputlist']
        inputlist.clear()

        self.outputs.clear()
        # check that a target file has been opened
        if self.joins.targetalias:
            # add all the fields from the target and everything joined to it
            for filealias in self.joins.getjoinedaliases():
                for field in self.files[filealias].getfields():
                    field.value = ('!' + filealias + '.' +
                                   field.originalname + '!')
                    newfield = self.outputs.addfield(field,
                                                     fieldsource=filealias)
                    fieldlist.append(newfield.getattributes())
                    inputlist.append([newfield['value']])
                    # initialize a blank value for this field in the calculator
                    blankvalue = outputfile.getblankvalue(newfield)
                    self.calc.setblankvalue(newfield, blankvalue)
        self.processtasks(('sample', 'refresh sample'))

    # 'add field' button
    def addfield(self, _widget, _data=None):
        """Add a new field after the last selected. Append if none selected."""
        # ignore press if no files are loaded
        if self.joins.gettarget() == '':
            return
        # get the selected row from the output list
        selection = self.gui['fieldview'].get_selection()
        # (model, [(path0,), (path1,), ...])
        (fieldlist, selectedrows) = selection.get_selected_rows()
        if selectedrows:
            insertindex = selectedrows[0][0]
        else:
            insertindex = len(self.gui['fieldlist'])

        # add an empty row after the last selected
        newfield = self.outputs.addnewfield(fieldindex=insertindex)
        fieldlist.insert(insertindex, newfield.getattributes())

        selection.unselect_all()
        selection.select_path(insertindex)
        self.gui['fieldview'].scroll_to_cell(insertindex)
        self.processtasks(('sample', None))

    # 'save field' button
    def copyfield(self, _widget, _data=None):
        """Create a copy of the selected field[s]."""
        selection = self.gui['fieldview'].get_selection()
        # (model, [(path0,), (path1,), ...])
        (fieldlist, selectedrows) = selection.get_selected_rows()
        if selectedrows:
            selection.unselect_all()
            # reverse it so indices won't get shifted as items are added
            selectedrows.reverse()
            for row in selectedrows:
                insertindex = row[0] + 1
                fieldcopy = self.outputs[row[0]].copy()
                newfield = self.outputs.addfield(fieldcopy,
                                                 fieldindex=insertindex)
                fieldlist.insert(insertindex, newfield.getattributes())
                selection.select_path(insertindex)
            self.gui['fieldview'].scroll_to_cell(insertindex)
        self.processtasks(('sample', None))

    # 'del field' button
    def removefield(self, _widget, _data=None):
        """Remove fields from the output."""
        selection = self.gui['fieldview'].get_selection()
        # (model, [(path0,), (path1,), ...])
        (fieldlist, selectedrows) = selection.get_selected_rows()
        if selectedrows:
            selection.unselect_all()
            # reverse it so indices won't get shifted as items are removed
            selectedrows.reverse()
            for row in selectedrows:
                fieldlist.remove(fieldlist.get_iter(row))
                self.outputs.removefield(row[0])
        self.processtasks(('sample', None))

    # 'move up' button
    def movetop(self, _widget, _data=None):
        """Move the selected items to the top of the list of output fields."""
        selection = self.gui['fieldview'].get_selection()
        # (model, [(path0,), (path1,), ...])
        (fieldlist, selectedrows) = selection.get_selected_rows()
        if selectedrows:
            selectedcount = selection.count_selected_rows()
            selection.unselect_all()
            moveindex = 0
            for row in selectedrows:
                fieldlist.move_before(fieldlist.get_iter(row),
                                      fieldlist.get_iter(moveindex))
                self.outputs.movefield(row[0], moveindex)
                moveindex += 1
            selection.select_range(0, selectedcount - 1)
            self.gui['fieldview'].scroll_to_cell(0)
        self.processtasks(('sample', None))

    # 'move up' button
    def moveup(self, _widget, _data=None):
        """Move the selected items up in the list of output fields."""
        selection = self.gui['fieldview'].get_selection()
        # (model, [(path0,), (path1,), ...])
        (fieldlist, selectedrows) = selection.get_selected_rows()
        if selectedrows:
            selection.unselect_all()
            # don't move items past end of the list, or other selected items
            startindex = 0
            for row in selectedrows:
                # check if the field is already as far up as possible
                if row[0] > startindex:
                    fieldlist.swap(fieldlist.get_iter(row),
                                   fieldlist.get_iter(row[0] - 1))
                    self.outputs.movefield(row[0], row[0] - 1)
                    selection.select_path(row[0] - 1)
                else:
                    selection.select_path(row[0])
                startindex += 1
            self.gui['fieldview'].scroll_to_cell(max(selectedrows[0][0] - 1,
                                                     0))
        self.processtasks(('sample', None))

    # 'move down' button
    def movedown(self, _widget, _data=None):
        """Move the selected items down in the list of output fields."""
        selection = self.gui['fieldview'].get_selection()
        # (model, [(path0,), (path1,), ...])
        (fieldlist, selectedrows) = selection.get_selected_rows()
        if selectedrows:
            selectedrows.reverse()
            selection.unselect_all()
            # don't move items past end of the list, or other selected items
            endindex = len(self.outputs.outputfields) - 1
            # scroll the view now since the right values to use are available
            self.gui['fieldview'].scroll_to_cell(min(selectedrows[0][0] + 1,
                                                     endindex))
            for row in selectedrows:
                # check if the field is already as far down as possible
                if row[0] < endindex:
                    fieldlist.swap(fieldlist.get_iter(row),
                                   fieldlist.get_iter(row[0] + 1))
                    self.outputs.movefield(row[0], row[0] + 1)
                    selection.select_path(row[0] + 1)
                else:
                    selection.select_path(row[0])
                endindex -= 1
        self.processtasks(('sample', None))

    # 'move down' button
    def movebottom(self, _widget, _data=None):
        """Move the selected items to the end of the list of output fields."""
        selection = self.gui['fieldview'].get_selection()
        # (model, [(path0,), (path1,), ...])
        (fieldlist, selectedrows) = selection.get_selected_rows()
        if selectedrows:
            selectedrows.reverse()
            selection.unselect_all()
            endindex = len(self.outputs.outputfields) - 1
            moveindex = endindex
            for row in selectedrows:
                fieldlist.move_after(fieldlist.get_iter(row),
                                     fieldlist.get_iter(moveindex))
                self.outputs.movefield(row[0], moveindex)
                moveindex -= 1
            selection.select_range(moveindex + 1, endindex)
            self.gui['fieldview'].scroll_to_cell(endindex)
        self.processtasks(('sample', None))
