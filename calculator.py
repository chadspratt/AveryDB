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

from fieldcalcs import defaultfuncs


# not sure if this needs to be in a class. lots of scope ambiguity to test
class Calculator(object):
    """This class creates custom functions for each of the output fields."""
    def __init__(self):
        self.outputfuncs = {}
        self.inputblanks = {}
        self.moremodules = {}

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
                if components[0] in dir(defaultfuncs):
                    # prepend 'defaultfuncs.' to the function name
                    newfuncbody = re.sub(funcname,
                                         'defaultfuncs.' + funcname,
                                         newfuncbody)
                # otherwise assume it's a builtin and leave it alone
            else:
                # if it has a module name, make sure the module is imported
                module = components[0]
                if module not in globals() and module not in self.moremodules:
                    try:
                        # try this way in case it's a python library module
                        self.moremodules[module] = __import__(module)
                    except ImportError:
                        # assume it's a fieldcals module
                        self.moremodules[module] = __import__('fieldcalcs.' +
                                                              module,
                                                              globals(),
                                                              locals(),
                                                              [module])
                if module in self.moremodules:
                    # replace the module name with a reference to the locally
                    # imported module
                    newmodule = 'self.moremodules["' + module + '"]'
                    newfuncbody = re.sub(module, newmodule, newfuncbody)

        # define the new function to wrap the expression
        newfuncstr = 'def ' + newfuncname + '(self, args):\n'
        newfuncstr = newfuncstr + '    return ' + newfuncbody

        # XXX print statement
        print newfuncstr

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
