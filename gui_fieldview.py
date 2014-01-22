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
import sqlite3


class GUI_FieldView(object):
    def updatefieldattribute(self, _cell, row, newvalue, fieldlist, column):
        """Update data when a fieldview cell is edited."""
        # Update output manager if the field name was changed
        if column == 0:
            newvalue = self.outputs.updatename(row, newvalue)
        # update the view
        fieldlist[row][column] = newvalue
        # update the field
        self.outputs[row][column] = newvalue
        # update the output sample
        self.processtasks(('sample', None))

    def updatefieldtype(self, _combo, row, new_iter, typelist, fieldlist,
                        column):
        newvalue = typelist[new_iter][0]
        # update the view
        fieldlist[row][column] = newvalue
        # update the field
        self.outputs[row][column] = newvalue
        # update the output sample
        self.processtasks(('sample', None))
        self.gui['fieldview'].grab_focus()

    def autoadjustfieldlengths(self, _widget, _data=None):
        lengthadjuster = self.fieldlengthadjuster()
        self.processtasks(('lengthadjust', lengthadjuster))

    # longish-running,  yields periodically so the GUI can function
    def fieldlengthadjuster(self):
        """Detects needed length for fields and yields to GUI periodically."""
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
            recordcount = self.joins.getrecordcount()
            i = 0
            # calculate all the outputs to find the max lengths
            for inputvalues in cur.execute(joinquery):
                outputvalues = self.calc.calculateoutput(inputvalues)
                # compare outputvalues to find the longest for each
                for fieldname, fieldvalue in outputvalues:
                    if fieldname in newlengths:
                        newlengths[fieldname] = max(newlengths[fieldname],
                                                    len(fieldvalue))
                i += 1
                if i % 1000 == 0:
                    yield float(i) / recordcount
            fieldlist = self.gui['fieldlist']
            extralength = self.options['extra_field_length']
            for fieldname in newlengths:
                fieldindex = textfieldindices[fieldname]
                fieldlength = newlengths[fieldname] + extralength
                self.updatefieldattribute(None, fieldindex, fieldlength,
                                          fieldlist, attrposition)

    def addjoinedfields(self, filealias):
        fieldlist = self.gui['fieldlist']
        inputlist = self.gui['inputlist']
        outputfile = self.outputs.outputfile
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

    # XXX what about fields with changed value
    def removejoinedfields(self, filealias):
        """Remove fields that belong to a join that was removed."""
        removalindices = []
        fieldlist = self.gui['fieldlist']
        i = 0
        for field in self.outputs:
            if field.source == filealias:
                removalindices.append(i)
            i += 1
        # remove from the end so the indices won't shift
        removalindices.reverse()
        for index in removalindices:
            self.outputs.removefield(index)
            fieldlist.remove(fieldlist.get_iter(index))
        self.processtasks(('sample', None))

    # XXX dragging dropping columns to reorder attributes, barely started
    def reordercols(self, widget):
        """Update the column order when they are drug around in the GUI."""
        return
        columns = widget.get_columns()
        columnnames = [col.get_title() for col in columns]
        # fieldlist = self.gui['fieldlist']
        for i in range(len(columnnames)):
            pass
