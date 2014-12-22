import os
import hashlib
import subprocess

def svn_version():
    #DISTPATH=os.path.join(os.path.dirname(os.path.abspath(__file__)),'dist','Releases')
    ROOTPATH=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DISTPATH=os.path.join(ROOTPATH,'build','dist','Releases')
    print "ROOTPATH="+ROOTPATH
    print "DISTPATH="+DISTPATH
    myprocess = subprocess.Popen (["svnversion",DISTPATH],stdout=subprocess.PIPE)
    (myout,myerr)=myprocess.communicate()

    return str(myout)

def baseurl():
    svninfo = ''
    ROOTPATH=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DISTPATH=os.path.join(ROOTPATH,'build','dist','Releases')
    myprocess = subprocess.Popen(["svn", "info", ROOTPATH],stdout=subprocess.PIPE)
    (myout,myerr)=myprocess.communicate()
    for line in myout.splitlines():
	if "URL: " in line:
		svninfo = line[5:]
		break
		
    print "SVN info URL: ", svninfo
    baseurl = svninfo + "/build/dist/Releases/"
    return baseurl


if __name__ == '__main__':
    sv = svn_version()
    try :
        svint=int(sv)
        print "svn version:" + str(svint)
       
    except :
        print "svn version not synced:" + sv
        exit()

    bu=baseurl()
    print "base url   :" + bu


