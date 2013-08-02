# -*- coding: utf-8 -*-
"""
Created on Sun Jun 30 20:07:08 2013

@author: chad
"""


def area(height, width):
    return height * width


# test comment
def concat(field1, field2):
    return str(field1) + ' ' + str(field2)


def halfstring(inputstr):
    """Return the first half of a string."""
    strlen = len(inputstr)
    return  inputstr[:strlen / 2]


def propertyfrompropid(propid):
    """Convert int propid to R0* padded string."""
    strid = str(propid)
    idlen = len(strid)
    prefix = 'R'
    padding = 4 - idlen
    if padding > 0:
        prefix += '0' * padding
    return prefix + strid
