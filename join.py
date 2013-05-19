# -*- coding: utf-8 -*-
#  just a struct

class Join:
    def __init__(self, targetalias='', targetfield='', joinalias='', joinfield=''):
        self.targetalias = targetalias #probably not necessary
        self.targetfield = targetfield
        self.joinalias = joinalias
        self.joinfield = joinfield