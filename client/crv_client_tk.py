#!/bin/env python

import crv_client
import crv

from Tkinter import *
import tkMessageBox
import time

font = ("Helvetica",10, "grey")
boldfont = ("Helvetica",10,"bold")
checkCredential = False 

class Login(Frame):
    def __init__(self, master=None,action=None,proxynode='login2.plx.cineca.it'):

        Frame.__init__(self, master)
        self.pack( padx=10, pady=10 )
        self.master.title("Login:")
        self.action=action
        self.master.geometry("+200+200")
        self.proxy = StringVar()
        self.proxy.set(proxynode)
        self.proxynode = self.make_entry( "Host:", 16, textvariable=self.proxy)
        self.user = StringVar()
        user_entry = self.make_entry( "User name:", 16, textvariable=self.user)
        self.password = StringVar()
        password_entry = self.make_entry( "Password:", 16, textvariable=self.password, show="*")
        self.b = Button(self, borderwidth=4, text="Login", width=10, pady=8, command=self.login)
        self.b.pack(side=BOTTOM)
        password_entry.bind('<Return>', self.enter)
        user_entry.focus_set()
       
    def enter(self,event):
        self.login()

    def login(self):
        """ Collect 1's for every failure and quit program in case of failure_max failures """

        #print(self.proxynode.get(),self.user.get(), self.password.get())
        
        if  (self.proxynode.get() and self.user.get() and self.password.get()):
            #Start login only if all the entry are filled
            global checkCredential 
            checkCredential = self.action(self.proxynode.get(),self.user.get(), self.password.get())
            if checkCredential:
                self.destroy()
                self.quit()
                print('Logged in')
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
    def __init__(self, master=None,crv_client_connection=None):
        self.debug=False
        Frame.__init__(self, master)
        self.client_connection=crv_client_connection
        self.connection_buttons=dict()
        self.pack( padx=10, pady=10 )
        self.master.title("CRV Connection Manager")
        self.master.geometry("750x80+200+200")
        self.master.minsize(700,80)
        self.f1=None
        self.f2=None


        self.f3 = Frame(self, width=500, height=100)
        self.f3.grid( row=6,column=0) 
        button = Button(self.f3, text="NEW DISPLAY", borderwidth=2, command=self.submit)
        button["font"]=boldfont
        button.grid( row=6,column=0 )
 
        button = Button(self.f3, text="REFRESH", borderwidth=2, command=self.refresh)
        button["font"]=boldfont
        button.grid( row=6,column=1 )
       
        
    def update_sessions(self,ss):
        self.sessions=ss
        if(self.f1):
            self.f1.destroy()
        self.f1 = Frame(self, width=500, height=100)
        self.f1.grid( row=1,column=0) 
        f1 = self.f1
        labelList = ['created', 'display', 'node', 'state', 'username', 'walltime']
        
        if(self.f2):
            self.f2.destroy()
        if len(self.sessions.array) == 0:
            self.f2 = Frame(self, width=500, height=100)
            self.f2.grid( row=1,column=0) 
            w = Label(self.f2, text='No display available. Press \'NEW DISPLAY\' to create a new one.', height=2)
            w.grid( row=1,column=0)
            geometryStr = "750x160"
            self.master.geometry(geometryStr)
        else:

        
            c=crv.crv_session()
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
                        print "killing session", sessionid
                        self.client_connection.kill(sessionid)
                        time.sleep(2)
                        self.update_sessions(self.client_connection.list())
                    bk = Button( f1, text="KILL", borderwidth=2, command=cmd )
                    bk["font"]=boldfont
                    
                    bk.grid( row=line+1, column=1 )
                    
                    bk = Button( f1, text="CONNECT", borderwidth=2)
                    bk["font"]=boldfont
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
                    self.connection_buttons[sessionid]=(bk,disable_cmd)
                    def cmd(self=self, session=el,disable_cmd=disable_cmd):
                        print "connecting to session", session.hash['sessionid']
                        self.client_connection.vncsession(session,gui_cmd=disable_cmd)
                    bk.configure( command=cmd )
                    if sessionid in self.client_connection.activeConnectionsList:
                        bk.configure(state=DISABLED)

                    bk.grid( row=line+1, column=0 )
                    
            
            
                i = 0
                for t in sorted(c.hash.keys()):
                    if t in labelList:
                        lab = Label(f1, text=el.hash[t])
                        lab.grid( row=line+1, column=i+2 )
                        i = i + 1
            
                newHeight = 80 + 35 * len(self.sessions.array)
                geometryStr = "750x" + str(newHeight)
                self.master.geometry(geometryStr)

    

    def submit(self):
        print "Requesting new connection"
        newconn=self.client_connection.newconn()
        print "New connection aquired"
        newconn.write(2)
        if(self.debug): print "Update connection panel"
        self.update_sessions(self.client_connection.list())
        #self.connection_buttons[newconn.hash['sessionid']].invoke()
        self.client_connection.vncsession(newconn,newconn.hash['otp'],self.connection_buttons[newconn.hash['sessionid']][1])
        if(self.debug): print "End submit"
##        if tkMessageBox.askyesno("Confirm", "Subimt this job?"):
##            print "job sumitted"
##        else:
##            print "you canceled"


    def refresh(self):
        if(self.debug): print "Refresh connection list"
        self.update_sessions(self.client_connection.list())
        if(self.debug): print "End Refresh connection list"

class crv_client_connection_GUI(crv_client.crv_client_connection):
    def __init__(self):
        crv_client.crv_client_connection.__init__(self)
        self.login = Login(action=self.login_setup)
        self.login.mainloop()
        
        if(self.debug): print "Check credential returned: " + str(checkCredential)
        if checkCredential:
            gui = ConnectionWindow(crv_client_connection=self)
            gui.update_sessions(self.list())
            gui.mainloop()
           
            


if __name__ == '__main__':
    try:
#        c.debug=True

        c=crv_client_connection_GUI()
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
        
        
    except Exception:
        print "ERROR OCCURRED HERE"
        raise
  