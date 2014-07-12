"""Event handlers for adding and removing joins."""
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


class GUI_JoinConfig(object):
    def loadjoinfields(self, _widget, _data=None):
        """Update the join field combo when the join alias combo changes."""
        # clear the liststore and add the new items
        joinfieldlist = self.gui['joinfieldlist']
        joinfieldlist.clear()

        # get the selected file alias
        joinalias = self.gui['joinaliascombo'].get_active_text()
        if joinalias is not None:
            joinfields = self.files[joinalias].getfields()
            for joinfield in joinfields:
                joinfieldlist.append([joinfield.originalname])

    def loadtargetfields(self, _widget, _data=None):
        """Update target field combo when target alias combo changes."""
        # clear the liststore and add the new items
        targetfieldlist = self.gui['targetfieldlist']
        targetfieldlist.clear()

        # get the selected file alias
        targetalias = self.gui['targetaliascombo'].get_active_text()
        if targetalias is not None:
            targetfields = self.files[targetalias].getfields()
            for targetfield in targetfields:
                targetfieldlist.append([targetfield.originalname])

    def matchtargetfield(self, widget, _data=None):
        """Sets the target field if there is one with a matching name."""
        value = widget.get_active_text()
        if value is not None:
            value = value.lower()
        targetfieldlist = self.gui['targetfieldlist']
        for row in targetfieldlist:
            if value == row[0].lower():
                self.gui['targetfieldcombo'].set_active_iter(row.iter)
                return
        # clear selection if no match
        self.gui['targetfieldcombo'].set_active(-1)

    # 'apply' join choice button
    def addjoin(self, _widget, _data=None):
        """Save join using the selected fields in the gui."""
        # get combobox selections
        joinalias = self.gui['joinaliascombo'].get_active_text()
        joinfieldname = self.gui['joinfieldcombo'].get_active_text()
        targetalias = self.gui['targetaliascombo'].get_active_text()
        targetfieldname = self.gui['targetfieldcombo'].get_active_text()
        inner = self.gui['innerjoincheckbox'].get_active()

        if joinfieldname is not None and targetfieldname is not None:
            # check if joinalias is in use, and if it is, create a new alias
            # this simplifies the data model since it prevents loops
            if joinalias in self.joins.getjoinedaliases():
                joinalias = self.files.addnewalias(joinalias)
            jointable = self.files[joinalias]
            joinfield = jointable.fields[joinfieldname]
            targettable = self.files[targetalias]
            targetfield = targettable.fields[targetfieldname]
            # save to joins
            newjoin = self.joins.addjoin(joinalias, jointable, joinfield,
                                         targetalias, targettable, targetfield,
                                         inner)
            self.refreshjoinlists()
            self.queuetask(('index', newjoin))
            self.queuetask(('sample', 'refresh sample'))
            # add the new fields to the GUI field view
            self.addjoinedfields(joinalias)
            self.processtasks()

    def removejoin(self, _widget, _data=None):
        """Removes the selected joins and any child joins dependent on it."""
        selection = self.gui['joinview'].get_selection()
        (fieldlist, selectedrow) = selection.get_selected()
        if fieldlist.get_string_from_iter(selectedrow) != '0':
            joinalias = fieldlist[selectedrow][0]
            self.joins.removealias(joinalias)
            self.refreshjoinlists()
            # remove the fields from this join from the GUI field view
            self.removejoinedfields(joinalias)

    def toggleinner(self, cell, path, data=None):
        jointree = self.gui['jointree']
        rowiter = jointree.get_iter(path)
        # toggle the checkbox
        togglestatus = not jointree[path][3]
        jointree[path][3] = togglestatus
        # update the join
        targetiter = jointree.iter_parent(rowiter)
        targetalias = jointree.get_value(targetiter, 0)
        joinalias = jointree[path][0]
        self.joins.setinner(targetalias, joinalias, togglestatus)
        self.processtasks(('sample', 'refresh sample'))

    def refreshjoinlists(self):
        """Update when a join is added/removed or main target is changed."""
        # refresh the target alias combobox list
        targetaliaslist = self.gui['targetaliaslist']
        targetcombo = self.gui['targetaliascombo']
        # save the current selection
        activealias = targetcombo.get_active_text()
        # refresh the list of valid targets
        targetaliaslist.clear()
        for alias in self.joins.joinedaliases:
            targetaliaslist.append([alias])
        # reselect the previous selection, if it's still there
        for row in targetaliaslist:
            if activealias in row:
                targetcombo.set_active_iter(row.iter)

        jointree = self.gui['jointree']
        # refresh the list of joins
        jointree.clear()
        # add the main target
        targetalias = self.joins.gettarget()
        # two falses are for inner toggle state, and activatable
        targetiter = jointree.append(None, [targetalias, '', '', False, False])
        # add all the joins
        for childjoin in self.joins[targetalias]:
            self.rebuildjointree(targetiter, childjoin)
        self.gui['joinview'].expand_all()

    # recursive function to fill jointree from
    def rebuildjointree(self, parentiter, join):
        """Update the join tree store by reading from the JoinManager."""
        newrow = [join.joinalias, join.joinfield.name, join.targetfield.name,
                  join.inner, True]
        newparent = self.gui['jointree'].append(parentiter, newrow)
        for childjoin in self.joins[join.joinalias]:
            self.rebuildjointree(newparent, childjoin)
