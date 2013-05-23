# -*- coding: utf-8 -*-
# maybe unneeded?
class Record(dict):
    def __init__(self):
        dict.__init__()
        
    def __getitem__(self, key):
        return dict.__getitem__[key]
    
    def __setitem__(self, key, value):
        dict.__setitem__(key, value)