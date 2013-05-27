# -*- coding: utf-8 -*-
# GUI window config

from Tkinter import *

class App(object):
    def __init__(self, master, main):        
        # GUI definition
        self.master = master
        frame = Frame(master)
        frame.pack()

        #self.dbflistlabel = Label(frame, text="dbf join files")
        #self.dbflistlabel.pack()
        self.filebuttonsframe = Frame(frame)
        self.filebuttonsframe.pack()
        self.button = Button(self.filebuttonsframe, text='Select target dbf', command=main.opentarget)
        self.button.pack(side=LEFT)
        self.add_dbf = Button(self.filebuttonsframe, text='add dbf', command=main.openjoin)
        self.add_dbf.pack(side=LEFT)
        self.remove_dbf = Button(self.filebuttonsframe, text='remove dbf', command=main.removejoin)
        self.remove_dbf.pack(side=LEFT)

        self.targetframe = Frame(frame)
        self.targetframe.pack()
        self.targetlabel = Label(self.targetframe, text='Primary target file: ')
        self.targetlabel.pack(side=LEFT)
        self.target = Label(self.targetframe, text='')
        self.target.pack(side=LEFT)

        self.dbfframe = Frame(frame)
        self.dbfframe.pack()
        
        self.dbftargetframe = Frame(self.dbfframe)
        self.dbftargetframe.pack(side=LEFT)
        
        self.dbftargetlabel = Label(self.dbftargetframe, text='target file')
        self.dbftargetlabel.grid(row=0, column=2)
        self.dbftargetyscroll = Scrollbar(self.dbftargetframe, orient=VERTICAL)
        self.dbftargetxscroll = Scrollbar(self.dbftargetframe, orient=HORIZONTAL)
        self.dbftargetlist = Listbox(self.dbftargetframe, width=50, yscrollcommand=self.dbftargetyscroll.set, xscrollcommand=self.dbftargetxscroll.set, exportselection=0)
        self.dbftargetyscroll.config(command=self.dbftargetlist.yview)
        self.dbftargetxscroll.config(command=self.dbftargetlist.xview)
        self.dbftargetyscroll.grid(row=1, column=5, sticky=N+S)
        self.dbftargetxscroll.grid(row=2, column=0, columnspan=5, sticky=E+W)
        self.dbftargetlist.grid(row=1, column=0, columnspan=5)
        
        self.dbfjoinframe = Frame(self.dbfframe)
        self.dbfjoinframe.pack(side=RIGHT)
        
        self.dbfjoinlabel = Label(self.dbfjoinframe, text='join file')
        self.dbfjoinlabel.grid(row=0, column=2)
        self.dbfjoinyscroll = Scrollbar(self.dbfjoinframe, orient=VERTICAL)
        self.dbfjoinxscroll = Scrollbar(self.dbfjoinframe, orient=HORIZONTAL)
        self.dbfjoinlist = Listbox(self.dbfjoinframe, width=50, yscrollcommand=self.dbfjoinyscroll.set, xscrollcommand=self.dbfjoinxscroll.set, exportselection=0)
        self.dbfjoinyscroll.config(command=self.dbfjoinlist.yview)
        self.dbfjoinxscroll.config(command=self.dbfjoinlist.xview)
        self.dbfjoinyscroll.grid(row=1, column=5, sticky=N+S)
        self.dbfjoinxscroll.grid(row=2, column=0, columnspan=5, sticky=E+W)
        self.dbfjoinlist.grid(row=1, column=0, columnspan=5)

        self.configjoin = Button(frame, text="config selected", command=main.loadjoinchoices)
        self.configjoin.pack()

        self.targetjoinframe = Frame(frame)
        self.targetjoinframe.pack()
        
        self.targetframe = Frame(self.targetjoinframe)
        self.targetframe.pack(side=LEFT)
        
        self.targetlabel = Label(self.targetframe, text="target field")
        self.targetlabel.grid(row=0, column=2)
        self.target_yscroll = Scrollbar(self.targetframe, orient=VERTICAL)
        self.target_xscroll = Scrollbar(self.targetframe, orient=HORIZONTAL)
        self.target_list = Listbox(self.targetframe, width=50, yscrollcommand=self.target_yscroll.set, exportselection=0)#, xscrollcommand=self.target_xscroll.set
        self.target_yscroll.config(command=self.target_list.yview)
        self.target_xscroll.config(command=self.target_list.xview)
        self.target_yscroll.grid(row=1, column=5, sticky=N+S)
        #self.target_xscroll.grid(row=2, column=0, columnspan=5, sticky=E+W)
        self.target_list.grid(row=1, column=0, columnspan=5)

        self.joinframe = Frame(self.targetjoinframe)
        self.joinframe.pack(side=RIGHT)
        
        self.joinlabel = Label(self.joinframe, text="join field")
        self.joinlabel.grid(row=0, column=2)
        self.join_yscroll = Scrollbar(self.joinframe, orient=VERTICAL)
        self.join_xscroll = Scrollbar(self.joinframe, orient=HORIZONTAL)
        self.join_list = Listbox(self.joinframe, width=50, yscrollcommand=self.join_yscroll.set, exportselection=0)#, xscrollcommand=self.join_xscroll.set
        self.join_yscroll.config(command=self.join_list.yview)
        self.join_xscroll.config(command=self.join_list.xview)
        self.join_yscroll.grid(row=1, column=5, sticky=N+S)
        #self.join_xscroll.grid(row=2, column=0, columnspan=5, sticky=E+W)
        self.join_list.grid(row=1, column=0, columnspan=5)

        self.savejoin = Button(frame, text="save field selection", command=main.savejoinchoice)
        self.savejoin.pack()

        self.outputframe = Frame(frame)
        self.outputframe.pack()
        self.outputlabel = Label(self.outputframe, text='output fields')
        self.outputlabel.pack()

        self.outputlistframe = Frame(self.outputframe)
        self.outputlistframe.pack(side=LEFT)
        self.outputbuttonsframe = Frame(self.outputframe)
        self.outputbuttonsframe.pack(side=RIGHT)

        self.output_yscroll = Scrollbar(self.outputlistframe, orient=VERTICAL)
        self.output_xscroll = Scrollbar(self.outputlistframe, orient=HORIZONTAL)
        self.output_list = Listbox(self.outputlistframe, width=50, selectmode=EXTENDED, yscrollcommand=self.output_yscroll.set, exportselection=0)#, xscrollcommand=self.output_xscroll.set
        self.output_yscroll.config(command=self.output_list.yview)
        self.output_xscroll.config(command=self.output_list.xview)
        self.output_yscroll.grid(row=1, column=5, sticky=N+S)
        #self.output_xscroll.grid(row=2, column=0, columnspan=5, sticky=E+W)
        self.output_list.grid(row=1, column=0, columnspan=5)

        self.initoutput = Button(self.outputbuttonsframe, text='init output', command=main.initoutput)
        self.initoutput.pack()
        self.removeoutput = Button(self.outputbuttonsframe, text='del field', command=main.removeoutput)
        self.removeoutput.pack()
        self.moveup = Button(self.outputbuttonsframe, text='move up', command=main.moveup)
        self.moveup.pack()
        self.movedown = Button(self.outputbuttonsframe, text='move down', command=main.movedown)
        self.movedown.pack()

        self.outputbuttonframe = Frame(frame)
        self.outputbuttonframe.pack()
        self.configoutput = Button(self.outputbuttonframe, text='config selected field', command=main.configoutput)
        self.configoutput.pack(side=LEFT)
        self.saveoutput = Button(self.outputbuttonframe, text='save field', command=main.saveoutput)
        self.saveoutput.pack(side=LEFT)
        self.addoutput = Button(self.outputbuttonframe, text='add field', command=main.addoutput)
        self.addoutput.pack(side=LEFT)

        self.outputfieldframe = Frame(frame)
        self.outputfieldframe.pack()

        self.outputnamevalueframe = Frame(self.outputfieldframe)
        self.outputnamevalueframe.pack(side=LEFT)
        self.outputnameframe = Frame(self.outputnamevalueframe)
        self.outputnameframe.pack()
        self.outputvalueframe = Frame(self.outputnamevalueframe)
        self.outputvalueframe.pack()

        self.outputnamelabel = Label(self.outputnameframe, text='field name:')
        self.outputnamelabel.pack(side=LEFT)
        self.outputname = Entry(self.outputnameframe)
        self.outputname.pack(side=RIGHT)
        self.outputvaluelabel = Label(self.outputvalueframe, text='value:')
        self.outputvaluelabel.pack(side=LEFT)
        self.outputvalue = Text(self.outputvalueframe, width=30, height=4)
        self.outputvalue.pack(side=RIGHT)

        self.fieldattframe = Frame(self.outputfieldframe)
        self.fieldattframe.pack(side=RIGHT)
        self.fieldtypeframe = Frame(self.fieldattframe)
        self.fieldtypeframe.pack()
        self.fieldlenframe = Frame(self.fieldattframe)
        self.fieldlenframe.pack()
        self.fielddecframe = Frame(self.fieldattframe)
        self.fielddecframe.pack()

        self.fieldtypelabel = Label(self.fieldtypeframe, text='Type:')
        self.fieldtypelabel.pack(side=LEFT)
        self.fieldtype = Entry(self.fieldtypeframe)
        self.fieldtype.pack(side=RIGHT)
        self.fieldlenlabel = Label(self.fieldlenframe, text='Len:')
        self.fieldlenlabel.pack(side=LEFT)
        self.fieldlen = Entry(self.fieldlenframe)
        self.fieldlen.pack(side=RIGHT)
        self.fielddeclabel = Label(self.fielddecframe, text='Dec:')
        self.fielddeclabel.pack(side=LEFT)
        self.fielddec = Entry(self.fielddecframe)
        self.fielddec.pack(side=RIGHT)

        self.outputfilenameframe = Frame(frame)
        self.outputfilenameframe.pack()
        self.outputfilenamelabel = Label(self.outputfilenameframe, text='output filename:')
        self.outputfilenamelabel.pack(side=LEFT)
        self.outputfilename = Entry(self.outputfilenameframe, text='output.dbf')
        self.outputfilename.pack(side=LEFT)
        self.outputfilename.insert(0,'output.dbf')
        self.dojoin = Button(frame, text='execute join', command=main.dojoin)
        self.dojoin.pack()

def initapp(main):
    root = Tk()
    app = App(root, main)
    root.title('DBF Utility')
    return app
    
def startapp(app):
    app.master.mainloop()
    