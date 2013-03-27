#!/usr/bin/env python
# -*- coding: UTF-8 -*
""" 
Library for work with DBF files (without iterators for work with old Python versions)
"""
# Changelog:
# 0.2 - 2005-09-22 
#                  line 128 and late - for NUMERIC - count of the number of decimal places
# 0.3 - 2006.05.31 
#                Add type 0x30    Visual FoxPro
#                If field type not = \000 ignore this field (for DBF with empty headers)
VERSION=0.2

from struct import unpack,pack
import string

class dbf:
      """DBF header"""

      def __init__(self):
          self.dbfType       = 0  # Type of file
          self.lastChange    = "" # Last change date
          self.recordCount   = 0  # Field count
          self.recordsOffset = 0  # location start of data
          self.recordLength  = 0  # Record length
          self.haveCDX       = 0  # Have or not index file CDX
          self.fields        = []
          self.filename      = ''
          self.fh            = None
          self.recormask     = "" # mask fro split row into fields

      def cloneDBF(self,dest):
          """ Clone struct DBF with dest descriptors """
          hdr = pack("cccciHH16sc3s",chr(self.dbfType),
                                   chr(int(self.lastChange[:2])),
                                   chr(int(self.lastChange[2:4])),
                                   chr(int(self.lastChange[4:])),
                                   0,
                                   self.recordsOffset,
                                   self.recordLength,
                                   chr(0x00)*16,
                                   chr(self.haveCDX),
                                   chr(0x00)*3)
          dest.write(hdr)
          # Write fields
          for f in self.fields:
              name = f[0]+chr(0x00)
              try:
                record = pack("11sclBB14x",name,f[1],0,f[2],f[3])
              except:
                        print "error in",name,f[1],0,f[2],f[3]
                        raise
              if len(record)<32:
                 record = record+(chr(0x00)*(32-len(record)))
              dest.write(record)
          dest.write(chr(0x0D))
          #Не забыть добавить призрачную запись.
          dest.write(chr(0x20)*self.recordLength)

      def close(self):
          """ Close DBF """
          self.fh.close()

      def delete(self,recno):
          """ Delete record with recno number"""
          if recno > self.recordCount:
            raise IndexError
          self.fh.seek(self.recordsOffset+(recno*self.recordLength))
          print "Current pos:",self.fh.tell()
          self.fh.write(chr(0x2A)) # first field is delete flag 
          print "Write:",chr(0x2A)

      def open(self,filename):
          """ Open file """
          self.filename=filename
          self.fh = open(filename,"r+b")
          self.fh.seek(0)
          self.fromFile()
          # generate records mask for parsing
          mask = "1s" # delete field
          for f in self.fields:
              mask=mask+str(f[2])+"s"
          self.recormask = mask

      def appendRaw(self,raw):
          """ Add new 'raw' record """
          # Go to end
          self.fh.seek(self.recordsOffset+((self.recordCount)*self.recordLength))
          self.fh.write(raw)
          # add ghost record
#          self.fh.write(chr(0x20)*self.recordLength)
          # Renew header (row count)
          self.recordCount+=1
          self.fh.seek(4)
          self.fh.write(pack("i",self.recordCount))

      def append(self,data):
          """ Add record"""
          self.appendRaw(self.hache2raw(data))

      def raw2hache(self,raw,needFields=None,result={}):
          """ Parse 'raw' row in dict
          Convert  N type into int or float dec count depending
          Convert onli fields including into needFields
          """
          record = unpack(self.recormask,raw)
          result['_DELETE'] = record[0]

          for i in xrange(len(record)-1):
            fn = self.fields[i][0]
            if not needFields or fn in needFields:
              if self.fields[i][1]=='N':
                 if self.fields[i][3]==0:
                    res=0
                    try:
                       res=int(record[i+1].strip())
                    except:
                       pass # 
                 else:
                    res=0.00
                    try:
                       res=float(record[i+1].strip())
                    except:
                       pass # 
                 result[fn] = res
              else:
                 result[ fn] = record[i+1].strip()
          return result

      def hache2raw(self,data):         
          """ Convert dict into row """
          params = [self.recormask,chr(0x20)] # Mask and DELETE.
          for f in self.fields:
              if f[1]=='C': 
                        params.append(("%-"+str(f[2])+"s") % str(data.get(f[0],'')))
              elif f[1]=='N' and f[3]>0: 
                        try:
                             params.append(("%"+str(f[2])+"."+str(f[3])+"f") % float(data.get(f[0],'')))
                        except:
                             print "Error in",f
                             raise

              else: 
                        params.append(("%"+str(f[2])+"s") % str(data.get(f[0],''))) # выровнять по правому краю
          return apply(pack,params)

      def write(self,recno,data):
          """ Write data from # position """
          self.writeRaw(recno,self.hache2raw(data))

      def read(self,recno,needFields=None):
          """Read record recno"""
          return self.raw2hache(self.readRaw(recno),needFields)

      def readRaw(self,recno):
          """ Read one record in raw mode """
          if recno > self.recordCount:
            raise IndexError
          self.fh.seek(self.recordsOffset+(recno*self.recordLength))
          return self.fh.read(self.recordLength)

      def writeRaw(self,recno,rawdata):
          """ Change record writing radata in his place
          WARNING size of rawdata not checking """
          if recno > self.recordCount:
            raise IndexError
          self.fh.seek(self.recordsOffset+(recno*self.recordLength))
          self.fh.write(rawdata)

      def getNext(self,recno):
          """  Return next not deleted row
            Data returning in (num,row) form
            if not found row return None
          """
          while 1:
                recno = recno+1
                if recno>self.recordCount:
                   return None
                else: 
                 data =self.readRaw(recno)
                if len(data)<self.recordLength:
                   break
                if data[0]!=chr(0x2A):   
                   return recno,data
          return None

      def toFile(self,fh): #Пока не закончено.
          """ Write header to file. File must be open into
          write with binary mode. Write offset must be 0"""
          hdr = pack("cccciHH16sc3s",chr(self.dbfType),
                                   chr(int(self.lastChange[:2])),
                                   chr(int(self.lastChange[2:4])),
                                   chr(int(self.lastChange[4:])),
                                   self.recordCount,
                                   self.recordsOffset,
                                   self.recordLength,
                                   chr(0x00)*16,
                                   chr(self.haveCDX),
                                   chr(0x00)*3)
          fh.write(hdr)
          # Пишем поля
          for f in self.fields:
              name = f[0]+chr(0x00)
              record = pack("11sclbb14x",name,f[1],0,f[2],f[3])
              print "Record length:",len(record)
              if len(record)<32:
                 record = record+(chr(0x00)*(32-len(record)))
              fh.write(record)
          fh.write(chr(0x0D))
          #Add ghost record.
          fh.write(chr(0x20)*self.recordLength)
                                   

      def fromFile(self):
          """ read header from file """
          mask = "c3ciHH16xc3x"
          (self.dbfType, year,month,day,self.recordCount,self.recordsOffset,self.recordLength,self.haveCDX) = unpack(mask,self.fh.read(32))
          self.lastChange = "%02i%02i%02i" % (ord(year),ord(month),ord(day))
          self.haveCDX = ord(self.haveCDX)
          self.dbfType = ord(self.dbfType)
          # Read fields description
          self.fields = []
          for i in range((self.recordsOffset-33)/32):
              bytes = unpack('12c4xBb14x', self.fh.read(32)) 
              field = '' 
              for i in xrange(11): 
                  if bytes[i] == '\000': 
                      break 
                  field = field+bytes[i] 
              type = bytes[11] 
              if type.strip()!='\000':
                      length = bytes[12] 
                      dec = bytes[13] 
                      self.fields.append((field,type,length,dec)) 

      def printInfo(self):
          if self.dbfType==0x03:
             dbtype = "FoxBASE+/dBASE III +, без memo"
          elif self.dbfType==0x83:
             dbtype = "FoxBASE+/dBASE III + c мемо"
          elif self.dbfType==0x03:
             dbtype = "FoxPro/dBASE IV, без memo"
          elif self.dbfType==0xF5:
             dbtype = "FoxPro с memo"
          elif self.dbfType==0x8B:
             dbtype = "dBASE IV с memo"
          elif self.dbfType==0x30:
             dbtype = "Visual FoxPro"
          else:
             dbtype = "Format unknown "+hex(self.dbfType)
          print "Format:...................",dbtype
          #
          print "Last change time:.........",self.lastChange #
          #
          print "Record count:.............",self.recordCount
          
          print "First record offset:......",self.recordsOffset
          #
          print "One record length:........",self.recordLength
          print "1-exist (CDX type),0-not..",self.haveCDX
          print "Fields:"
          print "Name...... Typ Len...Dec"
          print "------------------------"
          for i in self.fields:
              print "%-10s %3s %4i %3i" % i

