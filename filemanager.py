"""FileManager handles all adding, removing, and delivery of files.

It doesn't do anything further with the files."""
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
#
import csv
import os
import re
from collections import OrderedDict

from table import NeedTableError
from table import InvalidDataError


class FileManager(object):
    """Manages opening, closing, and providing access to files."""
    def __init__(self):
        # filesbyfilename[filename] = Table
        # or for files with multiple tables
        # filesbyfilename[filename_tablename] = Table
        self.filesbyfilename = {}
        # filenamesbyalias[alias] = filename or filename_tablename
        self.filenamesbyalias = {}
        self.removedfiles = {}
        # usable filetypes (and initial directory)
        self.filetypes = OrderedDict()
        # filehandlers['.fileextension'] = format handler object from filetypes
        # the order of the handlers is the order that they're tried, in case
        # the file just has the wrong extension. csv is last in the registry
        # becauase it is likely to get a false-positive.
        self.filehandlers = OrderedDict()
        # XXX do this separate from init?
        self.initfiletypes()

    def inithandler(self, extension, modulename, classname):
        """Loads a module for handling a filetype."""
        extension = extension.upper()
        module = __import__('filetypes.' + modulename, fromlist=[None])
        self.filehandlers[extension] = module.__dict__[classname]

    def initfiletypes(self):
        """Create a dictionary for use by a file dialog to filter files."""
        # By putting this first, it will be the default option
        self.filetypes['All supported'] = {'mimes': [], 'patterns': []}
        # open the registry file
        os.chdir('filetypes')
        registryfile = open('registry', 'r')
        reader = csv.DictReader(registryfile)
        for row in reader:
            descrip = row['description']
            extension = row['extension']
            modulename = row['module']
            classname = row['class']
            try:
                self.inithandler(extension, modulename, classname)
            # don't include the format if the module couldn't be loaded
            except ImportError:
                continue
            # store/group extensions by description
            if descrip in self.filetypes:
                self.filetypes[descrip]['patterns'].append('*' + extension)
            else:
                self.filetypes[descrip] = {'mimes': [],
                                           'patterns': ['*' + extension]}
            self.filetypes['All supported']['patterns'].append('*' + extension)
        # put last so it appears last, catchall in case a file isn't named well
        self.filetypes['All files'] = {'mimes': [], 'patterns': ['*']}
        registryfile.close()
        os.chdir('..')

    def addfile(self, filename, tablename=None):
        """Open a new file. If file is already open, add an alias for it."""
        # check if file is already opened. files are referenced by filepath or
        # by path_tablename if the file contains multiple tables
        fullfilename = filename
        if tablename is not None:
            fullfilename += '_table_' + tablename

        if fullfilename in self.removedfiles:
            alias = self.removedfiles[fullfilename]
            del self.removedfiles[fullfilename]
            return alias
        elif fullfilename in self.filesbyfilename:
            # data has already been added
            return None

        alias = self.createalias(filename, tablename)
        # create new file
        fileext = '.' + filename.split('.')[-1]
        # a table name was not passed
        if tablename is None:
            # try opening the file as if it only contains one table of data
            try:
                newfile = self.filehandlers[fileext.upper()](filename)
            # if it contains more than one table, return the list of tables
            except NeedTableError as e:
                if len(e.tablelist) == 0:
                    print 'No data in file.'
                    return None
                return e.tablelist
            # invalid dbf data
            except InvalidDataError as e:
                print 'Data not readable'
                return None
            # any other errors that might occur
            except Exception:
                # try all the other file handlers
                for fileext in self.filehandlers:
                    try:
                        newfile = self.filehandlers[fileext](filename)
                    # found the right format, but missing a table name
                    except NeedTableError as e:
                        if len(e.tablelist) == 0:
                            print 'No data in file.'
                            return None
                        return e.tablelist
                    # haven't found the right format, move to the next
                    except Exception:
                        continue
                    # if it opened successfully, stop
                    print filename + ' is actually of type ' + fileext
                    break
                # if none of them worked, give up
                else:
                    print 'Unsupported data format'
                    return None
        # a table name was passed
        else:
            # if a table name was passed, then open that table
            try:
                newfile = self.filehandlers[fileext.upper()](filename, tablename)
            except Exception:
                # try all the other file handlers
                for fileext in self.filehandlers:
                    try:
                        newfile = self.filehandlers[fileext](filename, tablename)
                    # if it doesn't work, move to the next
                    except Exception:
                        continue
                    # if it does work, stop
                    break
                # if none of them worked, give up
                else:
                    print 'Unsupported data format'
                    return None

        self.filesbyfilename[fullfilename] = newfile
        self.filenamesbyalias[alias] = fullfilename

        return alias

    def createalias(self, inputname, tablename=None):
        """Creates a unique alias for a file."""
        filenamesplit = re.findall('[a-zA-Z0-9]+', inputname)
        # assumes the filename ends with 'name.extension'
        alias = filenamesplit[-2]
        # don't start an alias with a number, sqlite dislikes it
        if alias[0].isdigit():
            alias = '_' + alias
        if tablename is not None:
            alias += tablename
        # append a number for successive alias requests
        dupecount = 1
        aliaslen = len(alias)  # store original length
        while alias in self.filenamesbyalias:
            # append next number to original alias
            alias = alias[:aliaslen] + str(dupecount)
            dupecount += 1
        return alias

    def addnewalias(self, alias):
        """Add a new alias to a table (table is specificed by alias)."""
        datatable = self[alias]
        newalias = self.createalias(datatable.filename, datatable.tablename)
        self.filenamesbyalias[newalias] = self.filenamesbyalias[alias]
        return newalias

    def removealias(self, alias):
        """Remove an alias and remove the file if it has no other aliases."""
        filename = self.filenamesbyalias[alias]
        # doing nothing is preferable
        self.removedfiles[filename] = alias
        return
        del self.filenamesbyalias[alias]
        # if the file has no other alias pointing to it, close and remove it
        if filename not in self.filenamesbyalias.values():
            self.filesbyfilename[filename].close()
            del self.filesbyfilename[filename]

    def openoutputfile(self, filename, fileext, tablename=None):
        """Returns a file for writing."""
        if fileext is None:
            return None
        # if the filext string contains a list of extensions, use the first
        if re.search(r'\,', fileext):
            fileext = re.match(r'[^,]+', fileext).group(0)
        # instantiate a filehandler
        outputfile = self.filehandlers[fileext.upper()](filename + fileext,
                                                        tablename, mode='w')
        return outputfile

    def __getitem__(self, key):
        """Return a file object given either a file name or alias"""
        if key in self.filenamesbyalias:
            return self.filesbyfilename[self.filenamesbyalias[key]]

    def __iter__(self):
        return iter([self.filesbyfilename[fn] for fn in self.filesbyfilename])
