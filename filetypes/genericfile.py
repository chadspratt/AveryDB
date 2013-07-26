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
# Template for different filetype wrappers


class GenericFile(object):
    def __init__(self, filename, mode='r'):
        return 'define __init__'

    def getfields(self):
        """Get the field definitions from an input file."""
        return 'define getfields'

    def setfields(self, newfield):
        """Set the field definitions of an output file."""
        return 'define setfields'

    def addrecord(self, newrecord):
        """Write a record (stored as a dictionary) to the output file."""
        return 'define addrecord'

    def close(self):
        """Close the output file. Input files close automatically."""
        return 'define close'

    def __iter__():
        """Get the records from an input file in sequence."""
        return 'define __iter__'
