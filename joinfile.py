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
# import all filetypes even if unreadable (arcpy)?
# test for ability to read/write gis databases with arcpy
from filetypes import dbffile


class JoinFile(object):
    """Used to open, read and write all files of all supported types."""
    def __init__(self, filename='', mode='r'):
        self.filename = filename
        self.indices = {}
        if filename != '':
            try:
                self.filehandler = self.openfile(filename, mode=mode)
            except ValueError:
                print 'Invalid file type'
        self.aliasgenerator = self._generatealias()

    @classmethod
    def openfile(cls, filename, mode='r'):
        """Supplies an abstracted file handler for different file formats."""
        lowercase_filename = filename.lower()
        # This is the only code that treats different file types differently
        if lowercase_filename.endswith('dbf'):
            filehandler = dbffile.DBFFile(filename, mode=mode)
        else:
            #this won't happen unless selecting invalid files is allowed
            raise ValueError

        return filehandler

    def getfields(self):
        """Returns a list of field objects."""
        return self.filehandler.getfields()

    # generate and return an alias for the file. Each time a file is opened
    def _generatealias(self):
        """Creates a unique alias for a file."""
        filenamesplit = re.findall('[a-zA-Z0-9]+', self.filename)
        alias = filenamesplit[-2]
        # start with just the filename
        yield alias
        # append a number for successive alias requests
        dupecount = 1
        aliaslen = len(alias)  # store original length
        while True:
            # append next number to original alias
            alias = alias[:aliaslen] + str(dupecount)
            yield alias
            dupecount += 1

    def generatealias(self):
        """Returns a modified, hopefully unique, file alias."""
        return self.aliasgenerator.next()

    def addfield(self, field):
        """Calls the file handler's addfield."""
        self.filehandler.addfield(field)

    def getrecordcount(self):
        """Call the file handler's getrecordcount to return the total count."""
        return self.filehandler.getrecordcount()

    def buildindex(self, fieldname):
        """Builds an index of a given field."""
        # check if it's already built. highly unlikely
        if fieldname in self.indices:
            return
        print 'building index: ', self.filename, ' - ', fieldname, '\n'
        recordcount = self.filehandler.getrecordcount()
        fieldindex = {}
        i = 0
        while i < recordcount:
            # process however many records before pausing
            for i in range(i, min(i + 250, recordcount)):
                # store the index of a record by the value of the join field
                # this doesn't check for duplicates since we can only use one
                # record when doing a join. If a value appears in more than
                # one record, the last record is used (out of convenience)
                fieldindex[self[i][fieldname]] = i
                i += 1
            # Take a break so the gui can be used
            yield float(i) / recordcount

        self.indices[fieldname] = fieldindex

    def getjoinrecord(self, fieldname, fieldvalue):
        """Returns a record with a given value for a given field."""
        if fieldname in self.indices:
            if fieldvalue in self.indices[fieldname]:
                recordindex = self.indices[fieldname][fieldvalue]
                return self[recordindex]

    def addrecord(self, newrecord):
        """Calls the file handler's addrecord."""
        self.filehandler.addrecord(newrecord)

    def close(self):
        """Calls the file handler's close."""
        self.filehandler.close()

    def __getitem__(self, index):
        return self.filehandler[index]
