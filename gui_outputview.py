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
import re
import sqlite3


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

    def autoadjustfieldlengths(self, _widget, _data=None):
        textfieldindices = {}
        newlengths = {}
        i = 0
        # check that there is a length attribute
        fieldattributes = self.outputs.outputfile.fieldattrorder
        fieldattributes = [attrname.lower() for attrname in fieldattributes]
        if 'length' in fieldattributes:
            attrposition = fieldattributes.index('length')
            # locate the text fields and save their index & name
            for outputfield in self.outputs:
                if outputfield.getattribute('type') == 'TEXT':
                        textfieldindices[outputfield.name] = i
                        newlengths[outputfield.name] = -1
            i += 1
        # stop if there is no length attribute
        else:
            return

        if len(textfieldindices) > 0:
            joinquery = self.joins.getquery()
            # open the database
            conn = sqlite3.connect('temp.db')
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            # create the table
            for inputvalues in cur.execute(joinquery):
                outputvalues = self.calc.calculateoutput(inputvalues)
                # compare outputvalues to find the longest for each
                for fieldname in newlengths:
                    newlengths[fieldname] = max(newlengths[fieldname],
                                                len(outputvalues[fieldname]))
            outputlist = self.gui['outputlist']
            for fieldname in newlengths:
                fieldindex = textfieldindices[fieldname]
                fieldlength = newlengths[fieldname]
                self.updatefieldattribute(None, fieldindex, fieldlength, outputlist, attrposition)

    # XXX dragging dropping columns to reorder attributes, mostly incomplete
    def reordercols(self, widget):
        """Update the column order when they are drug around in the GUI."""
        return
        columns = widget.get_columns()
        columnnames = [col.get_title() for col in columns]
        outputlist = self.gui['outputlist']
        for i in range(len(columnnames)):
            pass
