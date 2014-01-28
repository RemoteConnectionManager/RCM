#!/bin/env python

import os
import tempfile
import rcm_client
import rcm


from Tkinter import *
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


font = ("Helvetica",10, "grey")
boldfont = ("Helvetica",10,"bold")
checkCredential = False 
queueList = []
lastClientVersion = []


def safe(debug=False):
    def safedec(f):
        def fsafe(*l_args, **d_args):
            try:
                return f(*l_args, **d_args)
            except Exception as e:
                try:
                    l_args[0].stopBusy()
                except:
                    pass
                if debug:
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
    file_name = url.split('/')[-1]
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
        status = r"{0}  [{1:.2%}]".format(file_size_dl, p)
        
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
    def __init__(self, master=None,action=None,basedir=None):
        
        #Read configuration file
        self.configFileName = os.path.join(os.path.expanduser('~'),'.rcm','RCM.cfg')
        userName=""
        self.hostCollections = collections.deque(maxlen=5)
        self.config = ConfigParser.RawConfigParser()
        if(os.path.exists(self.configFileName)):
            try:
                self.config.read(self.configFileName)    
                hostList = self.config.get('LoginFields', 'hostList')
                self.hostCollections=pickle.loads(hostList)

            except:
                os.remove(self.configFileName)
                    

        Frame.__init__(self, master)
        self.pack( padx=20, pady=30 )
        self.master.title("RCM Login:")
        self.action=action
        self.master.geometry("+200+200")
        
        #CINECA LOGO       
        
        imagePath = os.path.join(basedir,'logo_cineca.gif')
        
        im = PhotoImage(file=imagePath)
        lbl = Label(self, image=im, relief=GROOVE, border=2)
        lbl.image = im
        lbl.pack(side=TOP)
        
        titleFrame = Frame(self, padx = 1, bd=10)
        w = Label(titleFrame, text='REMOTE CONNECTION MANAGER', height=1)
        w["font"]=boldfont
        w.pack(side=TOP)

        w = Label(titleFrame, text='version: '+ rcm_client.rcmVersion, height=1)
        w.pack(side=TOP)
        titleFrame.pack() 
           
        loginFrame = Frame(self, padx = 20, bd=8)
        
        self.host = StringVar()  
        self.user = StringVar()
        self.password = StringVar()
        
        if (len(list(self.hostCollections)) > 0):
            Label(loginFrame, text="""Sessions:""").grid(row=0)
            self.variable = StringVar(loginFrame)
            self.variable.set(list(self.hostCollections)[0]) # default value
            self.fillCredentials(self.variable)
            OptionMenu(loginFrame, self.variable, *list(self.hostCollections), command=self.fillCredentials).grid(row=0, column=1, sticky=W)        
        
        Label(loginFrame, text="Host: ",height=2).grid(row=1)
        Label(loginFrame, text="User: ",height=2).grid(row=2)
        Label(loginFrame, text="Password:",height=2).grid(row=3)

        
        hostEntry = Entry(loginFrame, textvariable=self.host, width=16)
        userEntry = Entry(loginFrame, textvariable=self.user, width=16)
        passwordEntry = Entry(loginFrame, textvariable=self.password, show="*", width=16)

        hostEntry.grid(row=1, column=1)
        userEntry.grid(row=2, column=1)
        passwordEntry.grid(row=3, column=1) 
        loginFrame.pack()       

        self.b = Button(self, borderwidth=2, text="LOGIN", width=10, pady=8, command=self.login)
        self.b["font"]=boldfont
        self.b.pack(side=BOTTOM)
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
                
                self.destroy()
                self.quit()
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
        self.debug=False
        Frame.__init__(self, master)
        self.client_connection=rcm_client_connection
        self.connection_buttons=dict()
        self.pack( padx=10, pady=10 )
        self.master.title("Remote Connection Manager " + rcm_client.rcmVersion +" - CINECA")
        self.master.minsize(800,130)
        self.bind("<<list_refresh>>",self.list_refresh)
        
        self.f1=None
        self.f1 = Frame(self, width=500, height=100)
        self.f1.grid( row=0,column=0) 
        self.f1.pack()
        w = Label(self.f1, text='Please wait...', height=2)
        w.grid( row=1,column=0)
        
        self.f2 = Frame(self, bd=10)
        #tryluigiself.f2.grid( row=1,column=0) 
        button = Button(self.f2, text="NEW DISPLAY", borderwidth=2, command=self.submit)
        button["font"]=boldfont
        button.grid( row=0,column=0 )
 
        button = Button(self.f2, text="REFRESH", borderwidth=2, command=self.list_refresh)
        button["font"]=boldfont
        button.grid( row=0,column=1 )                
        self.statusBarText = StringVar()
        self.statusBarText.set("Idle")
        self.status = Label(self.master, textvariable=self.statusBarText, bd=1, relief=SUNKEN, anchor=W)
        self.status.pack(side=BOTTOM, fill=X)
        self.f2.pack(side=BOTTOM)
        
        self.bind("<Destroy>", self.deathHandler)
        #check version after mainloop is started
        self.after(500,self.check_version)
    
    @safe_debug_off   
    def check_version(self):       
        self.startBusy("Checking new client version...")
        if('frozen' in dir(sys)):
            currentChecksum = compute_checksum(sys.executable)
            global lastClientVersion
            lastClientVersion = self.client_connection.get_version()
            
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
#        self.list_refresh()
        self.update_idletasks()
        self.event_generate("<<list_refresh>>")

       
    @safe_debug_off
    def update_sessions(self,ss):
        buttonHeight = 0
        self.sessions=ss
        if(self.f1):
            for child in self.f1.winfo_children():
                child.destroy()

        if len(self.sessions.array) == 0:
            w = Label(self.f1, text='No display available. Press \'NEW DISPLAY\' to create a new one.', height=2)
            w.pack()
        else:
            f1 = self.f1
            labelList = ['created', 'display', 'node', 'state', 'username', 'walltime', 'timeleft']
            c=rcm.rcm_session()
            i = 0
            for t in sorted(c.hash.keys()):
                if t in labelList:
                    w = Label(f1, text=t.upper(), relief=RIDGE, state=ACTIVE)
                    w.grid( row=0,column=i+2, sticky="we")
                    f1.columnconfigure ( i, minsize=80 )
                    i = i + 1
            
            for line, el in  enumerate( self.sessions.array ):
                if(self.client_connection):
                
                    def cmd(self=self, sessionid=el.hash['sessionid']):
                        if(self.debug): print "killing session", sessionid
                        self.kill(sessionid)
                        
                    if(el.hash['state'] == 'killed'):
                        continue
                    bk = Button( f1, text="KILL", borderwidth=2, command=cmd )
                    bk["font"]=boldfont
                    bk.grid( row=line+1, column=1 )
                    
                    bc = Button( f1, text="CONNECT", borderwidth=2)
                    bc["font"]=boldfont
                    bc.grid( row=line+1, column=0 )
                    buttonHeight = bc.winfo_reqheight()
                    sessionid = el.hash['sessionid']
                    
                    def disable_cmd(self=self, sessionid=el.hash['sessionid'],active=True):
                        button=self.connection_buttons[sessionid][0]
                        if(button.winfo_exists()):
                            if(active):
                                self.client_connection.activeConnectionsList.append(sessionid)
                                button.configure(state=DISABLED)
                            else:
                                button.configure(state=ACTIVE)
                                self.client_connection.activeConnectionsList.remove(sessionid)
#                                self.list_refresh()
                                self.event_generate("<<list_refresh>>") 
                                
                    self.connection_buttons[sessionid]=(bc,disable_cmd)
                    
                    
                    def cmd(self=self, session=el,disable_cmd=disable_cmd):
                        if(self.debug): print "connecting to session", session.hash['sessionid']
                        self.startBusy("Connecting to the remote display...")
                        self.client_connection.vncsession(session,gui_cmd=disable_cmd)
                        self.after(4000,self.stopBusy)
                        
                    bc.configure( command=cmd )
                    if sessionid in self.client_connection.activeConnectionsList:
                        bc.configure(state=DISABLED)
            
                i = 0
                for t in sorted(c.hash.keys()):
                    if t in labelList:
                        lab = Label(f1, text=el.hash[t])
                        if t == 'timeleft':
                            try:
                                timeleft = datetime.datetime.strptime(el.hash[t],"%H:%M:%S")
                                endTime = timeleft.replace(hour=0,minute=0,second=0)
                                limit = timeleft - endTime
                                if limit < datetime.timedelta(hours=1):
                                    lab.configure(fg="red")
                            except:
                                pass
                        lab.grid( row=line+1, column=i+2 )
                        i = i + 1
            

    @safe_debug_off
    def kill(self, sessionid):  
        self.startBusy("Killing the remote display...")
        self.client_connection.kill(sessionid)

        refreshList = self.client_connection.list()
        self.update_sessions(refreshList)
        self.stopBusy()
        self.delayed_refresh_dimensions()
  

    @safe_debug_off
    def submit(self):
        self.startBusy("Waiting for queue list...")
        global queueList
        queueList = self.client_connection.get_queue()
        self.stopBusy()
        if(self.debug): print "Queue list: ", queueList
        if queueList == ['']:
            tkMessageBox.showwarning("Warning", "Queue not found...")
            return
        
        dd = newDisplayDialog(self)
        if dd.displayDimensions == NONE:
            self.stopBusy()
            return
        
        self.displayDimension = dd.displayDimensions
        self.queue = dd.queue.get()
        self.startBusy("Creating a new remote display...")
        if(self.debug): print "Requesting new connection"
        newconn=self.client_connection.newconn(self.queue, self.displayDimension)

        if(self.debug): print "New connection aquired"
        
        refreshList = self.client_connection.list()
        self.update_sessions(refreshList)
        self.delayed_refresh_dimensions()
        self.startBusy("Connecting to the remote display...")
        time.sleep(2)
        self.client_connection.vncsession(newconn, newconn.hash['otp'], self.connection_buttons[newconn.hash['sessionid']][1] )
        self.after(2000,self.stopBusy)
        

    @safe_debug_off
    def list_refresh(self,event=None):       
        self.startBusy("Refreshing display list...")
        refreshList = self.client_connection.list()
        self.update_sessions(refreshList)
        self.stopBusy()
        self.delayed_refresh_dimensions()            

    def refresh_dimensions(self):       
        self.update_idletasks()
#        newHeight = self.f1.winfo_reqheight() + self.f2.winfo_reqheight() + self.status.winfo_reqheight() + 10
#        geometryStr = "800x" + str(newHeight)
        geometryStr = "800x" + str(self.winfo_reqheight()+ self.status.winfo_reqheight() + 20)
        self.master.geometry(geometryStr)

    def delayed_refresh_dimensions(self):       
            self.after(2,self.refresh_dimensions)            

    def startBusy(self, text):
        self.master.config(cursor="watch")
        self.statusBarText.set(text)
        self.update()
        self.update_idletasks()
        
    def stopBusy(self):
        self.master.config(cursor="")
        self.statusBarText.set("Idle")
        
        
class newVersionDialog(tkSimpleDialog.Dialog):

    def body(self, master):
        url = lastClientVersion[1]
        self.result = False

        Label(master, text="A new version of the \"Remote Connection Manager\" is avaiable at:").grid(row=0)
        ent = Entry(master, state='readonly', fg='blue', width=len(url), justify=CENTER)
        var = StringVar()
        var.set(url)
        ent.config(textvariable=var, relief='flat', highlightthickness=0)
        ent.grid(row=1)
        Label(master, text="It is highly recommended to install the new version to keep working properly.").grid(row=2)
        Label(master, text="Do you want to install it now?").grid(row=3)
        
        # clone the font, set the underline attribute,
        # and assign it to our widget
        f = tkFont.Font(ent, ent.cget("font"))
        f.configure(underline = True)
        ent.configure(font=f)

    def apply(self):
        self.result = True
                
        

class newDisplayDialog(tkSimpleDialog.Dialog):
    
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
        
        self.v = IntVar()
        self.displayDimension = NONE
        self.queue = StringVar(master)
        self.queue.set(queueList[0])
        if (len(queueList) > 1):
            optionFrame = Frame(master, padx = 20, bd=5)
            Label(optionFrame, text="""Select queue:""").pack(side=LEFT)        
            w = apply(OptionMenu, (optionFrame, self.queue) + tuple(queueList))
            w.pack(side=LEFT)
            optionFrame.pack(anchor=W)
        
        displayFrame = Frame(master, padx = 20, bd=5)

        fullDisplayDimension = str(self.winfo_screenwidth()) + 'x' + str(self.winfo_screenheight())
        
        #always set full display as last item
        if (not len(list(self.displayDimensionsList)) > 0):
            self.displayDimensionsList.append("Full Screen")
        
        if (not "Full Screen" in list(self.displayDimensionsList)):
            self.displayDimensionsList.pop()
            self.displayDimensionsList.append("Full Screen")     


        self.e1String = StringVar()  
        Label(displayFrame, text="""Display size:""").pack(side=LEFT)
        if (len(list(self.displayDimensionsList)) > 0):           
            self.displayVariable = StringVar(displayFrame)
            self.displayVariable.set(list(self.displayDimensionsList)[0]) # default value
            self.fillEntry(self.displayVariable)
            OptionMenu(displayFrame,self.displayVariable, *list(self.displayDimensionsList), command=self.fillEntry).pack(side=LEFT)        
        displayFrame.pack(anchor=W) 

        entryFrame = Frame(master, padx = 20, bd=2)        
        e1 = Entry(entryFrame, textvariable=self.e1String, width=16).pack(side=LEFT)        
        entryFrame.pack(anchor=W)
        return e1
    
    def fillEntry(self,v):
        displayDimensions = self.displayVariable.get()
        if (displayDimensions == "Full Screen"):
            displayDimensions = str(self.winfo_screenwidth()) + 'x' + str(self.winfo_screenheight())

        self.e1String.set(displayDimensions)
        
    
    def apply(self):
        self.displayDimensions = self.e1String.get()
        
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
            
    
class rcm_client_connection_GUI(rcm_client.rcm_client_connection):
    def __init__(self):
        rcm_client.rcm_client_connection.__init__(self)
        self.login = Login(action=self.login_setup,basedir=self.basedir)
        self.login.mainloop()
        
        if(self.debug): print "Check credential returned: " + str(checkCredential)
        if checkCredential:
            gui = ConnectionWindow(rcm_client_connection=self)
            gui.mainloop()


if __name__ == '__main__':
    #try:
#        c.debug=True
    c=rcm_client_connection_GUI()
##	c.debug=True
##        gui = ConnectionWindow()
        
##        res=c.list()
##        res.write(2)
##        newc=c.newconn()
##        newsession = newc.hash['sessionid']
##        print "created session -->",newsession,"<- display->",newc.hash['display'],"<-- node-->",newc.hash['node']
##        c.vncsession(newc)
##        res=c.list()
##        res.write(2)
##        c.kill(newsession)
##        res=c.list()
##        res.write(2)
        
        
    #except Exception:
    #    print "ERROR OCCURRED HERE"
    #    raise
  
