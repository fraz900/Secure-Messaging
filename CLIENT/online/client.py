import socket
import hashlib
import time
from threading import Thread
from textwrap import wrap
from online.encryption import DH,AES,RSA
from user_data.user_utils import user,message_store

#Object used to represent and manage all
#networked interactions
class connection():
    #n.b. default server IP is for testing only
    def __init__(self,IP="127.0.0.1",PORT=12345,user_class=None,debug=False):
        #Initiates object by setting default values
        #(server information, communication codes, key values,
        #encapsulated objects etc)
        self.DEBUG = debug
        #network information
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.SERVER_IP = IP
        self.PORT = PORT
        #commands
        self.REFRESHAUTH_COMMAND = "rac"
        self.CREATEACCOUNT = "ca"
        self.UPLOADDATA = "ud"
        self.UPDATEDATA = "upd"
        self.DELETEDATA = "dd"
        self.VIEWDATA = "vd"
        self.SHARE = "sd"
        self.CHECKLOGIN = "cl"
        self.CHECKAUTH_COMMAND = "cac"
        self.GETOWNERSHIP = "go"
        self.GENERATEKEY = "gk"
        self.PING = "pi"
        self.SEND_USER_MESSAGE = "sm"
        self.USE_KEY = "us"
        self.CHECK_MESSAGES = "cm"
        self.CHECK_USER = "cu"
        self.DELETEMESSAGE = "dm"
        self.EDITMESSAGE= "em"
        self.ISSUE2FA = "it"
        self.RESETPASSWORD = "rp"
        self.UPDATEPUBLICKEY = "up"
        self.GETPUBLICKEY = "gp"
        #responses
        self.GOAHEAD = "200"
        self.AUTHERROR = "401"
        self.WARNINGS = {"400":"client error, incorrect command","401":"authentication error, failure to authenticate","404":"resource not found","500":"Data not allowed","501":"invalid resource"}
        #other
        self.KEYTIMEOUT = 3600 #seconds, one hour
        self.AUTHCODE = None
        self.LARGESIZE = 20000
        self.UPLOADS = "uploads.txt"
        #Initiating other objects
        if user_class == None:
            self.u = user()
        else:
            self.u = user_class
        check = self.u.details()
        if not check:
            self.REFRESH_CODE = None
            self.USER_NAME = None
        else:
            self.REFRESH_CODE = check[1]
            self.USER_NAME = check[0]

    def print1(self,message):
        #Function used to provide debug information
        if self.DEBUG:
            print(message)
            
    def _send_message(self,sock,message,setup=False):
        #Function used to send messages to the server
        message = str(message)
        self.print1(f"sent : {message}")
        if setup:
            sock.sendall(str(message).encode())
        else:
            a = AES(message)
            encrypted_message = a.encrypt(self.key)
            sock.sendall(encrypted_message.encode())
            
    def _recieve_message(self,size=1024,setup=False,goahead=False):
        #Used to recieve messages from the server
        if size < 1024:
            size = 1024
        data = self.s.recv(size)
        data = data.decode()
        if setup:
            self.print1(f"recieved : {data}")
            if goahead:
                if data.strip() != self.GOAHEAD:
                    self._error_handling(data)
                    return False
            return data.strip()
        else:
            a = AES(data)
            message = a.decrypt(self.key)
            self.print1(f"recieved : {message}")
            if goahead:
                if message.strip() != self.GOAHEAD:
                    self._error_handling(data)
            return message.strip()

    def _error_handling(self,error):
        #Provides the appropriate error for a given
        #error code
        error = str(error)
        error = error.strip()
        try:
            error = self.WARNINGS[error]
        except KeyError:
            print(error)
            error = "UNKNOWN ERROR"
        raise Exception(error)
    
    def _size(self,s)->int:
        #Returns the UTF-8 encoded size of a given string
        return len(s.encode('utf-8'))
    
    def _initiate_connection(self,encrypted=True):
        #creates a connection to the server, optionally
        #encrypted
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.SERVER_IP,self.PORT))
        data = self._recieve_message(setup=True,goahead=True)

        if encrypted:
            check = self.u.t.check_key_token()
            if check:
                token,key = check
                self._send_message(self.s,self.USE_KEY,setup=True)
                self._recieve_message(setup=True)
                self._send_message(self.s,self.USE_KEY,setup=True)
                data = self._recieve_message(setup=True,goahead=True)
                self._send_message(self.s,token,setup=True)
                accepted = self._recieve_message(setup=True)
                if accepted == self.AUTHERROR:
                    self.u.t.delete("key")
                    self._initiate_connection()
                    return 
                elif accepted != self.GOAHEAD:
                    self._error_handling(accepted)
                    return False
                self.key = key
                return True
            else:
                self._send_message(self.s,self.GENERATEKEY,setup=True)
                self._recieve_message(setup=True)
                diffie = DH()
                dhKey = diffie.generate_key()
                modulus = diffie.generate_prime()
                base = diffie.generate_base(modulus)
                ag = diffie.equation(base,dhKey,modulus)
                self._send_message(self.s,modulus,setup=True)
                self._recieve_message(setup=True)
                self._send_message(self.s,base,setup=True)
                self._recieve_message(setup=True)
                self._send_message(self.s,ag,setup=True)
                bg = int(self._recieve_message(setup=True))
                final = diffie.equation(bg,dhKey,modulus)
                a = AES("")
                self.key = a.produce_key(final)
                self._send_message(self.s,self.GOAHEAD)
                try:
                    key_toke = self._recieve_message(size=self.LARGESIZE)
                    self.u.t.store_key_token(self.key,key_toke)
                    return
                except Exception as e:
                    self.print1(e)
            
        else:
            self._send_message(self.s,self.GOAHEAD,setup=True)
            self._recieve_message(setup=True)
            
    def get_auth_token(self):
        #Ensures the client has a valid cached auth code
        current_time = time.time()
        try:
            check_time,auth = self.u.t.check_auth_code()
            if (current_time-check_time) < self.KEYTIMEOUT:
                self.AUTHCODE = auth
                self._initiate_connection()
                self._send_message(self.s,self.CHECKAUTH_COMMAND)
                data = self._recieve_message()
                data = data.strip(goahead=True)
                self._send_message(self.s,self.AUTHCODE)
                data = self._recieve_message()
                self.s.close()
                if data.strip() == self.GOAHEAD:
                    return True
        except:
            None
                    
        commands = [self.REFRESHAUTH_COMMAND,self.REFRESH_CODE]
        self._initiate_connection()
        self._send_message(self.s,self.REFRESHAUTH_COMMAND)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,self.USER_NAME)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,self.REFRESH_CODE)
        data = self._recieve_message(size=self.LARGESIZE)
        data = data.strip()
        try:
            test = self.WARNINGS[data]
            self._error_handling(data)
        except KeyError:
            self.AUTHCODE = data
            self.u.t.store_auth_code(self.AUTHCODE)
            self.s.close()
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            return True
        
    def create_account(self,username,password,email,pub_key):
        #Registers a new account to be stored on the server
        hasher = hashlib.sha256()
        hasher.update(password.encode())
        password = hasher.hexdigest()
        self._initiate_connection()
        self._send_message(self.s,self.CREATEACCOUNT)
        data = self._recieve_message(goahead=True)
        correct = False
        while not correct:
            self._send_message(self.s,username)
            self._recieve_message(goahead=True)
            self._send_message(self.s,password)
            self._recieve_message(goahead=True)
            self._send_message(self.s,email)
            self._recieve_message(goahead=True)
            self._send_message(self.s,pub_key)
            user_test = self._recieve_message()
            password_test = self._recieve_message(size=self.LARGESIZE)
            if user_test == username and password_test == password:
                correct = True

        self._send_message(self.s,self.GOAHEAD)
        data = self._recieve_message()
        if data == self.GOAHEAD:
            self.REFRESH_CODE = password
            self.USER_NAME = username
            return True
        else:
            self._error_handling(data)

    def authenticated_start(self):
        #Used to initiate a connection where the client
        #needs to be authenticated 
        if self.AUTHCODE == None:
            self.get_auth_token()
        auth = self.AUTHCODE

        self._initiate_connection()
        self._send_message(self.s,self.CHECKAUTH_COMMAND)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,auth)
        data = self._recieve_message()
        self.s.close()
        if data.strip() == self.GOAHEAD:
            return auth
        else:
            self.get_auth_token()
            auth = self.AUTHCODE
            return auth
    
    def upload(self,data_to_send,shared=False,recurse=False):
        #Used to upload a file to the server
        shared_state = "singular"
        if shared:
            shared_state = "shared"
        if self.AUTHCODE == None:
            self.get_auth_token()

        auth = self.AUTHCODE
        
        self._initiate_connection()
        self._send_message(self.s,self.UPLOADDATA)
        data = self._recieve_message()
        if data != self.GOAHEAD:
            self._error_handling(data)
            return False

        self._send_message(self.s,auth)
        confirm = self._recieve_message()
        if confirm != self.GOAHEAD:
            if recurse:
                self._error_handling(confirm)
                return False
            else:
                self.s.close()
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.AUTHCODE = None
                self.upload(data,name,recurse=True)
        self._send_message(self.s,shared_state)
        self._recieve_message(goahead=True)
        self._send_message(self.s,self._data_hash(data_to_send))
        self._recieve_message(goahead=True)
        size = self._size(data_to_send)
        size *= 50
        self._send_message(self.s,size)
        self._recieve_message()
        packets = wrap(data_to_send,2048)
        for packet in packets:
            self._send_message(self.s,packet)
            check = self._recieve_message(goahead=True)
        self._send_message(self.s,self.GOAHEAD)
        
        namer = self._recieve_message(size=self.LARGESIZE)
        return namer

    def ping(self):
        #Used to ping the server (essentially checking it's online)
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.SERVER_IP,self.PORT))
            data = self._recieve_message(setup=True)
            self.s.close()
            return True
        except:
            return False
    def login(self,username,password,hashed=False):
        #Used to check if user provided login details are valid
        if not hashed:
            password = self._hash(password)
        self._initiate_connection()
        self._send_message(self.s,self.CHECKLOGIN)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,username)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,password)
        data = self._recieve_message(goahead=True)
        self.USER_NAME = username
        self.REFRESH_CODE = password
        return True

    def _hash(self,string):
        #Returns a sha256 hash of a given string
        hasher = hashlib.sha256()
        hasher.update(string.encode())
        return(hasher.hexdigest())
    
    def update(self,filename,new):
        #Used to update the details of an uploaded file
        auth = self.authenticated_start()

        self._initiate_connection()
        self._send_message(self.s,self.UPDATEDATA)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,auth)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,filename)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,new)
        data = self._recieve_message(goahead=True)
        self.s.close()
        return True
        
    def delete(self,file_token):
        #Used to delete an uploaded file
        auth = self.authenticated_start()
        self._initiate_connection()
        self._send_message(self.s,self.DELETEDATA)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,auth)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,file_token)
        data = self._recieve_message(goahead=True)
        self.s.close()
        return True
    
    def view(self,filename):
        #Used to download an uploaded file
        auth = self.authenticated_start()
        self._initiate_connection()
        self._send_message(self.s,self.VIEWDATA)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,auth)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,filename)
        self._recieve_message(goahead=True)
        self._send_message(self.s,self.GOAHEAD)
        file_size = int(round(float(self._recieve_message())))
        self._send_message(self.s,self.GOAHEAD)
        final = ""
        while True:
            data = self._recieve_message(size=500000)
            if data == self.GOAHEAD:
                break
            self._send_message(self.s,self.GOAHEAD)
            final += data
        self.s.close()
        return final
    def share(self,filename,user_to_share):
        #Used to provide another user account access to an uploaded file
        auth = self.authenticated_start()
        self._initiate_connection()
        self._send_message(self.s,self.SHARE)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,auth)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,user_to_share)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,filename)
        data = self._recieve_message(goahead=True)
        return True

    def get_ownership(self,filename):
        #Returns the owner of a file that has been shared with the user
        auth = self.authenticated_start()
        self._initiate_connection()
        self._send_message(self.s,self.GETOWNERSHIP)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,auth)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,filename)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,self.GOAHEAD)
        size = int(self._recieve_message())
        self._send_message(self.s,self.GOAHEAD)
        content = self._recieve_message(size=size)
        return content

    def ping_time(self):
        #Returns the time (in ms) it takes to recieve a response
        #from the server
        self._initiate_connection(encrypted=False)
        current_time = time.time()
        self._send_message(self.s,self.PING,setup=True)
        self._recieve_message(setup=True)
        new_time = time.time()
        pinger = new_time-current_time
        return pinger*1000

    def send_user_message(self,message,recipient,e2e=False):
        #Used to send a message from this user to another user
        #Optionally end to end encrypted
        if e2e:
            key = self.get_pubkey(recipient)
            message = "<e>" + message
            length,sender = RSA().encryptor(message,key)
            sender = "<e2e>"+str(length)+","+str(sender)
        else:
            sender = message
        auth = self.authenticated_start()
        self._initiate_connection()
        self._send_message(self.s,self.SEND_USER_MESSAGE)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,auth)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,recipient)
        self._recieve_message(goahead=True)
        a = AES(sender)
        new_data = a.encrypt(self.key)
        size = self._size(new_data)
        size *= 1.2
        self._send_message(self.s,size)
        self._recieve_message(goahead=True)
        self._send_message(self.s,sender)
        token = self._recieve_message(size=self.LARGESIZE)
        current_time = time.time()
        info = message_store(self.USER_NAME,recipient,message,current_time,token)
        self.u.m.store_message(info)
        return True

    def update_pubkey(self,new_pubkey):
        #Used to inform the server that the client is using a
        #new RSA public key
        auth = self.authenticated_start()
        self._initiate_connection()
        self._send_message(self.s,self.UPDATEPUBLICKEY)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,auth)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,new_pubkey)
        self._recieve_message(goahead=True)
        return True

    def get_pubkey(self,username):
        #Used to retrieve the server stored public key
        #of a given user
        self._initiate_connection()
        self._send_message(self.s,self.GETPUBLICKEY)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,username)
        answer = self._recieve_message(size=self.LARGESIZE)
        if answer in self.WARNINGS:
            self._error_handling(answer)
        else:
            return answer

        
    def check_messages(self):
        #Used to retrieve any messages sent from or recieved by the user
        #since their last stored message
        #(i.e. makes sure the messages database is up to date)
        last_message = self.u.m.most_recent_message()
        
        auth = self.authenticated_start()
        self._initiate_connection()
        self._send_message(self.s,self.CHECK_MESSAGES)
        self._recieve_message(goahead=True)
        self._send_message(self.s,auth)
        self._recieve_message(goahead=True)

        self._send_message(self.s,self.GOAHEAD)
        self._recieve_message(goahead=True)
        self._send_message(self.s,last_message)
        num_of_messages = int(self._recieve_message())
        if num_of_messages == 0:
            return False
        
        message_list = []
        for x in range(num_of_messages):
            self._send_message(self.s,self.GOAHEAD)
            author = self._recieve_message()
            self._send_message(self.s,self.GOAHEAD)
            size = int(round(float(self._recieve_message())))
            self._send_message(self.s,self.GOAHEAD)
            content = self._recieve_message(size=size)
            if content.startswith("<e2e>"):
                content = content.replace("<e2e>","")
                info = content.split(",")
                content = RSA().decryptor(info[1],info[0],self.u.pubkey,self.u.privkey)
                if not content.startswith("<e>"):
                    content = "<F><End to End encrypted message that could not be decrypted>"
            self._send_message(self.s,self.GOAHEAD)
            send_time = self._recieve_message()
            self._send_message(self.s,self.GOAHEAD)
            token = self._recieve_message(size=self.LARGESIZE)
            self._send_message(self.s,self.GOAHEAD)
            recipient = self._recieve_message()
            combined = message_store(author,recipient,content,send_time,token)
            message_list.append(combined)
        self._send_message(self.s,self.GOAHEAD)

        self.u.m.store_messages(message_list)
        return message_list

    def delete_message(self,token):
        #Deletes a message sent by the user
        #stored on the server
        auth = self.authenticated_start()
        self._initiate_connection()
        self._send_message(self.s,self.DELETEMESSAGE)
        self._recieve_message(goahead=True)
        self._send_message(self.s,auth)
        self._recieve_message(goahead=True)

        self._send_message(self.s,token)
        self._recieve_message(goahead=True)

    def edit_message(self,token,new_message):
        #changes the contents of a message sent by the user stored on the server
        auth = self.authenticated_start()
        self._initiate_connection()
        self._send_message(self.s,self.EDITMESSAGE)
        self._recieve_message(goahead=True)
        self._send_message(self.s,auth)
        self._recieve_message(goahead=True)

        self._send_message(self.s,token)
        self._recieve_message(goahead=True)
        a = AES(new_message)
        new_data = a.encrypt(self.key)
        size = self._size(new_data)
        size *= 1.2
        self._send_message(self.s,size)
        self._recieve_message(goahead=True)
        self._send_message(self.s,new_message)
        self._recieve_message(goahead=True)
        self.s.close()
        return True
        
    def check_user(self,username):
        #Checks if a given username is associated with an existing user account
        self._initiate_connection()
        self._send_message(self.s,self.CHECK_USER)
        self._recieve_message(goahead=True)
        self._send_message(self.s,username)
        check = self._recieve_message()
        if check == self.GOAHEAD:
            return True
        return False

    def issue_2fa_code(self,username):
        #Request that the server emails out a 2 factor authentication code
        self._initiate_connection()
        self._send_message(self.s,self.ISSUE2FA)
        self._recieve_message(goahead=True)
        self._send_message(self.s,username)
        self._recieve_message(goahead=True)

        self._recieve_message(goahead=True)
        return True

    def reset_password(self,username,new_password,code):
        #Requests that the server updates the user account password
        #authenticated with a 2fa code
        hasher = hashlib.sha256()
        hasher.update(new_password.encode())
        new_password = hasher.hexdigest()
        
        self._initiate_connection()
        self._send_message(self.s,self.RESETPASSWORD)
        self._recieve_message(goahead=True)
        self._send_message(self.s,username)
        self._recieve_message(goahead=True)

        self._send_message(self.s,code)
        self._recieve_message(goahead=True)
        self._send_message(self.s,new_password)
        self._recieve_message(goahead=True)
        return True
    
    def file_to_bin(self,filename):
        #Returns the binary representation of a given file
        bytetable = [("00000000"+bin(x)[2:])[-8:] for x in range(256)]
        binrep = "".join(bytetable[x] for x in open(filename, "rb").read())
        return binrep
    
    def bin_to_bytes(self,binrep):
        #turns a string based binary representation
        #into a python bytes object representation
        v = int(binrep, 2)
        b = bytearray()
        while v:
            b.append(v & 0xff)
            v >>= 8
        return bytes(b[::-1])

    def _file_hash(self,path):
        #returns the sha256 hash of a given file
        hasher = hashlib.sha256()
        file = open(path,"rb")
        while True:
            data = f.read(65536)
            if not data:
                break
            hasher.update(data)
        file.close()
        return hasher.hexdigest()

    def _data_hash(self,data):
        #Returns the sha256 hash of any given data
        hasher = hashlib.sha256()
        hasher.update(data.encode())
        return hasher.hexdigest()
if __name__ == "__main__":
    #For testing purposes only
    c = connection()
    file_test = True
    match_test = False
    account_test = False
    ping_test = False
    if ping_test:
        print(c.ping())
    if file_test:
        print(c.ping())
        time.sleep(1)
        name = c.upload("this is a test","testing",shared=False)
        time.sleep(1)
        print(c.view(name))
        time.sleep(1)
        c.share(name,"test")
        time.sleep(1)
        print(c.get_ownership(name))
        time.sleep(1)
        c.delete(name)
    if account_test:
        c.create_account("account","password")
        c.get_auth_token()
