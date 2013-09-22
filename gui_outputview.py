"""Event handlers for the output field list view."""
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


class GUI_OutputView(object):
    def updatefieldattribute(self, _cell, row, newvalue, outputlist, column):
        """Update data when an outputview cell is edited."""
        # Update output manager if the field name was changed
        if column == 0:
            newvalue = self.outputs.updatename(row, newvalue)
        # update the view
        outputlist[row][column] = newvalue
        # update the field
        self.outputs[row][column] = newvalue
        # update the output sample
        self.processtasks(('sample', None))

    def updatefieldtype(self, _combo, row, new_iter, typelist, outputlist):
        newvalue = typelist[new_iter][0]
        # update the view
        outputlist[row][1] = newvalue
        # update the field. 'type' is always the second column
        self.outputs[row][1] = newvalue
        # update the output sample
        self.processtasks(('sample', None))
        self.gui['outputview'].grab_focus()

    # XXX dragging dropping columns to reorder attributes, incomplete
    def reordercols(self, widget):
        """Update the column order when they are drug around in the GUI."""
        return
        columns = widget.get_columns()
        columnnames = [col.get_title() for col in columns]
        outputlist = self.gui['outputlist']
        for i in range(len(columnnames)):
            pass
