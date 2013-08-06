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
        targetfieldlist = self.gui['targetfieldlist']
        for row in targetfieldlist:
            if value in row:
                self.gui['targetfieldcombo'].set_active_iter(row.iter)
                return

    # 'apply' join choice button
    def addjoin(self, _widget, _data=None):
        """Save join using the selected fields in the gui."""
        # get combobox selections
        joinalias = self.gui['joinaliascombo'].get_active_text()
        joinfield = self.gui['joinfieldcombo'].get_active_text()
        targetalias = self.gui['targetaliascombo'].get_active_text()
        targetfield = self.gui['targetfieldcombo'].get_active_text()

        if joinfield is not None and targetfield is not None:
            # save to joins
            result = self.joins.addjoin(joinalias, joinfield,
                                        targetalias, targetfield)
            # check if the result is an error message
            if type(result) == str:
                self.gui.messagedialog(result)
            # otherwise result is the new Join
            else:
                self.refreshjoinlists()
                self.queuetask(('index', result))
                self.queuetask(('sample', None))
                self.processtasks()

    def removejoin(self, _widget, _data=None):
        """Removes the selected joins and any child joins dependent on it."""
        selection = self.gui['joinview'].get_selection()
        (outputlist, selectedrow) = selection.get_selected()
        joinalias = outputlist[selectedrow][0]
        self.joins.removealias(joinalias)
        self.refreshjoinlists()
