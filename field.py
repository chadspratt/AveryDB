# -*- coding: utf-8 -*-

class Field:
    def __init__(self, fieldname, fieldtype, fieldlen, fielddec):
        self.name = fieldname
        self.type = fieldtype
        self.len = fieldlen
        self.dec = fielddec