import os
import hashlib
import subprocess

class platform_version:
    def __init__(self):
        self.ROOTPATH=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.DISTPATH=os.path.join(self.ROOTPATH,'build','dist','Releases')
        self.checkfile = os.path.join(self.ROOTPATH,"build","dist", "checksum.txt")
        self.configurationFile = os.path.join(self.ROOTPATH,"server", "versionRCM.cfg")


    def svn_version(self):
        myprocess = subprocess.Popen (["svnversion",self.DISTPATH],stdout=subprocess.PIPE)
        (myout,myerr)=myprocess.communicate()

        return str(myout)

    def baseurl(self):
        svninfo = ''
        myprocess = subprocess.Popen(["svn", "info", self.ROOTPATH],stdout=subprocess.PIPE)
        (myout,myerr)=myprocess.communicate()
        for line in myout.splitlines():
	    if "URL: " in line:
		svninfo = line[5:]
		break
		
#        print "SVN info URL: ", svninfo
        baseurl = svninfo + "/build/dist/Releases/"
        return baseurl

    def check_svn(self):
        sv=self.svn_version()
        try :
            self.svint=int(sv)
            
        except :
            print "svn version not synced:" + sv
            return False

        self.baseurl=self.baseurl()
        print "svn version:" + str(self.svint)+" base_url: "+self.baseurl
        return True


    def checksum(self,fname=''):
#        print "checksum-->" + fname + "<--"
        if not os.path.exists(fname): 
           fname = os.path.join(self.ROOTPATH, 'build','dist','Releases', fname)
        if os.path.exists(fname):
            fh = open(fname, 'rb')
            m = hashlib.md5()
            while True:
                data = fh.read(8192)
                if not data: break
                m.update(data)
            currentChecksum = m.hexdigest()
            return currentChecksum
        else: 
            print "ERROR file : ",fname," NOT FOUND"
            return None 

    def get_checksum_file(self):
        with open(self.checkfile, 'r') as inF:
            lines = inF.read().splitlines()
            inF.close()
        plat  = lines[0]
        check = lines[1]
        path  = lines[2]
#        print "get_checksum_file:",(plat,check,path)
        currcheck = self.checksum(path)
        if check == currcheck:
            return (plat,check,path)
        else:
            print "ERROR invalid check:",currcheck,check
            return None

    def update(self):
        res=self.get_checksum_file()
        if res :
            (myplatform,currentChecksum,rcmExe)  = res
        else:
            print "invalid check"
            return None

        if not self.check_svn(): 
            print "invalid svn"
            return None

        url =  self.baseurl + rcmExe + '?p=' + str(self.svint)
        with open(self.configurationFile, 'r') as inF:
            fileContent = inF.readlines()
            inF.close()
    
        checksumWritten = False
        for idx, line in enumerate(fileContent):    
            if myplatform in line:
                if(checksumWritten == False):
                    line = myplatform + " = " + currentChecksum + '\n'
                    fileContent[idx] = line
                    checksumWritten = True
                else:
                    line = myplatform + " = " + url + '\n'
                    fileContent[idx] = line
                    break
        if not checksumWritten:
            with open(self.configurationFile, 'w') as outF:
                for idx, line in enumerate(fileContent):    
                    if '[checksum]' in line:
                        fileContent.insert(idx+1, myplatform + " = " + currentChecksum + '\n')
                    if '[url]' in line:
                        fileContent.insert(idx+1, myplatform + " = " + url  + '\n')

        with open(self.configurationFile, 'w') as outF:
            for line in fileContent:
                outF.write(line)
            outF.close()
        print "updated version file: "+self.configurationFile



if __name__ == '__main__':
    pv = platform_version()
    sv = pv.update()



