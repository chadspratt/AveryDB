"""Code to handle queuing and execution of background tasks."""
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
import table

class BackgroundTasks(object):
    def queuetask(self, task=None):
        """Add a task to the process queue but don't start processing."""
        if task:
            self.tasks_to_process.append(task)

    def processtasks(self, task=None):
        """Process all the queued "background" tasks, like converting files."""
        if task:
            self.tasks_to_process.append(task)
        if not self.taskinprogress:
            self.taskinprogress = True
            while self.tasks_to_process:
                tasktype, taskdata = self.tasks_to_process.pop(0)
                if tasktype == 'index':
                    self.buildindex(taskdata)
                    self.updatesample('refresh sample')
                elif tasktype == 'sample':
                    # a needed sql table might not be created yet
                    try:
                        self.updatesample(taskdata)
                    # if it fails, add it back to the end of the task list
                    except sqlite3.OperationalError:
                        self.tasks_to_process.append((tasktype, taskdata))
                elif tasktype == 'sqlite':
                    filealias, dataconverter = taskdata
                    self.converttosql(filealias, dataconverter)
                elif tasktype == 'lengthadjust':
                    self.adjustfieldlengths(taskdata)
            # This has to go after conversion is done.
            if self.executejoinqueued:
                self.gui['executejointoggle'].set_active(False)
                self.executejoin(None)
            self.taskinprogress = False

    def buildindex(self, join):
        """Build index in the background"""
        indexalias = join.joinalias
        indexfield = join.joinfield
        self.files[indexalias].buildindex(indexfield)

    def converttosql(self, filealias, dataconverter):
        """Convert a file to an SQLite table."""
        progresstext = 'Converting to sqlite: ' + filealias
        self.gui.setprogress(0, progresstext)
        # Run the generator until it's finished. It yields % progress.
        try:
            for progress in dataconverter:
                # this progress update lets the GUI function
                self.gui.setprogress(progress, progresstext, lockgui=False)
        except table.FileClosedError:
            print 'File removed, aborting conversion.'
        self.gui.setprogress(0, '')

    def adjustfieldlengths(self, lengthdetectgen):
        """Run the generator that finds and sets min field lengths."""
        progresstext = 'Adjusting field lengths'
        self.gui.setprogress(0, progresstext)
        # Run the generator until it's finished. It yields % progress.
        for progress in lengthdetectgen:
            # this progress update lets the GUI function
            self.gui.setprogress(progress, progresstext, lockgui=False)
        self.gui.setprogress(0, '')