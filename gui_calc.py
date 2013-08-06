"""Event handlers for the calculator window."""
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


class GUI_Calc(object):
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
