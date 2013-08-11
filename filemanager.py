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

import needtableerror


class FileManager(object):
    """Manages opening, closing, and providing access to files."""
    def __init__(self):
        # all variables are meant to be accessed through functions
        # filesbyfilename[filename] = Table
        # or for files with multiple tables
        # filesbyfilename[filename_tablename] = Table
        self.filesbyfilename = {}
        # filenamesbyalias[alias] = filename or filename_tablename
        self.filenamesbyalias = {}
        # usable filetypes (and initial directory)
        self.filetypes = {}
        self.filetypes['All files'] = {'mimes': [], 'patterns': ['*']}
        self.filetypes['dbf files'] = {'mimes': ['application/dbase',
                                                 'application/x-dbase',
                                                 'application/dbf',
                                                 'application/x-dbf'],
                                       'patterns': ['*.dbf']}
        self.filetypes['csv files'] = {'mimes': ['text/csv'],
                                       'patterns': ['*.csv']}
        # If two aliases point to one file, only one will be used as the table
        # name
        self.filehandlers = {}
        # XXX do this separate from init?
        self.inithandlers()

    def inithandlers(self):
        """Parses filetypes/registry and loads all the defined modules."""
        os.chdir('filetypes')
        registryfile = open('registry', 'r')
        reader = csv.DictReader(registryfile)
        for row in reader:
            # store a reference to each class by file extension
            extension = row['extension']
            if extension[0] == '.':
                extension = extension[1:]
            modulename = row['module']
            classname = row['class']

            module = __import__('filetypes.' + modulename, fromlist=[None])
            self.filehandlers[extension] = module.__dict__[classname]
        registryfile.close()
        os.chdir('..')

    def addfile(self, filename, tablename=None):
        """Open a new file. If file is already open, add an alias for it."""
        # check if file is already opened. files are referenced by filepath or
        # by path_tablename if the file contains multiple tables
        fullfilename = filename
        if tablename is not None:
            fullfilename += '_' + tablename
        alias = self.createalias(filename, tablename)
        if fullfilename in self.filesbyfilename:
            # use existing file
            # XXX just return here when automatic aliasing is added
            newfile = self.filesbyfilename[filename]
        else:
            # create new file
            fileext = filename.split('.')[-1]
            # If a table name was not passed
            if tablename is None:
                # try opening the file as if it only contains one table of data
                try:
                    newfile = self.filehandlers[fileext](filename)
                # if it contains more than one table, return the list of tables
                except needtableerror.NeedTableError as e:
                    return e.tablelist
            else:
                # if a table name was passed, then open that table
                newfile = self.filehandlers[fileext](filename, tablename)
            self.filesbyfilename[fullfilename] = newfile

        self.filenamesbyalias[alias] = fullfilename

        return alias

    def createalias(self, inputname, tablename=None):
        """Creates a unique alias for a file."""
        filenamesplit = re.findall('[a-zA-Z0-9]+', inputname)
        alias = filenamesplit[-2]
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
        return self.addfile(datatable.filename, datatable.tablename)

    def removealias(self, alias):
        """Remove an alias and remove the file if it has no other aliases."""
        filename = self.filenamesbyalias[alias]
        del self.filenamesbyalias[alias]
        # if the file has no other alias pointing to it, close and remove it
        if filename not in self.filenamesbyalias.values():
            self.filesbyfilename[filename].close()
            del self.filesbyfilename[filename]

    def openoutputfile(self, filename):
        """Returns a file, with the given filename opened for writing."""
        fileext = filename.split('.')[-1]
        return self.filehandlers[fileext](filename, mode='w')

    def __getitem__(self, key):
        """Return a file object given either a file name or alias"""
        if key in self.filenamesbyalias:
            return self.filesbyfilename[self.filenamesbyalias[key]]

    def __iter__(self):
        return iter([self.filesbyfilename[fn] for fn in self.filesbyfilename])
