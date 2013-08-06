"""Event handlers for the function editor window."""
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


class GUI_FunctionEditor(object):
    def showfunceditor(self, _widget, _data=None):
        """Initialize and show the function editor window."""
        # get the selected lib from the combobox
        selectedlibname = self.gui['calclibrarycomboentry'].get_active_text()
        # get the selected function name from the function list
        selection = self.gui['calcfunctionview'].get_selection()
        (functionlist, selectedpath) = selection.get_selected()
        if selectedpath:
            selectedfuncname = functionlist.get_value(selectedpath, 0)
        else:
            selectedfuncname = None
        customlibs = self.calc.getcustomlibs()
        customlibrarylist = self.gui['customlibrarylist']
        customlibrarylist.clear()
        for customlib in customlibs:
            rowiter = customlibrarylist.append([customlib])
            if customlib == selectedlibname:
                # this would call changefunclibrary but on init it needs
                # to use the selected function from the calc window
                funclibcombo = self.gui['funclibrarycombo']
                funclibcombo.handler_block_by_func(self.loadlibraryfunctions)
                funclibcombo.set_active_iter(rowiter)
                funclibcombo.handler_unblock_by_func(self.loadlibraryfunctions)
        # if the lib was custom, load its functions
        if self.gui['funclibrarycombo'].get_active_iter():
            libfunctions = self.calc.getfuncs(selectedlibname)
            customfunctionlist = self.gui['customfunctionlist']
            customfunctionlist.clear()
            for libname, _libdoc in libfunctions:
                rowiter = customfunctionlist.append([libname])
                if libname == selectedfuncname:
                    # this will trigger changefuncfunction to init the text
                    self.gui['funcfunctioncombo'].set_active_iter(rowiter)
        self.gui['funcwindow'].show_all()

    def hidefunceditor(self, _widget, _data=None):
        """Hide the function editor in response to a destroy event."""
        self.gui['funcwindow'].hide()
        return True

    def getlibraryname(self, _widget, _data=None):
        """Show a dialog to ask for a new function name."""
        self.gui['newlibentry'].set_text('')
        self.gui['newlibdialog'].show()

    def createlibrary(self, _widget, _data=None):
        """Create a new library file with the user-provided library name."""
        libname = self.gui['newlibentry'].get_text()
        self.calc.createlib(libname)
        self.gui['newlibdialog'].hide()
        # refresh the different library lists
        self.showfunceditor(None)
        self.showcalculator(None)

    def cancelcreatelibrary(self, _widget, _data=None):
        """Hide the library name dialog without creating anything."""
        self.gui['newlibdialog'].hide()

    def loadlibraryfunctions(self, widget, _data=None):
        """Update calc value box when the calc output field combo changes."""
        libname = widget.get_active_text()
        if libname is not None:
            libfunctions = self.calc.getfuncs(libname)
            customfunctionlist = self.gui['customfunctionlist']
            customfunctionlist.clear()
            for funcname, _funcdoc in libfunctions:
                customfunctionlist.append([funcname])

    def loadfunctiontext(self, _widget, _data=None):
        """Update calc value box when the calc output field combo changes."""
        libname = self.gui['funclibrarycombo'].get_active_text()
        funcname = self.gui['funcfunctioncombo'].get_active_text()
        if funcname:
            functext = self.calc.getfunctext(libname, funcname)
            valuebuffer = self.gui['funceditingtextview'].get_buffer()
            valuebuffer.set_text(functext)

    def savefunction(self, _widget, _data=None):
        """Write the contents of the editor to the selected library.

        Whatever is in the text editing area will be written to the library
        selected in the combobox at the top of the function editor window.
        If the function alread exists it will be overwritten. If the input is
        not a function it will probably cause problems and the file will need
        to be opened in an external editor and cleaned."""
        libname = self.gui['funclibrarycombo'].get_active_text()
        funcbuffer = self.gui['funceditingtextview'].get_buffer()
        functext = funcbuffer.get_text(funcbuffer.get_start_iter(),
                                       funcbuffer.get_end_iter())
        self.calc.writefunctext(libname, functext)
        self.loadfunctiontext(None)

    def saveclosefunction(self, _widget, _data=None):
        """Save the contents of the editor and close the function editor."""
        self.savefunction(None)
        self.hidefunceditor(None)
