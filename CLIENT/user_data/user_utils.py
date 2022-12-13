##########
# SCPOPE
# -User info access (txt)
# -User message access (sql)
# -User settings (XML,JSON???)
# -Generics (e.g. pfp etc)
###########

import sqlite3
import os
import time
from dataclasses import dataclass

class user():#stores user info and settings 
    def __init__(self):
        try:
            file = open("user_data/user_account.txt","r")
            data = file.read()
            lines = data.split("\n")
            self.username = lines[0]
            self.pass_hash = lines[1]
            self.exists = True
        except:
            self.exists = False
    def __repr__(self):
        if self.exists:
            return(self.username)
        else:
            return "does not exist"
    def create(self,uname,pass_hash):
        entry = f"{uname}\n{pass_hash}"
        file = open("user_data/user_account.txt","w")
        file.write(entry)
        file.close()
        self.exists = True
        self.username = uname
        self.pass_hash = pass_hash
        return True
    
    def details(self):
        if self.exists:
            return self.username,self.pass_hash
        else:
            return False
        
    def userExists(self):
        return self.exists
    
    def delete(self,file):
        matcher = {"account":"user_data/user_account.txt"}
        os.remove(matcher[file])

class tokens_storage():
    def __init__(self):
        None
    def check_key_token(self):
        try:
            file = open("user_data/key_token.txt","r")
            content = file.read()
            file.close()
            content = content.split("\n")
            identifier = content[0]
            key = content[1]
            print("utils",key)
            return identifier,key
        except:
            return False
    def store_key_token(self,key,identifier):
        file = open("user_data/key_token.txt","w")
        entry = f"{identifier}\n{key}"
        file.write(entry)
        file.close()
        return True

    def store_auth_code(self,code):
        current_time = time.time()
        file = open("user_data/auth_code.txt","w")
        entry = f"{current_time},{code}"
        file.write(entry)
        file.close()
        return True
        
    def check_auth_code(self):
        file = open("user_data/auth_code.txt","r")
        content = file.read()
        file.close()
        content = content.split(",")
        check_time = float(content[0])
        code = content[1]
        return check_time,code

    def delete(self,file):
        matcher = {"key":"user_data/key_token.txt"}
        os.remove(matcher[file])


@dataclass()
class message_store:
    author: str
    content: str
    send_time: float
    token: str
    
#database stuff (make object pls)
def store_message(message):
    None

def create_message_database():
    None


