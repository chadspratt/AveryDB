dbfutil
=======

For joining dbf files and editing the fields. dbf files are plain text database files commonly used for gis data

This uses two different dbf libraries developed by someone else. I tried them both out while writing this and never
chose one or the other and went back to recode accordingly.

http://dbfpy.sourceforge.net/
Used for writing the output dbf file. A lot more complex, which gives the impression that it's better.
I changed one line because of problems writing floats.

http://sourceforge.net/projects/demdbf/
Used for reading from dbf files. Claims to be "The world's fastest library to read and write DBF files written by Python"
