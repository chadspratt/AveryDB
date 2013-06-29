"""JoinManager handles the configuration of the join operation.

JoinManager creates and stores new join definitions and describes the joins to
other parts of the application in useful ways."""
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
# 

import join

class JoinManager(object):
    """Manages creation and access of join definitions."""
    def __init__(self):
        # joins[alias] = [Join0, Join1, ...]
        self.joins = {}
        self.targetalias = ''
        # List of currently joined aliases. each file is limited to joining once
        # for successive joins, the file needs to be reopened to get a new alias
        # The target alias also can't be joined to any other files
        self.joinedaliases = []
        
    def settarget(self, targetalias):
        """Updates the main target alias and clears all configured joins."""
        if targetalias != self.targetalias:
            self.targetalias = targetalias
            self.joins = {}
            self.joinedaliases = [targetalias]
    
    def gettarget(self):
        """Returns the alias of the main target file."""
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
    
    def addjoin(self, joinalias, joinfield, targetalias, targetfield):
        """Create a Join and add it to the dictionary of all Joins."""
        # Limit files to joining once. This avoids problems with circular joins,
        # removing joins, and unexpected messes in rare cases
        if joinalias in self.joinedaliases:
            # XXX raising an exception would be better?
            return joinalias + \
                   ' already in use. Open the file again for a new alias.'
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
        """Returns a list of all joined aliases in depth-first order."""
        if start == 'target':
            start = self.targetalias
        return self._joinsdfs(start)
                
    def _joinsdfs(self, start):
        """Returns a list of all joined aliases in depth-first order."""
        joinlist = [start]
        if start in self.joins:
            for entry in self.joins[start]:
                joinlist.extend(self._joinsdfs(entry.joinalias))
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
        