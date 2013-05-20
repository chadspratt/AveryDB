# -*- coding: utf-8 -*-
# Template for different filetype wrappers so that JoinFile can treat them all the same

import field

class GenericFile:
    def __init__(self):
        return 'define __init__'
    def getfields(self):
        return 'define getfields'
    def close(self):
        return 'define close'
#    def read(i)
#    def readnext()
#    def __iter__()
#    def write()