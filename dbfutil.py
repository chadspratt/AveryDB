#! /usr/bin/python27

## fix the hack of casting all values to float on line 250 of fields.py

import re
from Tkinter import Tk

from gui import App
# used for writing dbf files
from dbfpy import dbf
#import combobox
from join import Join

# fields[filename] = [(fieldname, fieldtype, length, decimalplaces), ...]
fields = {}
target = Join()
curjoin = ''
# used for editing output fields
oldfieldname = ''
oldfieldindex = -1
# [join_dbf_filename] = [targetindex, joinindex]
# joinfields = {}
# joinalias[alias] = join_dbf_filename, joinalis[join_dbf_filename] = alias
joinaliases = {}
# outputfields['fieldname'] = (fieldvalue, fieldtype, fieldlen, fielddec)
# fieldvalue = filename.fieldname
# fieldvalue is meant to support simple operations. 'f1.f1 + f2.f2' for example
outputfields = {}
# joins[targetfile] = [[targetfield, joinfile, joinfield], ...]
joins = {}
# fileindexes['filename'] = {joinvalue : index, ...}
fileindexes = {}









# util function used in dojoin()
# this is all arbitrary
def blankvalue(field):
    fieldtype = field[1]
    if fieldtype == 'N':
        return 0
    elif fieldtype == 'F':
        return 0.0
    elif fieldtype == 'C':
        return ''
    # i don't know for this one what a good nonvalue would be
    elif fieldtype == 'D':
        return (0,0,0)
    elif fieldtype == 'I':
        return 0
    elif fieldtype == 'Y':
        return 0.0
    elif fieldtype == 'L':
        return -1
    elif fieldtype == 'M':
        return " " * 10
    elif fieldtype == 'T':
        return



