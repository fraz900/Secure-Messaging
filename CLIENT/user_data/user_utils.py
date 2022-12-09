##########
# SCPOPE
# -User info access (txt)
# -User message access (sql)
# -User settings (XML,JSON???)
# -Generics (e.g. pfp etc)
###########

import sqlite3
import os

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
    def userExists(self):
        return self.exists
    def delete(self):
        os.remove("user_data/user_account.txt")


#database stuff (make object pls)
def store_message(message):
    None

def create_message_database():
    None
    
