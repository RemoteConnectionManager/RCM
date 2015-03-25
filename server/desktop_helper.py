#!/bin/env python
# -*- coding: utf-8 -*-
import os
import stat
import re
import string
import optparse
import shutil

class mytemplate(string.Template):
    def __init__(self,s=''):
        string.Template.__init__(self,s)
        rr="""
         \@(?:
          (?P<escaped>\@) |   # Escape sequence of two delimiters
          (?P<named>[_a-z][_a-z0-9]*)      |   # delimiter and a Python identifier
          \{(?P<braced>[_\.\-a-z][_\.\-a-z0-9]*)\}   |   # delimiter and a braced identifier
          (?P<invalid>\@)              # Other ill-formed delimiter exprs
         )
        """
        self.pattern=re.compile(rr, re.VERBOSE | re.IGNORECASE)
        self.delimiter='@'

    def templ_match(self,s=''):
        m=self.pattern.search(s)
        return m

class desktop_helper():
    def __init__(self):

        self.desk_subst={
            'icon':'',
            'exec':'',
        }

        desktop_template_xdg='''
     #!/usr/bin/env xdg-open
     [Desktop Entry]
     Version=1.0
     Encoding=UTF-8
     Exec=@{exec}
     @{icon}
     Name=@{name}
     StartupNotify=false
     Terminal=@{terminal}
     TerminalOptions=
     Type=Application
'''   

        self.t=mytemplate(desktop_template_xdg)

        self.op=optparse.OptionParser( usage="usage: %prog [options] full_module_name" )
        self.op.add_option("--icon_file",action="store",type="string", dest="icon_file",default='',help='set icon file')
        self.op.add_option("--desktop_file",action="store",type="string", dest="desktop_file",default='',help='define desktop file, defaults to module_name in desktop_folder')
        self.op.add_option("--shell_file",action="store",type="string", dest="shell_file",default='',help='define shell to use, if unspecified, create a module_name.sh in desktop folder')
        self.op.add_option("--shell_args",action="store",type="string", dest="shell_args",default='',help='define shell args in desktop file ')
        self.op.add_option("--desktop_folder",action="store",type="string", dest="desktop_folder",default='',help='define  desktop folder where the it creates the desktop folder')
        self.op.add_option("--desktop_name",action="store",type="string", dest="desktop_name",default='',help='define  desktop name of the icon')
        self.op.add_option("--command_string",action="store",type="string", dest="command_string",default='',help='define  command string to use, defaults to module name')
        self.op.add_option("--env_string",action="store",type="string", dest="env_string",default='',help='define  setup env string to use in shell, defaults to void')
        self.op.add_option("--copy_icon",action="store_true", dest="copy_icon",default=False,help='flag to copy the icon file into desktop_folder')
        self.op.add_option("--vglrun",action="store_true", dest="vglrun",default=False,help='flag to set vglrun usage')
        #self.op.add_option("--clean_links",action="store_true", dest="clean_links",default=False,help='clean dangling links fron removed modules')
        self.op.add_option("--add_link",action="store_true", dest="add_link",default=False,help='add link in common tools')
        self.op.add_option("--terminal",action="store_true", dest="terminal",default=False,help='open desktop terminal')
       

    def parse(self,argv=None):
        if not argv:
            (options,args) = self.op.parse_args(argv)
        else:
            (options,args) = self.op.parse_args()

        if len(args) > 0:  
            module_name= args[0]
            module_folder=''
            mc=module_name.split('/')

            if options.desktop_name : desktop_name=options.desktop_name
            else: desktop_name='_'.join(mc)

            self.desk_subst['name']=desktop_name

            home_var=mc[0].upper()+'_HOME'
            home_folder=os.getenv(home_var)
            if home_folder:
                if os.path.isdir(home_folder) :
                    module_folder=home_folder
                else:
                    print "WARNING NON existing home var folder: env("+home_var+") : "+module_folder
            else:
                print "WARNING NON existing home var "+home_var
            if options.desktop_folder :
                if os.path.isdir(options.desktop_folder) :
                    module_folder=options.desktop_folder
                else:
                    print "WARNING NON existing desktop folder: "+options.desktop_folder
            if not module_folder :
                print "unspecified module folder: exiting"
                exit()
            self.desktop=os.path.join(os.path.abspath(module_folder),'desktop')

            try: 
                os.makedirs(self.desktop)
            except OSError:
                if not os.path.isdir(self.desktop):
                    raise
            print "file desktop will be created in "+self.desktop


            if options.icon_file :
                if os.path.exists(options.icon_file) :
                    bname=os.path.basename(options.icon_file)
                    if options.copy_icon:
                        icon_file=os.path.join(self.desktop,bname)
                        shutil.copyfile(options.icon_file,icon_file)
                    else:
                        icon_file=options.icon_file
                    self.desk_subst['icon']="Icon="+icon_file
                else:
                    print "WARNING: icon file "+ options.icon_file +" not exists"

            if options.terminal :
                self.desk_subst['terminal']="true"
            else:
                self.desk_subst['terminal']="false"


            shell_file_content='#!/bin/bash\n'
#######  handling of command_string        
            if options.command_string :
                command_string=options.command_string
            else:
                print "setting command to run to module name: "+mc[0]
                command_string=mc[0]

#######  handling of vglrun
            if options.vglrun :
                shell_file_content+='shopt -s expand_aliases\n'
                command_string='vglrun '+command_string

            shell_file_content+='module load autoload virtualgl '+ module_name +'\n'
            shell_file_content+=options.env_string+'\n'
            shell_file_content+= command_string + ' $@'

            print "#### shell file content;\n"+  shell_file_content

#######  setup of shell file
            if options.shell_file :
                if os.path.exists(options.shell_file) :
                    shell_file=options.shell_file
                else:
                    print "ERROR: specified shell file "+options.shell_file+ " does not exists, exit"
                    exit()
            else:
                shell_file=os.path.join(self.desktop,desktop_name+'.sh')
		with open (shell_file, "w") as myfile:
                    myfile.write(shell_file_content)

            self.desk_subst['exec']="'/bin/bash' '"+shell_file+"'"
            if options.shell_args : self.desk_subst['exec']+=" '"+options.shell_args+ "'"

            desktop_file_content=self.t.safe_substitute(self.desk_subst)
            print "#### desktop file content;\n"+  desktop_file_content
            if options.desktop_file : desktop_file= options.desktop_file
            else: desktop_file=os.path.join(self.desktop,desktop_name+'.desktop')
  	    with open (desktop_file, "w") as myfile:
                 myfile.write(desktop_file_content)
            st=os.stat(desktop_file)
            os.chmod(desktop_file,st.st_mode |stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            common_tools_dir=os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))),'config','Desktop_setup','common_tools')
            if options.add_link:
                if os.path.isdir(common_tools_dir):
                    dest= os.path.join(common_tools_dir,os.path.basename(desktop_file))
                    if not os.path.exists(dest):
                        os.symlink(desktop_file,dest)
                    else:
                        print "WARNING,  already present desktop file link: "+dest
            
        else:
            print "module name required"
            exit()

if __name__ == '__main__':
    print "base folder: " + os.path.abspath(os.path.dirname(__file__))
    dh= desktop_helper()
    dh.parse()     