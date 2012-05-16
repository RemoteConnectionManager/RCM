#!/bin/env python

import crv_client
import crv

from Tkinter import *
import tkMessageBox

bigfont = ("Helvetica",10)
boldfont = ("Helvetica",12,"bold")

class Login(Frame):
    def __init__(self, master=None,action=None,proxynode='login2.plx.cineca.it'):

        Frame.__init__(self, master)
        self.pack( padx=10, pady=10 )
        self.master.title("Login:")
        self.action=action
        #self.master.geometry("+200+200")
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
        self.action(self.proxynode.get(),self.user.get(), self.password.get())
        self.destroy()
        self.quit()
        print('Logged in')
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

        Frame.__init__(self, master)
        self.client_connection=crv_client_connection
        self.pack( padx=10, pady=10 )
        self.master.title("Connections")
        self.master.geometry("+200+200")

        self.wL1 = Label(self, text="example label" )#, width=65, bg="gray", justify="left")
        self.wL1.grid( row=0,column=0, sticky="w")
        self.wL1["font"]=boldfont

        #f3 = Frame(self)
        #f3.grid( row=6,column=0, sticky="we")
        #w = Button(f3, text="submit", command=self.submit)
        #w.pack(side="left")


        #f3.grid( row=6,column=0, sticky="we")
        button = Button(self, text="close", command=self.submit)
        button.grid( row=10,column=0 )

        self.f1 = Frame(self, width=500, height=100)
        self.f1.grid( row=1,column=0) 
        f1 = self.f1
##        for i,t in enumerate([" id "," name "," np "," nf "," status "," progress "]):
##            w = Label(f1, text=t, relief="raised")
##            w.grid( row=1,column=i, sticky="we")
##            f1.columnconfigure ( i, minsize=80 )
##
##
##        elemento = {}
##        elemento["id"] = "id0"
##        elemento["name"] = "name0"
##        
##        for line, el in  enumerate( [elemento, elemento, elemento] ):
##            for i,t in enumerate([" id "," name "," np "," nf "," status "," progress "]):
##                lab1 = Label(f1, text=el["id"] )
##                lab1.grid( row=line+2, column=0 )
##                lab2 = Label(f1, text=el["name"] )
##                lab2.grid( row=line+2, column=1 )
##                def cmd(self=self, LINE=line):
##                    print "killing jog", LINE
##                b1 = Button( f1, text="kill this", command=cmd )
##                b1.grid( row=line+2, column=2 )


    def update_sessions(self,ss):
        self.sessions=ss
        f1 = self.f1
        c=crv.crv_session()
        for i,t in enumerate(sorted(c.hash.keys())):
            w = Label(f1, text=t, relief="raised")
            w.grid( row=0,column=i+2, sticky="we")
            f1.columnconfigure ( i, minsize=80 )


        
        for line, el in  enumerate( self.sessions.array ):
            if(self.client_connection):
            
                def cmd(self=self, sessionid=el.hash['sessionid']):
                    print "killing session", sessionid
                    self.client_connection.kill(sessionid)
                bk = Button( f1, text="kill", command=cmd )
                bk.grid( row=line+1, column=1 )
                
                def cmd(self=self, session=el):
                    print "connecting to session", session.hash['sessionid']
                    self.client_connection.vncsession(session)
                bk = Button( f1, text="connect", command=cmd )
                bk.grid( row=line+1, column=0 )
                
            for i,t in enumerate(sorted(c.hash.keys())):
                lab = Label(f1, text=el.hash[t] )
                lab.grid( row=line+1, column=i+2 )
        
        

    def submit(self):
        if tkMessageBox.askyesno("Confirm", "Subimt this job?"):
            print "job sumitted"
        else:
            print "you canceled"




class crv_client_connection_GUI(crv_client.crv_client_connection):
    def __init__(self):
        crv_client.crv_client_connection.__init__(self)
        self.login = Login(action=self.login_setup)
        self.login.mainloop()
        gui = ConnectionWindow(crv_client_connection=self)
        gui.update_sessions(self.list())
        gui.mainloop()


if __name__ == '__main__':
    try:

        c=crv_client_connection_GUI()
	c.debug=True
        gui = ConnectionWindow()
        gui.mainloop()
        
#        c.debug=True
        res=c.list()
        res.write(2)
        newc=c.newconn()
        newsession = newc.hash['sessionid']
        print "created session -->",newsession,"<- display->",newc.hash['display'],"<-- node-->",newc.hash['node']
        c.vncsession(newc)
        res=c.list()
        res.write(2)
        c.kill(newsession)
        res=c.list()
        res.write(2)
        
        
    except Exception:
        print "ERROR OCCURRED HERE"
        raise
  