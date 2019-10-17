#!/bin/python
# coding=utf8
# strace -f -t  -e abbrev=all -e 'trace=open' python /kubuntu/home/lcalori/spack/RCM/rcm/client/rcm_client_tk.py 2>&1
#strace -f -t -e trace=file -e abbrev=all vncviewer 2>&1 | cut  -d' ' -f 4- | grep 'open(' | cut -d'"' -f 2
#python -c "import collections; d = collections.OrderedDict(); while u=readline(): if 0 ==  d.get(u,0): print "-->"+u; d[u]=d.get(u,0)+1;; "


import os
import sys
import collections
import subprocess
import re
import shutil

class TraceHandler:
    def __init__(self):
        self.system_path={'bin':4, 'lib':4, 'etc':3, 'usr':2, 'home':1}
        self.trace_command='strace'
        #self.trace_options= ['-f', '-t',  '-e', 'abbrev=all', '-e', 'trace=open']
        self.trace_options= ['-f', '-t',  '-e', 'abbrev=all', '-e', 'trace=file']
        #self.trace_regex=r"^([^\s]*)\s*open\(\"([^\"]*)\",\s*(\w*)[\)\s\=]*([\-\d]*).*"
        #self.trace_regex=r"(.*)open\(\"([^\"]*).*"
        self.trace_regex = r"(.*)\(\"([^\"]*).*"
        #buit with https://regex101.com/r/DhfKGs/1
        # Note: for Python 2.7 compatibility, use ur"" to prefix the regex and u"" to prefix the test string and substitution.

        self.path_map=dict()

        self.path_collection=collections.OrderedDict()
        self.path_counts= collections.OrderedDict()

    def path_weight(self,path):
        path_list=os.path.normpath(path).split(os.path.sep)
        #print(path_list)
        weight=100
        if len(path_list) > 1 :
            first_path=path_list[1]
            if first_path:
                weight=100+10*self.system_path.get(path_list[1],0)
                #weight=weight-len(path_list)
            else:
                weight=1000
        else:
            weight=1000
        return weight

    def add_path_map_pair(self,source,dest):
        self.path_map[source]=dest

    def add_executable_prefix(self, folders_up=1, ):
        
    def add_path(self,path):
        print(path)
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
            #res=match.groups()[3]
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
                                      shell=False,
                                      universal_newlines=True)
        while True:
            nextline = self.process.stderr.readline()
            if nextline == '' and self.process.poll() is not None:
                break
            self.handle_line(nextline)
            sys.stdout.write("###--->#"+nextline)
            sys.stdout.flush()
        #for stdout_line in iter(self.process.stderr.readline, ""):

    def print_stats(self,skipequal=False):
        last= ('/',-1)
        for p in sorted(self.path_counts.keys(), key=lambda x: (self.path_weight(x), x, -self.path_counts[x][0])):
            if skipequal:
                curr = (p,self.path_counts[p][0])
                if curr[1] != last[1]:
                    print(" #->", p, self.path_counts[p][0])
                    last=curr
            else:
                print(" #->", p, self.path_counts[p][0])

    def copy_files(self,overwrite=False):
        for source in self.path_map:
            dest=self.path_map[source]
            os.makedirs(dest,exist_ok=True)
            print("Create dir: "+dest)

        for path in self.path_collection:
            if os.path.isfile(path):
                for source in self.path_map:
                    if path.find(source) == 0:
                        dest=self.path_map[source]
                        relpath=os.path.relpath(path, source)
                        target=os.path.join(dest,relpath)
                        target_dirname=os.path.dirname(target)
                        os.makedirs(target_dirname,exist_ok=True)
                        if not os.path.exists(target):
                            shutil.copy2(path,target)
                            print("copy "+path+" -->"+target)
                        else:
                            print("WARNING!!! overwrite path: "+target)
                            if overwrite:
                                shutil.copy2(path,target)




if __name__ == '__main__':
    print(sys.argv)
    if 1==len(sys.argv) :
        command_list = ['/bin/bash', '-c', "python -c 'import paramiko;'"]
    else:
        command_list = sys.argv[1:]
    trace_handler=TraceHandler()
    #for p in ['/', '/lib', '/pippo']:
    #    print(p+' ->'+str(trace_handler.path_weight(p)))
    trace_handler.trace(command_list)
    trace_handler.print_stats()
    jdk='/kubuntu/home/lcalori/spack/RCM_new/deploy/rcm_client/install/linux-linuxmint18-x86_64/gcc-5.4.0/jdk-8u141-b15-himqhkvhiep2osavn6jwvhjymeohpx7i'
    turbovnc='/kubuntu/home/lcalori/spack/RCM_new/deploy/rcm_client/install/linux-linuxmint18-x86_64/gcc-5.4.0/turbovnc-2.1.2-s2ki236ctdsblzyamfoformx3uekvcnc'
    #s1='/kubuntu/home/lcalori/spack/RCM_new/deploy/rcm_client/install/linux-linuxmint18-x86_64/gcc-5.4.0/openssl-1.0.2j-seqdsron63uj2433eezgj6fgoqu3z7un'
    asn1crypto='/kubuntu/home/lcalori/spack/RCM_new_client/py3env/lib/python3.5/site-packages/asn1crypto'
    paramiko='/kubuntu/home/lcalori/spack/RCM_new_client/py3env/lib/python3.5/site-packages/paramiko'
    d1='/tmp/prova'
    #trace_handler.add_path_map_pair(paramiko,d1)
    #trace_handler.add_path_map_pair(asn1crypto,d1)
    trace_handler.add_path_map_pair(jdk,d1)
    trace_handler.add_path_map_pair(turbovnc,d1)
    trace_handler.copy_files()
