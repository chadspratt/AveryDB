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
import unittest
#import os
import sys
sys.path.insert(0, '..')

import datafile


class TestDBFDataFile(unittest.TestCase):
    def setUp(self):
        self.testfile = datafile.DataFile('parcels.dbf')

    def test_getfields(self):
        testfields = self.testfile.getfields()
        self.assertEqual(len(testfields), 7)
        fieldnames = [testfield.name for testfield in testfields]
        expectednames = ['OBJECTID_1', 'OBJECTID', 'ABSTORSUBN', 'ABSTORSU_1',
                         'PROP_ID', 'SHAPE_AREA', 'SHAPE_LEN']
        self.assertListEqual(fieldnames, expectednames)

    def test_getnewalias(self):
        self.assertEqual(self.testfile.getnewalias(), 'parcels')
        self.assertEqual(self.testfile.getnewalias(), 'parcels1')
        self.assertEqual(self.testfile.getnewalias(), 'parcels2')

    def test_getrecordcount(self):
        self.assertEqual(self.testfile.getrecordcount(), 89)

    def test_getattributenames(self):
        self.assertListEqual(self.testfile.getattributenames(),
                             ['Name', 'Type', 'Length', 'Decimals', 'Value'])

    def tearDown(self):
        self.testfile.close()

if __name__ == '__main__':
    unittest.main()
