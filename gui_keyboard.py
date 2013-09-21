#!/usr/bin/python
"""Keyboard shortcuts
"""
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
import gtk


class GUI_Keyboard(object):
    def fieldskeypressed(self, _widget, event):
        keyname = gtk.gdk.keyval_name(event.keyval)
        if keyname == 'Delete':
            self.removeoutput(None)
        elif keyname == 'n' and (event.state & gtk.gdk.CONTROL_MASK):
            self.addoutput(None)
        elif keyname == 'Up' and (event.state & gtk.gdk.MOD1_MASK):
            self.moveup(None)
        elif keyname == 'Up' and (event.state & gtk.gdk.MOD1_MASK & gtk.gdk.CONTROL_MASK):
            self.movetop(None)
        elif keyname == 'Down' and (event.state & gtk.gdk.MOD1_MASK):
            self.movedown(None)
        elif keyname == 'Down' and (event.state & gtk.gdk.MOD1_MASK & gtk.gdk.CONTROL_MASK):
            self.movebottom(None)
