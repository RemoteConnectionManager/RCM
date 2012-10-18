#!/bin/env python

import os
import tempfile
import rcm_client
import rcm


from Tkinter import *
import ttk
import tkMessageBox
import tkSimpleDialog
import time
import ConfigParser
import datetime
import threading
import Queue
import tkFont
import hashlib
import webbrowser
import urllib2
import tempfile


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
                if debug:
                    import traceback
                    tkMessageBox.showwarning("Error","in {0}: {1}\n{2}".format(f.__name__, e,traceback.format_exc()))
                    traceback.print_exc()
                else:
                    tkMessageBox.showwarning("Error", e)
                
        return fsafe
    return safedec

safe_debug_on = safe(True)
safe_debug_off = safe(True)

def compute_checksum(filename):
    fh = open(filename, 'rb')
    m = hashlib.md5()
    while True:
        data = fh.read(8192)
        if not data:
            break
        m.update(data)
    return m.hexdigest()
        
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
    def __init__(self, master=None,action=None):
        
        #Read configuration file
        self.configFileName = os.path.join(os.path.expanduser('~'),'.rcm','RCM.cfg')
        userName=""
        self.customDisplayDimension=''
        if(os.path.exists(self.configFileName)):
            try:
                config = ConfigParser.RawConfigParser()
                config.read(self.configFileName)
                userName = config.get('LoginFields', 'username')
                self.customDisplayDimension = config.get('LoginFields', 'displaydimension')
            except:
                os.remove(self.configFileName)
                    

        Frame.__init__(self, master)
        self.pack( padx=10, pady=10 )
        self.master.title("RCM Login:")
        self.action=action
        self.master.geometry("+200+200")
        self.user = StringVar()
        self.user.set(userName)
        user_entry = self.make_entry( "User name:", 16, textvariable=self.user)
        self.password = StringVar()
        password_entry = self.make_entry( "Password:", 16, textvariable=self.password, show="*")
        self.b = Button(self, borderwidth=2, text="Login", width=10, pady=8, command=self.login)
        self.b.pack(side=BOTTOM)
        password_entry.bind('<Return>', self.enter)
        user_entry.focus_set()
       
    def enter(self,event):
        self.login()
        
    def login(self):     
        if  (self.user.get() and self.password.get()):
            #Write configuration file
            config = ConfigParser.RawConfigParser()
            config.add_section('LoginFields')
            config.set('LoginFields', 'username',self.user.get())
            config.set('LoginFields', 'displaydimension',self.customDisplayDimension)
            d = os.path.dirname(self.configFileName)
            if not os.path.exists(d):
                os.makedirs(d)
            
            with open(self.configFileName, 'wb') as configfile:
                config.write(configfile)
            
            #Start login only if all the entry are filled
            global checkCredential 
            checkCredential = self.action(self.user.get(), self.password.get())
            if checkCredential:
                self.destroy()
                self.quit()
                return
            else:
                tkMessageBox.showwarning("Error","Authentication failed!")
                return
                
    
    def make_entry(self, caption, width=None, **options):
        Label(self, text=caption).pack(side=TOP)
        entry = Entry(self, **options)
        if width:
            entry.config(width=width)
        entry.pack(side=TOP, padx=10, fill=BOTH)
        return entry


class ConnectionWindow(Frame):
       
    @safe_debug_off
    def __init__(self, master=None,rcm_client_connection=None):
        self.debug=True
        Frame.__init__(self, master)
        self.client_connection=rcm_client_connection
        self.connection_buttons=dict()
        self.pack( padx=10, pady=10 )
        self.master.title("Remote Connection Manager " + rcm_client_connection.rcmVersion +" - CINECA")
        self.master.geometry("800x115+200+200")
        self.master.minsize(800,80)
        
        self.q = Queue.Queue()
        self.updateGUI()
        
        self.progressbar = ttk.Progressbar(orient=HORIZONTAL, length=200, mode='determinate')
        self.progressbar.pack(side="top")
        
        self.f1=None
        self.f2 = Frame(self)
        self.f2.grid( row=1,column=0) 
        button = Button(self.f2, text="NEW DISPLAY", borderwidth=2, command=self.submit)
        button["font"]=boldfont
        button.grid( row=0,column=0 )
 
        button = Button(self.f2, text="REFRESH", borderwidth=2, command=self.refresh)
        button["font"]=boldfont
        button.grid( row=0,column=1 )
        
        #StatusBar = Label(self.master, text="idle..", relief=RIDGE  )
        #StatusBar.pack({"side":"left", "expand":"yes", "fill":"x"})       
        self.check_version();

    
    @safe_debug_off   
    def check_version(self):
        t = threading.Thread(target=self.check_versionThread)
        t.start()


    def check_versionThread(self):
        try:
            self.q.put( (self.startProgress,) )
            if('frozen' in dir(sys)):
                currentChecksum = compute_checksum(sys.executable)
                global lastClientVersion
                lastClientVersion = self.client_connection.get_version()
                
                self.q.put( (self.checkVersionDialog,currentChecksum) )
                
                self.q.put( (self.stopProgress,) )
        except Exception as e:
            self.q.put( (self.raiseException, e) )
         
    def checkVersionDialog(self, currentChecksum):
        if(currentChecksum != lastClientVersion[0]):
            verDialog = newVersionDialog(self)
            if (verDialog.result == True):
                self.q.put( (self.startProgress,) )
                update_exe_file()
                self.master.quit()
        rt = threading.Thread(target=self.refreshThread)
        rt.start()
            
       
    @safe_debug_off
    def update_sessions(self,ss):
        buttonHeight = 0
        self.sessions=ss
        if(self.f1):
            self.f1.destroy()

        self.f1 = Frame(self, width=500, height=100)
        self.f1.grid( row=0,column=0) 
        if len(self.sessions.array) == 0:
            w = Label(self.f1, text='No display available. Press \'NEW DISPLAY\' to create a new one.', height=2)
            w.grid( row=1,column=0)
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
                                
                    self.connection_buttons[sessionid]=(bc,disable_cmd)
                    
                    def cmd(self=self, session=el,disable_cmd=disable_cmd):
                        if(self.debug): print "connecting to session", session.hash['sessionid']
                        self.client_connection.vncsession(session,gui_cmd=disable_cmd)
                    bc.configure( command=cmd )
                    if sessionid in self.client_connection.activeConnectionsList:
                        bc.configure(state=DISABLED)
            
                i = 0
                for t in sorted(c.hash.keys()):
                    if t in labelList:
                        lab = Label(f1, text=el.hash[t])
                        if t == 'timeleft':
                            timeleft = datetime.datetime.strptime(el.hash[t],"%H:%M:%S")
                            endTime = timeleft.replace(hour=0,minute=0,second=0)
                            limit = timeleft - endTime
                            if limit < datetime.timedelta(hours=1):
                                lab.configure(fg="red")                      
                        lab.grid( row=line+1, column=i+2 )
                        i = i + 1
            
        newHeight = 115 + buttonHeight * len(self.sessions.array)
        geometryStr = "800x" + str(newHeight)
        self.master.geometry(geometryStr)

    @safe_debug_off
    def kill(self, sessionid):  
        threading.Thread(target=self.killThread, args=(sessionid,)).start()
        
  
    def killThread(self, sessionid):
        try:
            self.q.put( (self.startProgress,) )
            self.client_connection.kill(sessionid)
            
            #qdel takes some time...
            time.sleep(5)

            refreshList = self.client_connection.list()
            self.q.put( (self.update_sessions, refreshList) )
            self.q.put( (self.stopProgress,) )
        except Exception as e:
            self.q.put( (self.raiseException, e) )

    @safe_debug_off
    def submit(self):
        global queueList
        queueList = self.client_connection.get_queue()
        if(self.debug): print "Queue list: ", queueList
        if queueList == ['']:
            tkMessageBox.showwarning("Warning", "Queue not found...")
            return

        #ask for queue and screen dimesions
        dd = newDisplayDialog(self)
                
        if dd.displayDimension == NONE:
            return
        
        self.displayDimension = dd.displayDimension
        self.queue = dd.queue.get()
        t = threading.Thread(target=self.submitThread).start()
                    
        
    def submitThread(self):
        try:
            self.q.put( (self.startProgress,) )
            if(self.debug): print "Requesting new connection"
            newconn=self.client_connection.newconn(self.queue, self.displayDimension)

            if(self.debug): print "New connection aquired"
            
            refreshList = self.client_connection.list()
            self.q.put( (self.update_sessions, refreshList) )
            time.sleep(2)
            self.q.put( (self.client_connection.vncsession, newconn, newconn.hash['otp'], self.connection_buttons[newconn.hash['sessionid']][1] ) )

            if(self.debug): print "End submit"     
            self.q.put( (self.stopProgress,) )
        except Exception as e:
            self.q.put( (self.raiseException, e) )
 
    @safe_debug_off
    def refresh(self):
        t = threading.Thread(target=self.refreshThread)
        t.start()
                
    def refreshThread(self):
        try:
            self.q.put( (self.startProgress,) )
            if(self.debug): print "Refresh connection list"
            refreshList = self.client_connection.list()
            self.q.put( (self.update_sessions, refreshList) )
            if(self.debug): print "End Refresh connection list"
            self.q.put( (self.stopProgress,) )
        except Exception as e:
            self.q.put( (self.raiseException, e) )
        
    def raiseException(self, error):
        #self.stopProgress()
        self.q.put( (self.stopProgress,) )
        self.q.put( (self.master.config(cursor=""),))
        tkMessageBox.showwarning("Error", error)
        
    
    def updateGUI(self):
        try:
            while True :
                items = self.q.get_nowait()
                print items
                func = items[0]
                if func:
                    args = items[1:]
                    func(*args)
        except Queue.Empty:
            pass
        self.after(100, self.updateGUI)

    def startProgress(self):
        self.progressbar.configure(mode='indeterminate')
        self.progressbar.start()
        self.master.config(cursor="watch")
        
    def stopProgress(self):
        self.progressbar.stop()  
        self.progressbar.configure(mode='determinate')
        self.master.config(cursor="")
        
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
        #self.configFileName = os.path.join(tempfile.gettempdir(),'RCM.cfg')
        self.configFileName = os.path.join(os.path.expanduser('~'),'.rcm','RCM.cfg')
        self.userName=''
        self.customDisplayDimension=''
        if(os.path.exists(self.configFileName)):
            try:
                config = ConfigParser.RawConfigParser()
                config.read(self.configFileName)
                self.userName = config.get('LoginFields', 'username')
                self.customDisplayDimension = config.get('LoginFields', 'displaydimension')
            except:
                os.remove(self.configFileName)        
        
        self.v = IntVar()
        self.displayDimension = NONE
        optionFrame = Frame(master, padx = 20)
        
        Label(optionFrame, text="""Select a queue:""").pack(side=LEFT)        
        self.queue = StringVar(master)
        self.queue.set(queueList[0]) # default value
        w = apply(OptionMenu, (optionFrame, self.queue) + tuple(queueList))
        w.pack(side=LEFT)
        
        optionFrame.pack(anchor=W)
        
        self.fullDisplayDimension = str(self.winfo_screenwidth()) + 'x' + str(self.winfo_screenheight())
        if self.customDisplayDimension == '':
            self.customDisplayDimension = self.fullDisplayDimension
        self.e1 = Entry(master)
        self.e1.insert (0, self.customDisplayDimension)
        self.e1.config(state=DISABLED)
    
        self.text = ['Full screen', 'custom']
        Label(master, text="""Choose display dimensions:""", padx = 20).pack(anchor=W)
        Radiobutton(master, text=self.text[0], padx = 20, variable=self.v, value=0, command=self.enableEntry).pack(anchor=W)
        Radiobutton(master, text=self.text[1], padx = 20,variable=self.v, value=1, command=self.enableEntry).pack(anchor=W)
        self.e1.pack(padx = 20, anchor=W)
        return self.e1
        
    
    def enableEntry(self):
        if  self.v.get() == 1:
            self.e1.config(state=NORMAL)
        else:
            self.e1.config(state=DISABLED)
                
    
    def apply(self):
        if  self.v.get() == 0:
            #Full screen
            self.displayDimension = self.fullDisplayDimension
        if self.v.get() == 1:
            self.displayDimension = self.e1.get()
        self.destroy()
        
        #Write configuration file
        config = ConfigParser.RawConfigParser()
        config.add_section('LoginFields')
        config.set('LoginFields', 'username',self.userName)
        config.set('LoginFields', 'displaydimension',self.displayDimension)
        d = os.path.dirname(self.configFileName)
        if not os.path.exists(d):
            os.makedirs(d)
        with open(self.configFileName, 'wb') as configfile:
            config.write(configfile)
        return
            
    
    
class rcm_client_connection_GUI(rcm_client.rcm_client_connection):
    def __init__(self):
        rcm_client.rcm_client_connection.__init__(self)
        self.login = Login(action=self.login_setup)
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
  