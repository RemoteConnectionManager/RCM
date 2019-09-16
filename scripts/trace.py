#!/bin/python
#strace -f -t -e trace=file -e abbrev=all vncviewer 2>&1 | cut  -d' ' -f 4- | grep 'open(' | cut -d'"' -f 2
#python -c "import collections; d = collections.OrderedDict(); while u=readline(): if 0 ==  d.get(u,0): print "-->"+u; d[u]=d.get(u,0)+1;; "


import os,sys,collections
d = collections.OrderedDict()
for line in iter(sys.stdin.readline, ''):
  u=line.strip()
#  if 0 ==  d.get(u,0):
#    print "-->"+u;
  d[u]=d.get(u,0)+1

listpath=[]

for u in d:
  if os.path.exists(u):
    ff=os.path.abspath(u)
    if os.path.isfile(ff):
      listpath.append(ff)
#      print (str(ff)+'<-->'+str(d[u]))

cluster= collections.OrderedDict()

for filename in listpath:
#  print (filename)
  ext=os.path.splitext(filename)[1]
  base=filename
  parent=os.path.dirname(base)
  while base != parent : 
    (tot,extcount)=cluster.get(parent,(0,collections.OrderedDict()))
    tot=tot+1
    extcount[ext]=extcount.get(ext,0)+1
    cluster[parent]=(tot,extcount)
   
    base=parent
    parent=os.path.dirname(base)

  
l=sorted(cluster, key=lambda x: cluster[x][0], reverse=True)
last= -1
for path in l:
  num_files=cluster[path][0] 
  if last != num_files:
    print (str(path)+'<-->'+str(cluster[path][0]))
  last=num_files
#for path in sorted(cluster.items()[0], key=lambda x:x[1]):
#import operator
#sorted(cluster.items(), key=operator.itemgetter(1)[0])
#for path in cluster:
#  print (str(path)+'<-->'+str(cluster[path][0]))
