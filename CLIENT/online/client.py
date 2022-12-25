import socket
import hashlib
import time
from threading import Thread
try:
    from online.encryption import DH,AES
except:
    from encryption import DH,AES
from user_data.user_utils import user,tokens_storage,message_store,messages
class connection():
    def __init__(self,IP="127.0.0.1",PORT=12345,debug=True):
        self.DEBUG = debug
        #network things
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
        #responses
        self.GOAHEAD = "200"
        self.AUTHERROR = "401"
        self.WARNINGS = {"400":"client error, incorrect command","401":"authentication error, failure to authenticate","404":"resource not found","500":"Data not allowed","501":"invalid resource"}
        self.MATCHMAKINGERROR = "100"
        #other
        self.KEYTIMEOUT = 3600 #seconds, one hour
        self.AUTHCODE = None
        self.LARGESIZE = 20000
        self.UPLOADS = "uploads.txt"
        self.u = user()
        self.t = tokens_storage()
        self.m = messages()
        check = self.u.details()
        if not check:
            self.REFRESH_CODE = None
            self.USER_NAME = None
        else:
            self.REFRESH_CODE = check[1]
            self.USER_NAME = check[0]

    def print1(self,message):
        if self.DEBUG:
            print(message)
    def _send_message(self,sock,message,setup=False):
        message = str(message)
        self.print1(f"sent : {message}")
        if setup:
            sock.sendall(str(message).encode())
        else:
            a = AES(message)
            encrypted_message = a.encrypt(self.key)
            self.print1(self._size(encrypted_message))
            sock.sendall(encrypted_message.encode())
            
    def _recieve_message(self,size=1024,setup=False,goahead=False):
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
        error = str(error)
        error = error.strip()
        try:
            error = self.WARNINGS[error]
        except KeyError:
            print(error)
            error = "UNKNOWN ERROR"
        raise Exception(error)
    def _size(self,s)->int:
        return len(s.encode('utf-8'))
    def _initiate_connection(self,encrypted=True): #creates a connection to the server, 
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.SERVER_IP,self.PORT))
        data = self._recieve_message(setup=True,goahead=True)

        if encrypted:
            check = self.t.check_key_token()
            if check:
                token,key = check
                self._send_message(self.s,self.USE_KEY,setup=True)
                self._recieve_message(setup=True)
                self._send_message(self.s,self.USE_KEY,setup=True)
                data = self._recieve_message(setup=True,goahead=True)
                self._send_message(self.s,token,setup=True)
                accepted = self._recieve_message(setup=True)
                if accepted == self.AUTHERROR:
                    self.t.delete("key")
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
                    self.t.store_key_token(self.key,key_toke)
                    return
                except Exception as e:
                    self.print1(e)
            
        else:
            self._send_message(self.s,self.GOAHEAD,setup=True)
            self._recieve_message(setup=True)
    def get_auth_token(self):
        current_time = time.time()
        try:
            check_time,auth = self.t.check_auth_code()
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
            self.t.store_auth_code(self.AUTHCODE)
            self.s.close()
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            return True
        
    def create_account(self,username,password):
        hasher = hashlib.sha256()
        hasher.update(password.encode())
        password = hasher.hexdigest()
        self._initiate_connection()
        self._send_message(self.s,self.CREATEACCOUNT)
        data = self._recieve_message(goahead=True)
        correct = False
        while not correct:
            self._send_message(self.s,username)
            self._send_message(self.s,password)
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
    
    def upload(self,data_to_send,name,shared=False,recurse=False):#TODO add a filetype descriptor?
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
        self._recieve_message()
        a = AES(data_to_send)
        new_data = a.encrypt(self.key)
        size = self._size(new_data)
        size *= 1.2
        size = int(size)
        self._send_message(self.s,size)
        self._recieve_message()
        self._send_message(self.s,data_to_send)
        check = self._recieve_message(goahead=True)
        self._send_message(self.s,self.GOAHEAD)
        
        namer = self._recieve_message(size=self.LARGESIZE)
        file = open(self.UPLOADS,"a")
        entry = f"\n{name},{namer}"
        file.write(entry)
        file.close()
        return namer

    def ping(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.SERVER_IP,self.PORT))
            data = self._recieve_message(setup=True)
            self.s.close()
            return True
        except:
            return False
    def login(self,username,password,hashed=False):
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
        hasher = hashlib.sha256()
        hasher.update(string.encode())
        return(hasher.hexdigest())
    
    def update(self,filename,new):
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
        
    def delete(self,filename):
        auth = self.authenticated_start()
        self._initiate_connection()
        self._send_message(self.s,self.DELETEDATA)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,auth)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,filename)
        data = self._recieve_message(goahead=True)
        self.s.close()
        file = open(self.UPLOADS,"r")
        content = file.read()
        file.close()
        new = []
        content = content.split("\n")
        for line in content:
            if filename not in line:
                new.append(line)
        final = ""
        for line in new:
            final += line + "\n"
        file = open(self.UPLOADS,"w")
        file.write(final)
        file.close()
        return True
    def view(self,filename):
        auth = self.authenticated_start()
        self._initiate_connection()
        self._send_message(self.s,self.VIEWDATA)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,auth)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,filename)
        data = self._recieve_message(size=self.LARGESIZE)
        try:
            self.WARNINGS[data]
            self._error_handling(data)
            return
        except KeyError:
            None
        self.s.close()
        return data
    def share(self,filename,user_to_share):
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
        self._initiate_connection(encrypted=False)
        current_time = time.time()
        self._send_message(self.s,self.PING,setup=True)
        self._recieve_message(setup=True)
        new_time = time.time()
        pinger = new_time-current_time
        return pinger*1000

    def send_user_message(self,message,recipient):#TODO add some sort of size limit
        auth = self.authenticated_start()
        self._initiate_connection()
        self._send_message(self.s,self.SEND_USER_MESSAGE)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,auth)
        data = self._recieve_message(goahead=True)
        self._send_message(self.s,recipient)
        self._recieve_message(goahead=True)
        size = self._size(message)
        size *= 1.2
        self._send_message(self.s,size)
        self._recieve_message(goahead=True)
        self._send_message(self.s,message)
        self._recieve_message(goahead=True)
        return True

    def check_messages(self):#TODO (somewhere) add message storage lmao
        auth = self.authenticated_start()
        self._initiate_connection()
        self._send_message(self.s,self.CHECK_MESSAGES)
        self._recieve_message(goahead=True)
        self._send_message(self.s,auth)
        self._recieve_message(goahead=True)

        self._send_message(self.s,self.GOAHEAD)
        num_of_messages = int(self._recieve_message())
        
        message_list = []
        for x in range(num_of_messages):
            self._send_message(self.s,self.GOAHEAD)
            author = self._recieve_message()
            self._send_message(self.s,self.GOAHEAD)
            size = int(self._recieve_message())
            self._send_message(self.s,self.GOAHEAD)
            content = self._recieve_message(size=size)
            self._send_message(self.s,self.GOAHEAD)
            send_time = self._recieve_message()
            self._send_message(self.s,self.GOAHEAD)
            token = self._recieve_message(size=self.LARGESIZE)
            combined = message_store(author,content,send_time,token)
            message_list.append(combined)
        self._send_message(self.s,self.GOAHEAD)
        if num_of_messages == 0:
            return False
        self.m.store_messages(message_list)
        return message_list
if __name__ == "__main__":      
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
        name = c.upload("this do be a test 2699","testing234",shared=False)
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
