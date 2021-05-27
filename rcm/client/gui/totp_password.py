import time
import pyotp
import keyring
import binascii

class OtpGenerator:
    def __init__(self, base32secret=''):
        self.generator = None
        if base32secret:
            try:
                self.generator = pyotp.TOTP(base32secret)
                print("Instantiated TOTP")
                self.old_otp = self.generator.now()
            except binascii.Error:
                self.generator = None
                print("Invalid TOTP secret-->" + base32secret + "<--")


    def get_generator_function(self):
        if self.generator:
            def new_otp(prompt=''):
                otp = self.generator.now()
                while otp == self.old_otp:
                    print("OTP code unchanged: ", otp)
                    time.sleep(5)
                    otp = self.generator.now()
                self.old_otp = otp
                return (otp,True)
            return new_otp
        else:
            return None

class SingleOtpGeneratorFactory:
    _singleton = None

    def __new__(cls):
        if not cls._singleton:
            print("Object is created and the variables are instantiated.")
            cls._singleton = super(SingleOtpGeneratorFactory, cls).__new__(cls)
            cls.otp_generators = {}
        else:
            print("Sorry, byt object is already made.")
        return cls._singleton

    def get_generator_function(self,host='',user=''):
        if (host,user) in self.otp_generators:
            return self.otp_generators[(host,user)].get_generator_function()
        else:
            base32secret = search_secret(hostname=host, username=user, type='otp')
            if base32secret:
                generator = OtpGenerator(base32secret)
                self.otp_generators[(host,user)] = generator
                return generator.get_generator_function()
            else:
                return None

def cluster(hostname):
     return '.'.join(hostname.split('.')[-3:])


def domain(hostname):
    return '.'.join(hostname.split('.')[-2:])

def search_secret(hostname='', username='', type='otp'):
    for i in [-4,-3,-2]:
        service_name =  type + '@' + '.'.join(hostname.split('.')[i:])
        secret = keyring.get_password(service_name,username)
        if secret:
            return secret

def store_secret(hostname='', username='', secret='', type='otp'):
    keyring.set_password(type + '@' + hostname , username, secret)



def test_keyring():
    ### under windows it seems to use the credential manager:  seach for credential manager in
    ### Control Panel --> User Accounts --> Credential Manager
    ### Under Mint:
    ### Menu --> Accessories--> Passwords and Keys
    
    active_keyring = keyring.get_keyring()
#linux    print("keyring: " + active_keyring.name + " Viable: " + str(active_keyring.viable) + " appid: " + str(active_keyring.appid))
    print("keyring: " + active_keyring.name + " Viable: " + str(active_keyring.viable) )

    print(dir(active_keyring))
#linux    pref_coll = active_keyring.get_preferred_collection()
#linux    print(dir(pref_coll))
#linux    print("Preferred collection: " +
#linux          " Path: " + pref_coll.collection_path +
#linux          " Label: " +  pref_coll.get_label() +
#linux          " Locked: " + str(pref_coll.is_locked()) +
#linux          " session: " + str(pref_coll.session) +
#linux          " connection: " + str(pref_coll.connection)
#linux          )
#linux
#    for i in pref_coll.search_items({'application': 'Python keyring library'}):
#        print("Deleting Item label: " + i.get_label() + " Attrib: " + str(i.get_attributes()))
#        i.delete()

#linux    pref_coll.create_item('mylabel',{'application': 'Python keyring library', 'service': 'system', 'username': 'username','type':'otp'},'pluto')
#    store_secret('cineca.it','lcalori0','paperopoli__otp')
#    store_secret('m100.cineca.it','lcalori0','QUACKSTREET101')
#    store_secret('m100.cineca.it','lcalori0','quackstreet__pass',type='password')


    for host in ['rcm.galileo.cineca.it','rcm.m100.cineca.it','login03-ext.galileo.cineca.it']:
        for user in ['lcalori0', 'dummy'] :
            for type in ['otp', 'password']:
                secret = search_secret(host,user,type)
                if secret : print('secret for ' + type + ':' + user + '@' + host + " -->" + secret + "<--")
    #pref_coll.lock()
#linux    print("Preferred collection: " +
#linux          " Path: " + pref_coll.collection_path +
#linux          " Label: " +  pref_coll.get_label() +
#linux          " Locked: " + str(pref_coll.is_locked()) +
#linux          " session: " + str(pref_coll.session) +
#linux          " connection: " + str(pref_coll.connection)
#linux          )
#linux    for i in pref_coll.search_items({'application': 'Python keyring library'}):
#linux        print("Item label: " + i.get_label() + " Attrib: " + str(i.get_attributes()))

    print ("==========================================================")
    opt_function = SingleOtpGeneratorFactory().get_generator_function('login3-ext.m100.cineca.it','lcalori0')
    if opt_function:
        for x in range(10):
            print("OPT: " + opt_function()[0])
            time.sleep(1)

if __name__ == "__main__":

  test_keyring()
