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
import random
from collections import OrderedDict

from fieldcalcs import defaultfuncs


# not sure if this needs to be in a class. lots of scope ambiguity to test
class Calculator(object):
    """This class creates custom functions for each of the output fields."""
    def __init__(self):
        self.outputfuncs = OrderedDict()
        self.inputblanks = {}

    # doesn't need to be speedy
    def createoutputfunc(self, field):
        """Converts an expression to a single function call.

        example:
        Takes '!f0.ff0! + example(!f1.ff1!, !f2.ff2!, func2(5), "cat")' and
        creates newfunc(f0ff0, f1ff1, f2ff2) that is equivalent.
        example() and func2() are defined in a separate file, imported here
        Returns newfunc and a list of args: [(f0, ff0), (f1, ff1), (f2, ff2)]
        """
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        # generate a random name. necessary? safe, at least
        newfuncname = ''.join(random.choice(alphabet) for i in range(20))
        newfuncbody = field['value']
        argpos = 0
        # !filealias.fieldname!
        args = re.findall(r'![a-zA-Z0-9]+\.[a-zA-Z0-9_]+!', newfuncbody)
        for arg in args:
            internalname = 'args[' + str(argpos) + ']'
            argpos += 1
            newfuncbody = re.sub(arg, internalname, newfuncbody)

        # funcname(), module.funcname()
        funcs = re.findall(r'([a-zA-Z]+[a-zA-Z0-9\._]*)\(', newfuncbody)
        for funcname in funcs:
            components = funcname.split('.')
            # check for 'defaultfunc.funcname'
            if components[0] not in globals():
                # check if it's a func in defaultfunc
                if components[0] in dir(defaultfuncs):
                    # assume it's in defaultfuncs and append that module
                    newfuncbody = re.sub(funcname,
                                         'defaultfuncs.' + funcname,
                                         newfuncbody)

        # define the new function to wrap the expression
        newfuncstr = 'def ' + newfuncname + '(args):\n'
        newfuncstr = newfuncstr + '    return ' + newfuncbody

        # XXX print statement
        print 'final:\n', newfuncstr

        # create the function and return it with the list of args it needs
        exec(newfuncstr) in globals(), locals()
        for i in range(len(args)):
            # trim the leading and trailing '!'s and split at the period
            args[i] = args[i][1:-1].split('.')
        self.outputfuncs[field['name']] = (locals()[newfuncname], args)

    # needs to be speedy
    def calculateoutput(self, inputvalues):
        outputvalues = []
#        print 'inputvalues', inputvalues
        for outputfieldname in self.outputfuncs:
#            print 'outputfieldname', outputfieldname
            outputfunc, args = self.outputfuncs[outputfieldname]
#            print 'outputfunc, args', outputfunc, args
            # XXX need to account for missing values from missed joins
            argvalues = []
            for arg in args:
                if arg[0] in inputvalues:
                    argvalues.append(inputvalues[arg[0]][arg[1]])
#                    print 'inputvalues[arg[0]][arg[1]]', inputvalues[arg[0]][arg[1]]
                else:
                    argvalues.append(self.inputblanks[arg[0]][arg[1]])
                outputvalue = outputfunc(argvalues)
#                print 'argvalues', argvalues
            outputvalues.append((outputfieldname, outputvalue))
        print outputvalues
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
