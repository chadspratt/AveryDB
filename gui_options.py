"""Event handlers for the options window."""
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


class GUI_Options(object):
    """Handles everything in the options window."""
    def __init__(self):
        self.optionhandlers = {'default_output_dir': self.initdefaultoutput}

    def showoptions(self, _widget, _data=None):
        """Load all the settings from the config file into the gui."""
        self.gui['defaultoutputentry'].set_text(self.options['default_output_dir'])
        self.gui['extrafieldlengthspin'].set_value(self.options['extra_field_length'])
        self.gui['optionswindow'].show_all()

    def saveoptions(self, _widget, _data=None):
        # Default output location
        self.options['default_output_dir'] = self.gui['defaultoutputentry'].get_text()
        # Extra padding to add to autodetected field lengths
        extrafieldlengthspin = self.gui['extrafieldlengthspin']
        # update to be sure to get the value in case it was typed in
        extrafieldlengthspin.update()
        self.options['extra_field_length'] = extrafieldlengthspin.get_value_as_int()
        print 'extra_field_length:', self.options['extra_field_length']
        self.options.saveoptions()

    def savecloseoptions(self, _widget, _data=None):
        self.saveoptions(None)
        self.gui['optionswindow'].hide()

    # called for the window delete and cancel button
    def closeoptions(self, _widget, _data=None):
        self.gui['optionswindow'].hide()
        # tell gtk not to destroy the window
        return True

    def browsedefaultoutput(self, _widget, _data=None):
        setdefaultoutputdialog = self.gui.filedialog(self.files.filetypes, folder=True)
        response = setdefaultoutputdialog.run()
        # check that a file was selected
        if response == gtk.RESPONSE_OK:
            foldername = setdefaultoutputdialog.get_filename()
            self.gui['defaultoutputentry'].set_text(foldername)
        setdefaultoutputdialog.destroy()