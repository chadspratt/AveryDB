# -*- coding: utf-8 -*-
# handles the configuration and execution of the join operation
# should I seperate output? i think i can do it

import join

class JoinManager(object):
    def __init__(self):
        # joins[alias] = [Join0, Join1, ...]
        self.joins = {}
        self.targetalias = ''
        # stores the join currently being configured in the gui
        self.curtarget = ''
        self.curjoin = ''
        
    def settarget(self, targetalias):
        if targetalias != self.targetalias:
            self.targetalias = targetalias
            self.joins = {}
    
    def gettarget(self):
        return self.targetalias        
        
    def removefile(self, alias):
        """Remove all joins that depend on this file."""
        if alias in self.joins:
            self._removejoin(alias)
        # remove where this file is joined to others
        for targetalias in self.joins:
            for joinDefinition in self.joins[targetalias]:
                if joinDefinition.joinfile == alias:
                    self.joins[targetalias].remove(joinDefinition)
        if alias == self.targetalias:
            self.targetalias = ''

    def _removejoin(self, alias):
        """Recursively remove joins to this alias and child joins."""
        for joinDefinition in self.joins[alias]:
            self._removejoin(self, joinDefinition.joinfile)
        del self.joins[alias]
        
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
        # check that the target isn't a child of the file being joined
        if self.checkjoin(targetalias, joinalias):
            return 'Cannot create circular join. Reopen the file to use a different alias.'
        newJoin = join.Join(joinalias, joinfield, targetalias, targetfield)
        if targetalias in self.joins:
            self.joins[targetalias].append(newJoin)
        else:
            self.joins[targetalias] = [newJoin]
        return ''
            
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
        