# -*- coding: utf-8 -*-
# handles the configuration and execution of the join operation
# should I seperate output? i think i can do it

import join

class JoinManager:
    def __init__(self):
        # joins[alias] = [Join0, Join1, ...]
        self.joins = {}
        self.targetalias = ''
        # stores the join currently being configured in the gui
        self.curtarget = ''
        self.curjoin = ''
        
    def settarget(self, targetFile):
        self.targetFile = targetFile
    
    def gettarget(self):
        return self.target        
        
    def removefile(self, alias):
        """Remove all joins that depend on this file."""
        if alias in self.joins:
            self._removejoin(alias)
        # remove where this file is joined to others
        for targetalias in self.joins:
            for joinDefinition in self.joins[targetalias]:
                if joinDefinition.joinfile == alias:
                    self.joins[targetalias].remove(joinDefinition)

    def _removejoin(self, alias):
        """Recursively remove joins to this alias and child joins."""
        for joinDefinition in self.joins[alias]:
            self._removejoin(self, joinDefinition.joinfile)
        del self.joins[alias]
        
    # Check that joinalias is joined to targetalias, either directly or through intermediate files
    def checkjoin(self, targetalias, joinalias):
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
    
    def addjoin(self, targetfield, joinfield):
        """Create a Join and add it to the dictionary of all Joins."""
        newJoin = join.Join(self.curtarget, targetfield, self.curjoin, joinfield)
        if self.curtarget in self.joins:
            self.joins[self.curtarget].append(newJoin)
        else:
            self.joins[self.curtarget] = [newJoin]
            
    # util function to recursively get all filenames from joins{}
    # used in initoutput() and dojoin()
    def getjoinedaliases(self, start='target'):
        """Recursively generates all aliases joined to a target, starting with the target itself, using depth-first search."""
        if start == 'target':
            start = self.targetalias
        yield start
        if start in self.joins:
            for entry in self.joins[start]:
                 self.joinsdfs(entry.joinalias)
        
    # not used
    def __contains__(self, value):
        return value in self.joins