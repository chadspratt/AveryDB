# -*- coding: utf-8 -*-
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
# handles the configuration and execution of the join operation
# should I seperate output? i think i can do it

import join

class JoinManager(object):
    def __init__(self):
        # joins[alias] = [Join0, Join1, ...]
        self.joins = {}
        self.targetalias = ''
        # List of currently joined aliases. each file is limited to joining once
        # for successive joins, the file needs to be reopened to get a new alias
        # The target alias also can't be joined to any other files
        self.joinedaliases = []
        
    def settarget(self, targetalias):
        if targetalias != self.targetalias:
            self.targetalias = targetalias
            self.joins = {}
            self.joinedaliases = [targetalias]
    
    def gettarget(self):
        return self.targetalias        
        
    def removealias(self, alias):
        """Remove all joins that depend on a file."""
        # remove where this file is joined to others
        for targetalias in self.joins:
            for joindefinition in self.joins[targetalias]:
                if joindefinition.joinalias == alias:
                    self.joins[targetalias].remove(joindefinition)
        # remove all joins to this alias
        self.removejoins(alias)
        if self.targetalias == alias:
            self.targetalias = ''

    def removejoins(self, alias):
        """Recursively remove joins to this alias and child joins."""
        if alias in self.joins:
            # For each join to this alias
            for joindefinition in self.joins[alias]:
                # remove the joins from the joined alias
                self.removejoins(joindefinition.joinalias)
            del self.joins[alias]
        # remove the joined alias from the list of all joined aliases
        self.joinedaliases.remove(alias)
        
    # Check that joinalias is joined to targetalias, either directly or through intermediate files
    def checkjoin(self, joinalias, targetalias):
        """Check that a file is joined to the primary target and can therefore be used as a target."""
        if targetalias == joinalias:
            return True
        if targetalias in self.joins:
            targetjoins = self.joins[targetalias]
        else:
            return False
        # recursively check each file joined to targetalias
        for entry in targetjoins:
            if self.checkjoin(entry.joinalias, joinalias):
                return True
        return False
    
    def addjoin(self, joinalias, joinfield, targetalias, targetfield):
        """Create a Join and add it to the dictionary of all Joins."""
        # Limit files to joining once. This avoids problems with circular joins,
        # removing joins, and unexpected messes in rare cases
        if joinalias in self.joinedaliases:
            return joinalias + ' already in use. Open the file again for a different alias.'
        newjoin = join.Join(joinalias, joinfield, targetalias, targetfield)
        if targetalias in self.joins:
            self.joins[targetalias].append(newjoin)
        else:
            self.joins[targetalias] = [newjoin]
        self.joinedaliases.append(joinalias)
        return newjoin
            
    # If I have __iter__ do I need this?
    # used in initoutput() and dojoin()
    def getjoinedaliases(self, start='target'):
        """Return a list of the target and everything joined to it, in depth-first search order."""
        if start == 'target':
            start = self.targetalias
        return self.joinsdfs(start)
    
#    def getjoindepth(self, start='target', depth=0):
#        if start == 'target':
#            start = self.targetalias
#        fulldepth = depth
#        if start in self.joins:
#            for entry in self.joins[start]:
#                fulldepth = max(fulldepth, self.getjoindepth(entry.joinalias, depth+1))
#        return fulldepth
        
                
    def joinsdfs(self, start):
        joinlist = [start]
        if start in self.joins:
            for entry in self.joins[start]:
                joinlist.extend(self.joinsdfs(entry.joinalias))
        return joinlist
                 
    def __getitem__(self, target):
        if target in self.joins:
            return self.joins[target]
        return []
        
    # not used
    def __contains__(self, value):
        return value in self.joins
    
    # untested
    def __iter__(self):
        joinlists = []
        for filealias in self.getjoinedaliases():
            if filealias in self.joins:
                joinlists.append(self.joins[filealias])
        return iter(joinlists)
        