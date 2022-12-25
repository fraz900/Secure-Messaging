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
    
class messages():
    def __init__(self):
        PATH = "user_data/messages.db"
        self.conn = sqlite3.connect(PATH,check_same_thread=False)
        self.c = self.conn.cursor()
        command = """CREATE TABLE IF NOT EXISTS Messages(
                     id string PRIMARY KEY,
                     author string NOT NULL,
                     sent_time real,
                     contents string);"""
        self.c.execute(command)

    def store_message(self,message):
        if not self.get_message(message.id):
            self.c.execute(f"""INSERT INTO Messages (id,author,sent_time,contents)
                            VALUES ("{message.token}","{message.author}",{message.send_time},"{message.content}");""")
            self.conn.commit()
        else:
            return False

    def store_messages(self,messages):
        for message in messages:
            self.store_message(message)
            
    def get_messages(self,user):
        self.c.execute(f"""SELECT * FROM Messages WHERE author="{user}";""")
        rows = self.c.fetchall()
        messages = []
        for row in rows:
            messages.append(message_store(row[1],row[3],row[2],row[0]))
        return messages

    def get_message(self,token):
        self.c.execute(f"""SELECT * FROM Messages WHERE id="{token}";""")
        rows = self.c.fetchall()
        if len(rows) == 0:
            return False
        return rows[0]
    def get_users(self):
        self.c.execute("SELECT DISTINCT author FROM Messages")
        results = self.c.fetchall()
        return results

    def most_recent_message(self):
        self.c.execute("SELECT MAX(sent_time) FROM Messages")
        result = self.c.fetchall()
        return result[0][0]
    
    def delete_message(self,identifier):#TODO
        None

