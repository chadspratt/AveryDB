# -*- coding: utf-8 -*-
#  just a struct

class Join(object):
    def __init__(self, joinalias='', joinfield='', targetalias='', targetfield=''):
        self.joinalias = joinalias
        self.joinfield = joinfield
        self.targetalias = targetalias #probably not needed
        self.targetfield = targetfield
        