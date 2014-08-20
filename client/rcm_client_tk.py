#!/bin/env python

import os
import tempfile
import rcm_utils
import rcm_client
import rcm

#from Tkinter import *
from Tkinter import *
from ttk import *

import tkFileDialog
import tkMessageBox
import tkSimpleDialog
import time
import ConfigParser
import datetime
import tkFont
import hashlib
import urllib2
import tempfile
import pickle
import collections
#luigi_disable_thread#import threading


font = ("Helvetica",10, "grey")
boldfont = ("Helvetica",10,"bold")
checkCredential = False
##bad_globals##queueList = []
lastClientVersion = []


def safe(debug=False):
    def safedec(f):
        def fsafe(*l_args, **d_args):
            try:
                return f(*l_args, **d_args)
            except Exception as e:
                if(hasattr(l_args[0],'do_list_refresh')):
                	l_args[0].do_list_refresh=False
                if("stopBusy" in dir(l_args[0])):
                	l_args[0].stopBusy()
#                try:
#                    l_args[0].stopBusy()
#                except:
#                    pass
                if True:
                    import traceback
                    tkMessageBox.showwarning("Error","in {0}: {1}\n{2}".format(f.__name__, e,traceback.format_exc()))
                    traceback.print_exc()
                else:
                    tkMessageBox.showwarning("Error", e)
                
        return fsafe
    return safedec

safe_debug_on = safe(True)
safe_debug_off = safe(False)

@safe_debug_off
def compute_checksum(filename):
    fh = open(filename, 'rb')
    m = hashlib.md5()
    while True:
        data = fh.read(8192)
        if not data:
            break
        m.update(data)
    return m.hexdigest()
   
@safe_debug_off     
def download_file(url,outfile):
    u = urllib2.urlopen(url)
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    f = open(outfile, 'wb')
    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        p = float(file_size_dl) / file_size

    f.close()

@safe_debug_off
def update_exe_file():
    exe_dir=os.path.dirname(sys.executable)
    tmpDir = tempfile.gettempdir()
    newfile=os.path.join(tmpDir,os.path.basename(sys.executable))
    download_file(lastClientVersion[1],newfile)
    newfile_checksum = compute_checksum(newfile)
    time.sleep(5)

    if(lastClientVersion[0] != newfile_checksum):
        tkMessageBox.showwarning("Client Update", "Downloaded file Checksum mismatch \n Expected: "+lastClientVersion[0] +"\nFound  : "+ newfile_checksum \
        + "\nUpdate stopped.")        
        os.remove(newfile)
    else:
        global batchfilename
        if(sys.platform=='win32'):
            batchfilename=os.path.join(tmpDir,"RCM_update.bat")
            batchfile=open(batchfilename, 'wb')
            batchfile.write("rem start update bat"+"\n")
            batchfile.write("cd /D "+exe_dir+"\n")
            batchfile.write("copy mybatch.bat mybatch.txt\n")
            batchfile.write('ping -n 3 localhost >nul 2>&1'+"\n")
            batchfile.write("del mybatch.txt\n")
            batchfile.write("ren "+os.path.basename(sys.executable)+" _"+os.path.basename(sys.executable)+"\n")
            batchfile.write("copy "+newfile+"\n")
            batchfile.write("del "+" _"+os.path.basename(sys.executable)+"\n")
            batchfile.write("del "+newfile+"\n")
            batchfile.write("start "+os.path.basename(sys.executable)+"\n")
            batchfile.write("del "+batchfilename+"\n")
            batchfile.write("exit\n")
            batchfile.close()
            tkMessageBox.showinfo("Client Update", "The application will be closed and the new one will start in a while!")
            os.startfile(batchfilename)
        else:
            batchfilename=os.path.join(tmpDir,"RCM_update.sh")
            batchfile=open(batchfilename, 'wb')
            batchfile.write("#!/bin/bash\n")
            batchfile.write("#start update bat"+"\n")
            batchfile.write("cd "+exe_dir+"\n")
            batchfile.write("sleep 3 \n")
            batchfile.write("rm "+os.path.basename(sys.executable)+"\n")
            batchfile.write("cp "+newfile+" .\n")
            batchfile.write("chmod a+x "+os.path.basename(sys.executable)+"\n")
            batchfile.write("./"+os.path.basename(sys.executable)+"\n")
            batchfile.close()
            tkMessageBox.showinfo("Client Update", "The application will be closed and the new one will start in a while!")
            os.system("sh "+batchfilename+ " &") 
                    
class Login(Frame):
    def __init__(self, master=None, guiaction=None, action=None):
        
        #Read configuration file
        self.master = master
        self.configFileName = os.path.join(os.path.expanduser('~'),'.rcm','RCM.cfg')
        self.hostCollections = collections.deque(maxlen=5)
        self.config = ConfigParser.RawConfigParser()
        if(os.path.exists(self.configFileName)):
            try:
                self.config.read(self.configFileName)    
                hostList = self.config.get('LoginFields', 'hostList')
                self.hostCollections=pickle.loads(hostList)

            except:
                os.remove(self.configFileName)

        self.guiaction=guiaction
        self.action=action

        loginFrame = Frame(self.master, padding=10)

        loginLabel = Label(self.master, text='NEW LOGIN:', padding=5, font=boldfont)
        loginLabel.pack(side=TOP)

        self.host = StringVar()  
        self.user = StringVar()
        self.password = StringVar()


        if (len(list(self.hostCollections)) > 0 ):
            Label(loginFrame, text="""Sessions:""").grid(row=0)
            self.variable = StringVar(loginFrame)
            self.variable.set(list(self.hostCollections)[0]) # default value
            self.fillCredentials(self.variable)
            OptionMenu(loginFrame, self.variable, *list(self.hostCollections), command=self.fillCredentials).grid(row=0, column=1, sticky=W)        

        Label(loginFrame, text="Host: ", padding=5).grid(row=1)
        Label(loginFrame, text="User: ", padding=5).grid(row=2)
        Label(loginFrame, text="Password:", padding=5).grid(row=3)

        hostEntry = Entry(loginFrame, textvariable=self.host, width=16)
        userEntry = Entry(loginFrame, textvariable=self.user, width=16)
        passwordEntry = Entry(loginFrame, textvariable=self.password, show="*", width=16)

        hostEntry.grid(row=1, column=1)
        userEntry.grid(row=2, column=1)
        passwordEntry.grid(row=3, column=1) 
        loginFrame.pack()

        b = Button(self.master, text="LOGIN", style='RCM.TButton',padding=5, command=self.login)
        b.pack(side=BOTTOM, pady=15)
        passwordEntry.bind('<Return>', self.enter)
        hostEntry.focus_set()

    def fillCredentials(self,v):
        host = self.variable.get()
        self.host.set(host.split('@')[1])
        self.user.set(host.split('@')[0])
        
        
    def enter(self,event):
        self.login()
    
    @safe_debug_off
    def login(self):     
        if  (self.host.get() and self.user.get() and self.password.get()):           
           
            #Start login only if all the entry are filled
            global checkCredential 
            

            checkCredential = self.action(self.host.get(), self.user.get(), self.password.get())
            if checkCredential:
                #Write configuration file
                if not self.config.has_section('LoginFields'):
                    self.config.add_section('LoginFields')
                    displayDimensionsCollection = collections.deque(maxlen=5)
                    self.config.set('LoginFields', 'displayDimensionsList',pickle.dumps(displayDimensionsCollection))
                    
                newSession = self.user.get()  + '@' + self.host.get()    
                if (newSession in list(self.hostCollections)):
                    self.hostCollections.remove(newSession)
                self.hostCollections.appendleft(newSession)
                    
                self.config.set('LoginFields', 'hostList',pickle.dumps(self.hostCollections))
                d = os.path.dirname(self.configFileName)
                if not os.path.exists(d):
                    os.makedirs(d)
            
                with open(self.configFileName, 'wb') as configfile:
                    self.config.write(configfile)

                self.guiaction()
                return
            else:
                tkMessageBox.showwarning("Error","Authentication failed!")
                return


class ConnectionWindow(Frame):
       
    @safe_debug_off
    def deathHandler(self, event):
        if(self.debug): print self, " main app win has been closed . killing vnc connections"
        self.client_connection.vncsession_kill()
        
    def __init__(self, master=None,rcm_client_connection=None):
        self.debug=True
        self.sessions=None
        self.do_list_refresh=False
        self.do_update_gui=True
        Frame.__init__(self, master)
        self.client_connection=rcm_client_connection
        self.connection_buttons=dict()
        self.pack( padx=10, pady=10 )
        #self.bind("<<list_refresh>>",self.list_refresh)
        self.pending_connections = []

        
        self.f1=None
        self.f1 = Frame(self, padding=10)
        self.f1.pack(expand=1, fill=Y)
        w = Label(self.f1, text='Please wait...', padding=2)
        w.pack(expand=1, fill=Y)

        self.f2 = Frame(self, padding=10)
        button = Button(self.f2, text="NEW DISPLAY", padding=5,  style='RCM.TButton', command=self.submit)
        button.pack(expand=1)
        button.grid( row=0,column=1 )

        self.file_opt = options = {}
        options['filetypes'] = [('vnc files', '.vnc'), ('all files', '.*')]

        self.last_used_dir='.'

        button = Button(self.f2, text="REFRESH", padding=5,  style='RCM.TButton', command=self.list_refresh)
        button.grid( row=0,column=2 )
        self.f2.pack()
        
        self.bind("<Destroy>", self.deathHandler)
        #check version after mainloop is started
        self.after(500,self.check_version)
        self.after(200,self.auto_list_refresh)
        self.do_list_refresh = True


    @safe_debug_off   
    def check_version(self):
        self.startBusy("Getting config info")
        self.platform_config=self.client_connection.get_config()
        self.startBusy("Checking new client version...")
        if('frozen' in dir(sys)):
            currentChecksum = compute_checksum(sys.executable)
            global lastClientVersion
            lastClientVersion = self.platform_config.get_version()
            
            if(currentChecksum != lastClientVersion[0]):
                self.stopBusy()
                verDialog = newVersionDialog(self)
                if (verDialog.result == True):
                    self.startBusy("Downloading new version client...")
                    update_exe_file()
                    self.stopBusy()
                    self.master.destroy()
                    return
        self.stopBusy()
        self.update_idletasks()
        #self.event_generate("<<list_refresh>>")
        self.do_list_refresh = True

       
    @safe_debug_off
    def update_sessions(self,ss):
        self.connection_buttons=dict()
        self.sessions=ss
        if(self.f1):
            for child in self.f1.winfo_children():
                child.destroy()

        if len(self.sessions.array) == 0:
            w = Label(self.f1, text='No display available. Press \'NEW DISPLAY\' to create a new one.', padding=2)
            w.pack()
        else:
            f1 = self.f1
            labelList = ['state', 'session name', 'created', 'node', 'display', 'username', 'timeleft']
            c=rcm.rcm_session()
            i = 0
            for t in labelList:
                if t in c.hash.keys():
                    w = Label(f1, text=t.upper(), relief=RIDGE, state=ACTIVE, anchor=CENTER, padding=4, font=boldfont)
                    w.grid( row=0,column=i+3, sticky="we")

                    f1.columnconfigure ( i, minsize=80 )
                    i = i + 1
            
            for line, el in  enumerate( self.sessions.array ):
                if(self.client_connection):
                
                    def cmd(self=self, session=el):
                        if(self.debug): print "killing session", sessionid
                        self.kill(session)
                        
                    #if(el.hash['state'] == 'killed'):
                    #    continue

                    bk = Button( f1, text="KILL", padding=4,style='RCM.TButton', command=cmd)
                    bk.grid( row=line+1, column=2, pady=0)

                    def cmd_share(self=self, session=el):
                        self.asksaveasfilename(session)

                    bs = Button( f1, text="SHARE", padding=4,style='RCM.TButton', command=cmd_share)
                    bs.grid( row=line+1, column=1, pady=0)

                    bc = Button( f1, text="CONNECT", padding=4,style='RCM.TButton')
                    bc.grid( row=line+1, column=0, pady=0 )
                    sessionid = el.hash['sessionid']


                    def disable_cmd(self=self, sessionid=el.hash['sessionid'],active=True):
                        print "sessionid-->"+sessionid+"<--"

                        if(active):
                            self.client_connection.activeConnectionsList.append(sessionid)
                        else:
                            self.client_connection.activeConnectionsList.remove(sessionid)
                            self.do_list_refresh=True
                        self.do_update_gui=True

                    #if el.hash['state'] == 'valid':
                    self.connection_buttons[sessionid]=(bc,disable_cmd)
                    #    print "self.connection_buttons -------> " + str(self.connection_buttons)

                    
                    def cmd_warn(self=self, session=el,disable_cmd=disable_cmd):
                            tkMessageBox.showwarning("Warning!", "Display created with a previous RCM client version. Can not start the connection.")
                    def cmd(self=self, session=el,disable_cmd=disable_cmd):
                        if(session.hash['sessionid'] in self.client_connection.activeConnectionsList):
                            tkMessageBox.showwarning("Warning!", "Already connected to session " +session.hash['sessionid'])
                        else:
                            if(self.debug): print "connecting to session", session.hash['sessionid']
                            self.startBusy("Connecting to the remote display...")
                            self.client_connection.vncsession(session,gui_cmd=disable_cmd)
                            self.after(4000,self.stopBusy)

                    if (el.hash.get('vncpassword','') == ''):
                        bc.configure( command=cmd_warn )
                    else:
                        bc.configure( command=cmd )
                    if sessionid in self.client_connection.activeConnectionsList:
                        bc.configure(state=DISABLED)
                    if (el.hash['state'] == 'pending'):
                        bc.configure(state=DISABLED)
                        bs.configure(state=DISABLED)

                i = 0
                for t in labelList:
                    if t in c.hash.keys():
                        lab = Label(f1, text=el.hash[t], relief=RIDGE, anchor=CENTER, padding=6)
                        if t == 'timeleft':
                            try:
                                timeleft = datetime.datetime.strptime(el.hash[t],"%H:%M:%S")
                                endTime = timeleft.replace(hour=0,minute=0,second=0)
                                limit = timeleft - endTime
                                if limit < datetime.timedelta(hours=1):
                                    lab.configure(foreground="red")
                            except:
                                pass
                        lab.grid( row=line+1, column=i+3,sticky="we" )
                        i = i + 1
            
    @safe_debug_off
    def kill(self, session):  
        self.startBusy("Killing the remote display...")
        self.client_connection.kill(session)
        self.stopBusy()
        if(not session.hash['sessionid'] in self.client_connection.activeConnectionsList): 
            #self.event_generate("<<list_refresh>>")
            self.do_list_refresh = True

        #self.delayed_refresh_dimensions()
        self.do_list_refresh = True


    @safe_debug_off
    def asksaveasfilename(self, session=None):
        file_suggested=session.hash['session name'].replace(' ','_')+'.vnc'
        filename = tkFileDialog.asksaveasfilename(initialfile=file_suggested, initialdir=self.last_used_dir,**self.file_opt)

        if filename:
            out_file = open(filename, 'w')
            out_file.write("[Connection]\n")
            if (session.hash['tunnel'] == 'y'):
                #rcm_tunnel is a key word to know that I need to tunnel across that node
                out_file.write("rcm_tunnel={0}\n".format(session.hash['nodelogin']))
                out_file.write("host={0}\n".format(session.hash['node']))
            else:
                out_file.write("host={0}\n".format(session.hash['nodelogin']))
            out_file.write("port={0}\n".format(5900 + int(session.hash['display'])))
            out_file.write("password={0}\n".format(session.hash['vncpassword']))
            out_file.close()
            self.last_used_dir=os.path.dirname(filename)

    @safe_debug_off
    def submit(self):
        self.startBusy("Waiting for queue list...")
##bad_globals##        global queueList
        queues=self.client_connection.queues()
        queueList = queues.keys()
        vncs=self.client_connection.vncs()
        vncList = vncs.keys()

        self.stopBusy()
        if(self.debug): print "Queue list: ", queueList
        if queueList == ['']:
            tkMessageBox.showwarning("Warning", "Queue not found...")
            return
        
        dd = newDisplayDialog(self,queues,vncs)

        if dd.displayDimensions == NONE:
            self.stopBusy()
            return
        
        self.displayDimension = dd.displayDimensions
        self.queue = dd.queue.get()
        self.vnc_id=dd.vnc.get()
        self.sessionname = dd.sessionName

        #luigi_disable_thread#t = threading.Thread(target=self.create_display)
        #luigi_disable_thread#t.start()
        target=self.create_display()

        self.startBusy("Creating a new remote display...")
        self.after(8000, self.set_do_list_refresh)

    def set_do_list_refresh(self):
        self.do_list_refresh = True


    @safe_debug_off
    def create_display(self):
        newconn=self.client_connection.newconn(self.queue, self.displayDimension, self.sessionname, vnc_id=self.vnc_id)

        #luigi_disable_thread#lock = threading.Lock()
        #luigi_disable_thread#lock.acquire()
        #luigi_disable_thread#try:
        self.pending_connections.append(newconn)
        #luigi_disable_thread#finally:
        #luigi_disable_thread#    lock.release()

        
    @safe_debug_off
    def auto_list_refresh(self):
        if(self.do_list_refresh):
            self.list_refresh()
        if(self.do_update_gui):
            if(self.sessions):
                for line, el in  enumerate( self.sessions.array ):
                    sessionid=el.hash['sessionid']
                    (button,cmd)=self.connection_buttons.get(sessionid,(None,None))
                    if(button):
                        if(sessionid in self.client_connection.activeConnectionsList):
                            button.configure(state=DISABLED)
                        else:
                            button.configure(state=ACTIVE)
            self.do_update_gui=False

        if (len(self.pending_connections) != 0):
            conn = self.pending_connections.pop()
            self.list_refresh()
            (button,cmd)=self.connection_buttons.get(conn.hash['sessionid'], (None,None))
            if(cmd): self.client_connection.vncsession(conn, conn.hash['otp'], cmd)

        self.after(100,self.auto_list_refresh)

    @safe_debug_off
    def list_refresh(self,event=None):       
        self.startBusy("Refreshing display list...")
        refreshList = self.client_connection.list()
        self.update_sessions(refreshList)
        self.stopBusy()
        #self.delayed_refresh_dimensions()
        self.refresh_dimensions()
        self.do_list_refresh = False


    def refresh_dimensions(self):
        #print "current toplevel geom",self.master.winfo_toplevel().winfo_geometry()
        geometryStr = "1150x" + str(self.master.winfo_reqheight())+"+"+str(self.master.winfo_toplevel().winfo_x())+"+"+str(self.master.winfo_toplevel().winfo_y())
        #print "geometrystr---->"+geometryStr+"<--"
        self.master.winfo_toplevel().geometry(geometryStr)
        
    def delayed_refresh_dimensions(self):       
            self.after(2,self.refresh_dimensions)            

    def startBusy(self, text):
        self.master.config(cursor="watch")
        self.master.statusBarText.set(text)
        self.update()
        self.update_idletasks()
        
    def stopBusy(self):
        self.master.config(cursor="")
        self.master.statusBarText.set("Idle")
        
        
class newVersionDialog(tkSimpleDialog.Dialog):

    def body(self, master):
        url = lastClientVersion[1]
        self.result = False

        Label(master, text="A new version of the \"Remote Connection Manager\" is available at:").grid(row=0)
        Label(master, text=url, underline = True, foreground='blue' ).grid(row=1)
        Label(master, text="It is highly recommended to install the new version to keep working properly.").grid(row=2)
        Label(master, text="Do you want to install it now?").grid(row=3)


    def apply(self):
        self.result = True
                

class newDisplayDialog(tkSimpleDialog.Dialog):

    def __init__(self,master,queues,vnc_menu):
        self.queues=queues
        self.vnc_menu=vnc_menu
        tkSimpleDialog.Dialog.__init__(self,master)

    def buttonbox(self):
        box = Frame(self.topFrame)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()
        
    def body(self, master):

        #Read configuration file
        self.configFileName = os.path.join(os.path.expanduser('~'),'.rcm','RCM.cfg')
        self.displayDimensions = NONE
        self.displayDimensionsList = collections.deque(maxlen=5)
        self.config = ConfigParser.RawConfigParser()
        if(os.path.exists(self.configFileName)):
            try:
                self.config.read(self.configFileName)

                displayDimensionsList = self.config.get('LoginFields', 'displayDimensionsList')
                self.displayDimensionsList = pickle.loads(displayDimensionsList)
            except:
                print "remove .cfg"
                os.remove(self.configFileName)    
                
        #master.pack(fill=BOTH,expand=1)
        #self.master=master
        self.topFrame = Frame(master)
        self.topFrame.pack(fill=BOTH,expand=1)
        sessionNameFrame = Frame(self.topFrame, padding = 5)
        Label(sessionNameFrame, text="""Session name: """).pack(side=LEFT)  
        self.SessionNameString = StringVar() 
        e = Entry(sessionNameFrame, textvariable=self.SessionNameString, width=20).pack(side=LEFT)
        
        sessionNameFrame.pack(padx=15)
        
        self.v = IntVar()
        self.displayDimension = NONE
        self.queue = StringVar(master)
        self.vnc = StringVar(master)
        queueList = self.queues.keys()
        vncList=self.vnc_menu.keys()
        self.queue.set(queueList[0])
        self.vnc.set(vncList[0])
        if (len(queueList) > 1):
            optionFrame = Frame(self.topFrame, padding = 5)
            Label(optionFrame, text="""Select queue:""").pack(side=LEFT)
            def print_it(event):
              print self.queue.get()
            qq=tuple(queueList)

            w = OptionMenu(optionFrame, self.queue, qq[0], *qq, command=print_it)
            w.pack(side=LEFT)
            optionFrame.pack( padx=15)
        if (len(vncList) > 1):
            vncFrame = Frame(self.topFrame, padding = 5)
            Label(vncFrame, text="""Select vnc:""").pack(side=LEFT)
            w = apply(OptionMenu, (vncFrame, self.vnc,vncList[0]) + tuple(vncList))
            w.pack(side=LEFT)
            vncFrame.pack(anchor=W, padx=15)

        displayFrame = Frame(self.topFrame, padding = 5)

        fullDisplayDimension = str(self.winfo_screenwidth()) + 'x' + str(self.winfo_screenheight())
        
        #always set full display as last item
        if (not len(list(self.displayDimensionsList)) > 0):
            self.displayDimensionsList.append("Full Screen")
        
        if (not "Full Screen" in list(self.displayDimensionsList)):
            self.displayDimensionsList.pop()
            self.displayDimensionsList.append("Full Screen")

        self.e1String = StringVar()
        Label(displayFrame, text="""Display size:    """).pack(side=LEFT)
        if (len(list(self.displayDimensionsList)) > 0):           
            self.displayVariable = StringVar(displayFrame)
            self.displayVariable.set(list(self.displayDimensionsList)[0]) # default value
            self.fillEntry(self.displayVariable)
            OptionMenu(displayFrame,self.displayVariable, list(self.displayDimensionsList)[0],*list(self.displayDimensionsList), command=self.fillEntry).pack(side=LEFT)
        displayFrame.pack(padx=15)

        entryFrame = Frame(self.topFrame, padding = 5)
        e1 = Entry(entryFrame, textvariable=self.e1String, width=16).pack(side=LEFT)        
        entryFrame.pack(padx=15)
        return e1
    
    def fillEntry(self,v):
        displayDimensions = self.displayVariable.get()
        if (displayDimensions == "Full Screen"):
            displayDimensions = str(self.winfo_screenwidth()) + 'x' + str(self.winfo_screenheight())

        self.e1String.set(displayDimensions)

    def validate(self):
        if not self.SessionNameString.get()[0:20]:
            tkMessageBox.showwarning("Error","Please insert a valid session name!")
            return False
        else:
            return True


    
    def apply(self):
        self.displayDimensions = self.e1String.get()
        #session name: get only first 20 char
        self.sessionName = self.SessionNameString.get()[0:20]#.replace(' ', '\ ')
                
        dimensions = self.e1String.get()
        if (self.e1String.get() == str(self.winfo_screenwidth()) + 'x' + str(self.winfo_screenheight())):
            dimensions = "Full Screen"
            
        if (dimensions in list(self.displayDimensionsList)):
            self.displayDimensionsList.remove(dimensions)
            
        self.displayDimensionsList.appendleft(dimensions)
        self.config.set('LoginFields', 'displayDimensionsList',pickle.dumps(self.displayDimensionsList))
            
        d = os.path.dirname(self.configFileName)
        if not os.path.exists(d):
            os.makedirs(d)
        with open(self.configFileName, 'wb') as configfile:
            self.config.write(configfile)
            
        self.destroy()
        return


class LoginDialog:

     def __init__(self, parent, guiaction=None, pack_info=None):
        self.guiaction = guiaction
        if(not pack_info):
            self.pack_info=rcm_utils.pack_info()
        else:
            self.pack_info=pack_info 
        self.parent = parent
        self.top = Toplevel(self.parent)
        geometry = '+' + str(self.parent.winfo_x()) + '+' + str(self.parent.winfo_y())
        self.top.geometry(geometry)
        self.my_rcm_client = rcm_client.rcm_client_connection(pack_info = self.pack_info)
        self.topFrame= Frame(self.top)
        self.topFrame.pack(fill=BOTH,expand=1)
        self.frameLogin = Login(guiaction=self.ok, action=self.my_rcm_client.login_setup, master=self.topFrame)
        self.top.grab_set()


     def ok(self):
         self.guiaction(self.my_rcm_client)
         self.top.destroy()
    
#class rcm_client_connection_GUI(rcm_client.rcm_client_connection):
class rcm_client_connection_GUI():
    def __init__(self):
        self.pack_info=rcm_utils.pack_info()
        self.last_used_dir='.'

    def show(self):
        self.master = Tk()
        self.master.title('Remote Connection Manager ' + self.pack_info.rcmVersion + ' - CINECA')
        self.master.geometry("1150x180+100+100")
        self.topFrame = Frame(self.master)
        self.topFrame.pack(fill=BOTH,expand=1)
        #mycolor='#%02x%02x%02x' % (240,240,237)
        #self.master.configure(bg='gray')

        self.gui = None
        
        #s_color = Style()
        #s_color.configure('RCM.Color', background='gray')

        self.frame1 = LabelFrame(self.topFrame, padding=20, text='LOGIN MANAGER')

        self.frame1.pack(side=LEFT,  padx=10, pady=10, fill=Y)
        #print self.frame1.configure(background='gray')
        #print "in frame1 background--->"+str(self.frame1.cget('background'))+"<-- framecolor -->",str(self.frame1.cget('framecolor'))

        self.LoginLabel = Label(self.topFrame, padding=20, text='Press \'NEW LOGIN\' to start a session or \'OPEN\' to open a .vnc file')
        self.LoginLabel.pack(padx=10, pady=10, fill=Y)

        self.n = ConnectionWindowNotebook(self.topFrame)

        s = Style()
        s.configure('RCM.TButton', font=('Helvetica', 10, 'bold'))
        s.map('RCM.TButton',foreground=[('disabled','#909090')])
       
        LoginButton = Button(self.frame1, text="NEW LOGIN", padding=5, style='RCM.TButton', command=self.newLogin)
        LoginButton.pack()

        OpenButton = Button(self.frame1, text="   OPEN   ", padding=5, style='RCM.TButton', command=self.askopenfilename)
        OpenButton.pack(pady=10)

        self.frameBottom = Frame(self.topFrame, padding=1)
        self.frameBottom.pack(side=BOTTOM, fill=X)

        self.topFrame.statusBarText = StringVar()
        self.topFrame.statusBarText.set("Idle")
        self.status = Label(self.frameBottom, textvariable=self.topFrame.statusBarText, padding=1, relief=SUNKEN, anchor=W)
        self.status.pack(side=BOTTOM, fill=X)

    def mainloop(self):
        self.master.mainloop()


    def newLogin(self):

        myLoginDialog = LoginDialog(self.master, guiaction = self.createConnectionWindow, pack_info = self.pack_info)
        myLoginDialog.top.grab_set()


    def askopenfilename(self,filename=None):
        if(not filename):
            file_opt = options = {}
            options['filetypes'] = [('vnc files', '.vnc'), ('all files', '.*')]
            filename = tkFileDialog.askopenfilename(initialdir=self.last_used_dir,**file_opt)

        if filename:
            tunnel = False
            my_rcm_client = rcm_client.rcm_client_connection(pack_info = self.pack_info)
            my_rcm_client.passwd = ''

            #check if session needs tunneling
            file = open(filename, 'r')
            if 'rcm_tunnel' in file.read():
                file.seek(0)
                lines = file.readlines()
                for l in lines:
                    if 'rcm_tunnel' in l:
                        node = l.split('=')[1].rstrip()
                        #check credential for the cluster, not for the specific node
                        credential = self.n.getConnectionInfo(node.split('.',1)[1])
                        if credential != None:
                            user = credential['user']
                            my_rcm_client.login_setup(host=node,remoteuser=user,password=credential['password'])
                        else:
                            tkMessageBox.showwarning("Warning!", "Please login to \"{0}\" to open this shared display.".format(node))
                            return

                    if 'host' in l:
                        hostname = l.split('=')[1].rstrip()
                    if 'port' in l:
                        port = l.split('=')[1].rstrip()
                        display = int(port) - 5900
                    if 'password' in l:
                        password = l.split('=')[1].rstrip()

                c=rcm.rcm_session(node=hostname, tunnel='y', display=display, nodelogin=node, username=user, vncpassword=password)
                my_rcm_client.vncsession(session = c)
            else:
                my_rcm_client.vncsession(configFile = filename)
            self.last_used_dir=os.path.dirname(filename)


    def createConnectionWindow(self, rcm_client = None):
        exists = False
        if (self.LoginLabel):
            self.LoginLabel.destroy()
        self.n.pack(expand=1, fill=BOTH)
        self.rcm_client = rcm_client
        self.n.myadd(self.rcm_client)



class ConnectionWindowNotebook(Notebook):
    @safe_debug_off
    def __init__(self, master = None):
        self.master = master
        Notebook.__init__(self, master)
        self.ConnectionWindows = dict()


    def myadd(self, rcm_client = None):
        if rcm_client:
            notebookName = rcm_client.remoteuser + "@" + rcm_client.proxynode

            if notebookName in self.ConnectionWindows:
                self.select(self.ConnectionWindows[notebookName][0])
            else:
                child = ConnectionWindow(rcm_client_connection=rcm_client, master=self.master)
                Notebook.add(self, child, text = notebookName)
                index = self.index('end') - 1
                self.ConnectionWindows[notebookName] = (index, child)
                self.select(index)

    def getConnectionInfo(self, tunnel_node = ''):
        for i in self.ConnectionWindows:
            if tunnel_node in i:
                credential = dict()
                credential['user'] = self.ConnectionWindows[i][1].client_connection.remoteuser
                credential['password'] = self.ConnectionWindows[i][1].client_connection.passwd
                return credential


if __name__ == '__main__':
    c=rcm_client_connection_GUI()
    if(1 < len(sys.argv)):
        c.askopenfilename(sys.argv[1])
    else:
        c.show()
        c.mainloop()


