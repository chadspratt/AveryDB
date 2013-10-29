AveryDB
======= 
Running
-------
To use, you need to have Python 2.7 (2.6 will probably work) and PyGTK installed.
Use the PyGTK all-in-one installer from http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/

A portable version (doesn't require python and pygtk to be installed) is planned.

Run the file averydb.py

About
-----
The utility focuses on allowing you to join tables of data stored in separate files and outputting a customized result.  
Fields can be easily renamed, reordered, created, removed, altered, and perform any calculations for the output value.  
Not least of all, it does everything in one go, so if you're working with large amounts of data you don't have to start
one modification, wait for it to end, and start the next. You configure the entire process, from original input files to
the final version of the output.
Since it's meant to work with multiple formats, you can ignore the joining functionality and just use it as a file 
conversion tool (which gives you convenient fine tuning control over the conversion).
![Alt text](/screenshots/main_window.png "Main Window")
Formats
-------
AveryDB is meant to work with _avery_ format of database, though it's a ways from that goal.  
Right now it lets you input, combine, and output csv, dbf, and sqlite. Excel is on a short list of features to add next.

Joining
-------
Currently only left joins are supported. Inner joins (where you only keep matching records) will be added soon.  
Cross joins and everything else will be supported in an expert mode, where all the interface tools for setting
up joins will be replaced by a box where you can just enter your own query. At least in the near term. To make
everything fast, all data is loaded in to an SQLite database. 

Field Calculations
------------------
Values from input files are referenced by !filealias.fieldname!
These values can be used in single line statements like:

    !values.LAND_HSTD! + !values.LAND_NON_H!
    
Or they can be passed to a custom function like:

    propertyfrompropid(!Parcels.propid!)
    
All functions are stored in python files in the fieldcalcs directory. Each file in that directory acts as a
library of functions that can be called within the program. To call my_calc() from mylib.py you would do:

    mylib.my_calc(!whateverfile.andfield!)
    
Clicking the "calc" button on the right end of the central toolbar, you can open the calculator window, which
will display all the available inputs and libraries/functions.  
![Alt text](/screenshots/calculator.png "Calculator")  
Double click a function to add it to the value, then double click an input field and it will be inserted in
the function call.  
Highlight text and double click a function to wrap the function call around the selected text.  
When you save a field value in the calculator window the results are immediately shown in the sample output
of the main window. If there is an error in your function, the field value will show as "!error!" and the error
message will be printed to the console window.
You can select libraries from the dropdown list, or type the name of any fieldcalcs or python builtin library,
to load a list of its functions.
You can click "Library" to open the fieldcalcs directory, where the the library files are stored, in your system's
file browser.

From the calculator window you can click the plus button next to the library entry to launch a built-in function
editor.  
![Alt text](/screenshots/function_editor.png "Function Editor")  
Pressing tab will insert tabs, but these are converted to spaces when saved. Existing code is displayed with spaces,
but you can mix tabs in when editing it since they'll all be converted.
If you use an external editor to edit a library file, click the Reload Function button in the function editor window to
load the changes. If there are syntax errors, it will not load and the error will be printed in the console window.

Keyboard Shortcuts
------------------
When the area for editing the fields has focus there are the following shortcuts:
* Delete - remove selected fields
* Alt + Up/Down - move selected fields
* Ctrl + n - add a field before the first selected, or at the end if no records are selected (the list of fields
must have focus)

Other Options
-------------
* *Restrict one-to-many joins* - By default, if a record joins to multiple records, it will create multiple output
records. If you want one record from your input file to create one record in the output, check the box under the
list of joins. This is particulary useful with shapefiles, where the dbf file must have the matching records at a
specific index.
* *Replace Target* - Check this to rename the target file to targetfilename.old and have the output written to its old spot.
* *Default output location* - Under File > Options you can set the default location to write output files. This will be
used when the output filename is just a name and no slashes denoting a path.

Cost
----
The program is free, but if it saves you an hour of time, you could give whatever one hour of your time is worth.
At worst, you break even. Consider all hours of time saved after that to be guilt free.  

If it saves you 50 hours of time, maybe a second hour's wage donation?

Credits
-------
This uses the dbfpy library for reading and writing dbf files.
http://dbfpy.sourceforge.net/

All other code, unless otherwise noted, by Chad [Avery] Spratt.
