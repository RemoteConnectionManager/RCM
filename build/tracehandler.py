#!/bin/python
# coding=utf8
# strace -f -t  -e abbrev=all -e 'trace=open' python /kubuntu/home/lcalori/spack/RCM/rcm/client/rcm_client_tk.py 2>&1
#strace -f -t -e trace=file -e abbrev=all vncviewer 2>&1 | cut  -d' ' -f 4- | grep 'open(' | cut -d'"' -f 2
#python -c "import collections; d = collections.OrderedDict(); while u=readline(): if 0 ==  d.get(u,0): print "-->"+u; d[u]=d.get(u,0)+1;; "


import os,sys,collections,subprocess,re



class TraceHandler:
    def __init__(self):
        self.system_path={'bin':4, 'lib':4, 'etc':3, 'usr':2, 'home':1}
        self.trace_command='strace'
        self.trace_options= ['-f', '-t',  '-e', 'abbrev=all', '-e', 'trace=open']
        self.trace_regex=r"^([^\s]*)\s*open\(\"([^\"]*)\",\s*(\w*)[\)\s\=]*([\-\d]*).*"
        #buit with https://regex101.com/r/DhfKGs/1
        # Note: for Python 2.7 compatibility, use ur"" to prefix the regex and u"" to prefix the test string and substitution.


        self.path_collection=collections.OrderedDict()
        self.path_counts= collections.OrderedDict()

    def path_weight(self,path):
        os.path.normpath(path).split(os.path.sep)
    def add_path(self,path):
        apath=os.path.abspath(path)
        if os.path.exists(apath):
            self.path_collection[apath]=self.path_collection.get(apath,0)+1
            if os.path.isfile(apath):
                ext=os.path.splitext(apath)[1]
                base=apath
                parent=os.path.dirname(base)
                while base != parent :
                    (tot,extcount)=self.path_counts.get(parent,(0,collections.OrderedDict()))
                    tot=tot+1
                    extcount[ext]=extcount.get(ext,0)+1
                    self.path_counts[parent]=(tot,extcount)
                    base=parent
                    parent=os.path.dirname(base)

    def handle_line(self,line):

        match = re.match(self.trace_regex, line)
        if not match :
            print("Unmatched-->"+line+"<--")
        matches = re.finditer(self.trace_regex, line)
        for matchNum, match in enumerate(matches):
            matchNum = matchNum + 1
            #print ("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = matchNum, start = match.start(), end = match.end(), match = match.group()))
            path=match.groups()[1]
            res=match.groups()[3]
            self.add_path(path)
            for groupNum in range(0, len(match.groups())):
                groupNum = groupNum + 1

                #print ("Group {groupNum} found at {start}-{end}: {group}".format(groupNum = groupNum, start = match.start(groupNum), end = match.end(groupNum), group = match.group(groupNum)))




    def trace(self,command):
        self.full_command_list= [self.trace_command]
        self.full_command_list.extend(self.trace_options)
        self.full_command_list.extend(command)
        self.process=subprocess.Popen(self.full_command_list,
                                      bufsize=1,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      stdin=subprocess.PIPE,
                                      shell=False)
        while True:
            nextline = self.process.stderr.readline()
            if nextline == '' and self.process.poll() is not None:
                break
            self.handle_line(nextline)
            #sys.stdout.write("###--->#"+nextline)
            #sys.stdout.flush()
        #for stdout_line in iter(self.process.stderr.readline, ""):

    def print_stats(self):
        for p in sorted(self.path_counts, key=lambda x: self.path_counts[x][0], reverse=True):

            print(p, self.path_counts[p][0])
        for p in sorted(self.path_counts.keys(), key=lambda x: (len(os.path.normpath(x).split(os.path.sep)),-self.path_counts[x][0])):

            print("##->", p, self.path_counts[p][0])

def old_stuff():
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


if __name__ == '__main__':
    command_list = ['python', '-c', '"import paramiko;"']
    trace_handler=TraceHandler()
    trace_handler.trace(command_list)
    trace_handler.print_stats()