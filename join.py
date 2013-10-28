"""Contains a simple class for storing join configurations."""
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


class Join(object):
    """A struct for storing a join definition."""
    def __init__(self, joinalias, jointable, joinfield,
                 targetalias, targettable, targetfield,
                 inner=False):
        self.joinalias = joinalias
        self.jointable = jointable
        self.joinfield = joinfield
        self.targetalias = targetalias
        self.targettable = targettable
        self.targetfield = targetfield
        self.inner = inner
