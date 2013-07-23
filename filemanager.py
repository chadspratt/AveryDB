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
import sqlite3

import joinfile


class FileManager(object):
    """Manages opening, closing, and providing access to files."""
    def __init__(self):
        # all variables are meant to be accessed through functions
        # filesbyfilename[filename] = JoinFile
        self.filesbyfilename = {}
        # filenamesbyalias[alias] = filename
        self.filenamesbyalias = {}
        # usable filetypes (and initial directory)
        self.filetypes = {}
        self.filetypes['All files'] = {'mimes': [], 'patterns': ['*']}
        self.filetypes['dbf files'] = {'mimes': ['application/dbase',
                                                 'application/x-dbase',
                                                 'application/dbf',
                                                 'application/x-dbf'],
                                       'patterns': ['*.dbf']}
        # clear the sqlite db. could alternately do this on program close
        sqlitefile = open('temp.db', 'w')
        sqlitefile.truncate(0)
        sqlitefile.close()
        # If two aliases point to one file, only one will be used as the table
        # name
        # table names by filename
        self.tablesbyfilename = {}
        # table names by alias
        self.tablesbyalias = {}

    def addfile(self, filename):
        """Open a new file. If file is already open, add an alias for it."""
        # check if file is already opened
        if filename in self.filesbyfilename:
            newfile = self.filesbyfilename[filename]
        else:
            # open the file. need to catch exceptions in JoinFile
            newfile = joinfile.JoinFile(filename)
            self.filesbyfilename[filename] = newfile

        # get a unique alias (in case another loaded file has the same name)
        filealias = newfile.generatealias()
        while filealias in self.filenamesbyalias:
            filealias = newfile.generatealias()
        self.filenamesbyalias[filealias] = filename

        return filealias

    def removealias(self, alias):
        """Remove an alias and remove the file if it has no other aliases."""
        filename = self.filenamesbyalias[alias]
        del self.filenamesbyalias[alias]
        # if the file has no other alias pointing to it, close and remove it
        if filename not in self.filenamesbyalias.values():
            self.filesbyfilename[filename].close()
            del self.filesbyfilename[filename]

    # long-running, should yield periodically so the GUI can function
    def converttosqlite(self, alias):
        """Create an sqlite table to use instead of the filehandler."""
        # check that the file wasn't removed before it could be converted
        if alias not in self.filenamesbyalias:
            return
        filename = self.filenamesbyalias[alias]
        # check if the sqlite table has already been created
        if filename in self.tablesbyfilename:
            self.tablesbyalias[alias] = self.tablesbyfilename[filename]
            return
        # append an arbitrary string to avoid using reserved words
        self.tablesbyalias[alias] = 'table_' + alias
        alias = self.tablesbyalias[alias]
        print self.tablesbyalias
        # open the file and get the field names
        inputfile = self.filesbyfilename[filename]
        fields = inputfile.getfields()
        fieldnames = [field.name for field in fields]
        # create a string of question marks for the queries
        # one question mark for each field. four fields = '?, ?, ?, ?'
        qmarklist = []
        for x in range(len(fieldnames)):
            qmarklist.append('?')
        qmarks = ', '.join(qmarklist)

        # open the database
        conn = sqlite3.connect('temp.db')
        cur = conn.cursor()
        # create the table
        print 'CREATE TABLE "' + alias + """" ('""" + "', '".join(fieldnames) + "')"
        cur.execute('CREATE TABLE "' + alias + """" ('""" + "', '".join(fieldnames) + "')")
#        cur.execute('CREATE TABLE ' + alias + ' (' + qmarks + ');', fieldnames)
        # insert all the records
        recordcount = inputfile.getrecordcount()
        i = 0
        insertquery = 'INSERT INTO "' + alias + '" VALUES (' + qmarks + ');'
        print insertquery
        while i < recordcount:
            # process however many records before pausing
            for i in range(i, min(i + 250, recordcount)):
                record = inputfile[i]
                values = [record[fn] for fn in fieldnames]
                cur.execute(insertquery, values)
                i += 1
            # Take a break so the gui can be used
            yield float(i) / recordcount
        # save the name of the table for this filename
        self.tablesbyfilename[filename] = alias
        conn.commit()

    def buildsqlindex(self, indexalias, indexfield):
        # open the database
        conn = sqlite3.connect('temp.db')
        cur = conn.cursor()
        print ('CREATE INDEX ' + indexfield + '_index ON ' +
               self.tablesbyalias[indexalias] + '(' + indexfield + ')')
        try:
            cur.execute('CREATE INDEX ' + indexfield + '_index ON ' +
                        self.tablesbyalias[indexalias] + '(' + indexfield + ')')
        # index may already exist
        except sqlite3.OperationalError:
            pass

    def getallfields(self):
        fields = {}
        for fieldalias in self.filenamesbyalias:
            fields[fieldalias] = self[fieldalias].getfields()
        return fields

    @classmethod
    def openoutputfile(cls, filename):
        """Returns a file, with the given filename opened for writing."""
        return joinfile.JoinFile(filename, mode='w')

    def __getitem__(self, key):
        """Return a file object given either a file name or alias"""
        if key in self.filenamesbyalias:
            return self.filesbyfilename[self.filenamesbyalias[key]]

    def __iter__(self):
        return iter([self.filesbyfilename[fn] for fn in self.filesbyfilename])
