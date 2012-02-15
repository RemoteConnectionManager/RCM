#!/bin/env python
import pickle
import datetime
import os

class crv_session:

  def __init__(self,fromfile='',file='',state='',node='',display='',jobid='',sessionid='',username='',walltime=''):
    if (fromfile != ''):
      self.hash=pickle.load(open(fromfile,"rb"))
    else:
      self.hash={'file':file, 'state':state, 'node':node, 'display':display, 'jobid':jobid, 'sessionid':sessionid, 'username':username, 'walltime':walltime}
      self.hash['created']=datetime.datetime.now().strftime("%Y%m%d-%H:%M:%S")
  def serialize(self,file):
    pickle.dump(self.hash, open( file, "wb" ) )

  def write(self,format):
    if ( format == 0):
      print pickle.dumps(self.hash)
    elif ( format == 1):
      for k in sorted(self.hash.keys()):
        print "%s:%s" % ( k , self.hash[k] )
    elif ( format == 2):
      x=[]
      for k in sorted(self.hash.keys()):
        x.append(self.hash[k])
      print ":".join(x) 



class crv_sessions:

  def __init__(self,fromfile='',sessions=[]):
    if (fromfile != ''):
      self.array=pickle.load(fromfile)
    else:
      self.array=sessions

  def serialize(self,file):
    pickle.dump(self.array, open( file, "wb" ) )

  def write(self,format):
    if ( format == 0):
      print pickle.dumps(self.array)
    elif ( format == 1):
      for k in self.array:
        print "---------------------"
        k.write(1)
    elif ( format == 2):
      c=crv_session()
      print ":".join(sorted(c.hash.keys())) 
      for k in self.array:
        k.write(2)

 
