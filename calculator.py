"""Converts input records to output records.

This class takes input values and python statements and computes the output
values.
"""
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
import os
from collections import OrderedDict

# libraries to preload and list in the calculator dialog
# XXX needs a menu setting to edit it. in place or make a config file?
DEFAULT_LIBRARIES = ['math']


class Calculator(object):
    """This class creates custom functions for each of the output fields."""
    def __init__(self):
        self.outputfuncs = OrderedDict()
        self.inputblanks = {}
        self.moremodules = {}
        # list of all the modules the user can edit
        self.custommodules = ['defaultfuncs']

        for libname in DEFAULT_LIBRARIES:
            self.importlib(libname)
        self.moremodules['builtins'] = __builtins__

        # import everything from the fieldcalcs directory
        customfuncs = os.listdir('fieldcalcs')
        for funcname in customfuncs:
            name, extension = funcname.split('.')
            if extension == 'py':
                self.importlib(name)
                if name not in self.custommodules:
                    self.custommodules.append(name)

    def clear(self):
        """Clear the list of dynamically generated output functions."""
        self.outputfuncs = OrderedDict()

    def importlib(self, libname):
        """Import a library for the calculator to use."""
        libname = libname.strip()
        if libname is '':
            return
        if libname not in self.moremodules:
            try:
                # try this way in case it's a python library module
                self.moremodules[libname] = __import__(libname)
            except ImportError:
                # assume it's a fieldcals module
                self.moremodules[libname] = __import__('fieldcalcs.' +
                                                       libname,
                                                       globals(),
                                                       locals(),
                                                       [libname])

    def getlibs(self):
        """Get a list of all libraries currently imported for field calcs."""
        return self.moremodules

    def getcustomlibs(self):
        """Get a list of all the custom libraries."""
        return self.custommodules

    def getfuncs(self, libname):
        """Get the names of all public functions in a library."""
        if libname is '':
            return
        if libname not in self.moremodules:
            self.importlib(libname)
        libfuncs = []
        # get a list of all the names defined in the function
        names = dir(self.moremodules[libname])
        for name in names:
            libobject = getattr(self.moremodules[libname], name)
            # filter out other modules that were imported
            if callable(libobject):
                # filter out private methods:
                if not name.startswith('_'):
                    # return a tuple of the function name and docstring
                    libfuncs.append((name, libobject.__doc__))
        return libfuncs

    # this is only used for custom functions defined in a fieldcalcs module
    @classmethod
    def getfunctext(cls, libname, funcname):
        """Parse a library file and get the full text of a given function."""
        os.chdir('fieldcalcs')
        libfile = open(libname + '.py', 'r')
        os.chdir('..')

        libtext = libfile.readlines()
        libfile.close()
        i = 0
        funcstart = -1
        funcend = -1
        # find the start of the function
        while i < len(libtext):
            if re.findall('def ' + funcname, libtext[i]):
                funcstart = i
                # backtrack and grab comments that precede the function
                while libtext[funcstart - 1].strip().startswith('#'):
                    funcstart -= 1
                break
            i += 1
        else:
            # function not found
            return ''
        # find the end of the function
        i += 1
        while i < len(libtext):
            if libtext[i].startswith('    '):
                funcend = i
                i += 1
            else:
                break

        # return the function as a single string
        return ''.join(libtext[funcstart:funcend + 1])

    @classmethod
    def getfuncbounds(cls, libname, funcname):
        """Parse a library file and get the full text of a given function."""
        os.chdir('fieldcalcs')
        libfile = open(libname + '.py', 'r')
        os.chdir('..')

        libtext = libfile.readlines()
        libfile.close()
        i = 0
        funcstart = -1
        funcend = -1
        # find the start of the function
        while i < len(libtext):
            if re.findall('def ' + funcname, libtext[i]):
                funcstart = i
                # backtrack and grab comments that precede the function
                while libtext[funcstart - 1].strip().startswith('#'):
                    funcstart -= 1
                break
            i += 1
        else:
            # function not found
            return (None, None)
        # find the end of the function
        i += 1
        while i < len(libtext):
            if libtext[i].startswith('    '):
                funcend = i
                i += 1
            else:
                break

        # return the function as a single string
        return (funcstart, funcend)

    def writefunctext(self, libname, functext):
        """Save a function written in the gui to a file."""
        # extract the function name from the function text.
        funcname = re.findall(r'def ([a-zA-Z_][a-zA-Z_0-9]*)\(', functext)[0]
        curfuncstart, curfuncend = self.getfuncbounds(libname, funcname)
        os.chdir('fieldcalcs')
        libfile = open(libname + '.py', 'r')
        fulllibtext = libfile.readlines()
        libfile.close()
        # if the function is already in the file, replace it
        if curfuncstart:
            libfile = open(libname + '.py', 'w')
            libfile.truncate(0)
            # Add the portion of the library before the function being replaced
            outputtext = ''.join(fulllibtext[:curfuncstart])
            # Add the new function to lines
            outputtext = outputtext + functext
            # Add the portion of the library after the function being replaced
            outputtext = outputtext + ''.join(fulllibtext[curfuncend + 1:])
            libfile.write(outputtext)
        else:
            libfile = open(libname + '.py', 'a')
            libfile.write('\n\n' + functext)
        libfile.close()
        os.chdir('..')
        # reload the module so the new function can be used
        self.moremodules[libname] = reload(self.moremodules[libname])

    # doesn't need to be speedy
    def createoutputfunc(self, field):
        """Converts an expression to a single function call.

        Converts field['value'] to a function that can be quickly executed
        during output.

        The field value can contain several types of arguments:
        * constant values: 8. 'cat', [0, 1, 2, 3]
        * input field values: !filealias.fieldname!
        * builtin function calls: len(), str(), abs()
        * library function calls: math.sqrt(), os.getcwd()
        * custom functions defined in fieldcalcs.defaultfuncs: pad_ids()
        * functions from a different module in fieldcalcs: streets.fullname()
        (fullname function is defined in streets.py)

        The only extra syntax is for input field values.
        The function assumes the user has written everything correctly.
        """
        newfuncname = field['name']
        newfuncbody = field['value']
        argpos = 0
        # Convert all !filealias.fieldname! to usable argument references
        args = re.findall(r'![a-zA-Z0-9]+\.[a-zA-Z0-9_]+!', newfuncbody)
        for arg in args:
            internalname = 'args[' + str(argpos) + ']'
            argpos += 1
            newfuncbody = re.sub(arg, internalname, newfuncbody)

        # Convert all the function calls to callable references
        funcs = re.findall(r'([a-zA-Z]+[a-zA-Z0-9\._]*)\(', newfuncbody)
        for funcname in funcs:
            components = funcname.split('.')
            # A single word is either a builtin or from defaultfuncs
            if len(components) == 1:
                # check if it's a func in defaultfunc
                if components[0] in dir(self.moremodules['defaultfuncs']):
                    # prepend 'defaultfuncs.' to the function name
                    newfuncbody = re.sub(funcname,
                                         'defaultfuncs.' + funcname,
                                         newfuncbody)
                # otherwise assume it's a builtin and leave it alone
            else:
                # if it has a module name, make sure the module is imported
                module = components[0]
                self.importlib(module)
                if module in self.moremodules:
                    # replace the module name with a reference to the locally
                    # imported module
                    newmodule = 'self.moremodules["' + module + '"]'
                    newfuncbody = re.sub(module, newmodule, newfuncbody)

        # define the new function to wrap the expression
        newfuncstr = 'def ' + newfuncname + '(self, args):\n'
        newfuncstr = newfuncstr + '    return ' + newfuncbody

        # create the function and return it with the list of args it needs
        exec(newfuncstr) in globals(), locals()
        for i in range(len(args)):
            # trim the leading and trailing '!'s and split at the period
            args[i] = args[i][1:-1].split('.')
        self.outputfuncs[newfuncname] = (locals()[newfuncname], args)

    # needs to be speedy
    def calculateoutput(self, inputvalues):
        """Takes all the input records and computes the output record.

        Each of the output functions created by createoutputfunc() is called
        using inputvalues."""
        outputvalues = []
        for outputfieldname in self.outputfuncs:
            outputfunc, args = self.outputfuncs[outputfieldname]
            argvalues = []
            for arg in args:
                if arg[0] in inputvalues:
                    argvalues.append(inputvalues[arg[0]][arg[1]])
                # File didn't join for this record, pass a blank default value
                else:
                    argvalues.append(self.inputblanks[arg[0]][arg[1]])
            outputvalue = outputfunc(self, argvalues)
            outputvalues.append((outputfieldname, outputvalue))
        return outputvalues

    # util function used in dojoin()
    # doesn't need to be speedy
    def addblankvalue(self, filealias, field):
        """Supplies a blank value for a field, based on field type."""
        fieldtype = field['type']
        if fieldtype == 'C':
            blankvalue = ''
        elif fieldtype == 'N':
            blankvalue = 0
        elif fieldtype == 'F':
            blankvalue = 0.0
        # i don't know for this one what a good nonvalue would be
        elif fieldtype == 'D':
            blankvalue = (0, 0, 0)
        elif fieldtype == 'I':
            blankvalue = 0
        elif fieldtype == 'Y':
            blankvalue = 0.0
        elif fieldtype == 'L':
            blankvalue = -1
        elif fieldtype == 'M':
            blankvalue = " " * 10
        elif fieldtype == 'T':
            blankvalue = None
        if filealias in self.inputblanks:
            self.inputblanks[filealias][field['name']] = blankvalue
        else:
            self.inputblanks[filealias] = {field['name']: blankvalue}

    @classmethod
    def reloadcalcfuncs(cls):
        """Reloads the module in case a user has added a new function to it."""
        reload('calcfunctions')
