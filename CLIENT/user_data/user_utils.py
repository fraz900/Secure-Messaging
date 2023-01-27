import sqlite3
import os
import time
from dataclasses import dataclass
import xml.etree.cElementTree as ET
import pathlib
from online.encryption import RSA

class user():#stores user info and settings 
    def __init__(self):
        self.t = tokens_storage()
        self.m = messages()
        self.s = settings()
        self.RSA = RSA()
        try:
            file = open("user_data/user_account.txt","r")
            data = file.read()
            lines = data.split("\n")
            self.username = lines[0]
            self.pass_hash = lines[1]
            self.exists = True
            keys = lines[2]
            keys = keys.split(",")
            self.pubkey = keys[0]
            self.privkey = keys[1]
        except:
            self.exists = False
    def __repr__(self):
        if self.exists:
            return(self.username)
        else:
            return "does not exist"
    def create(self,uname,pass_hash,privkey,pubkey):
        entry = f"{uname}\n{pass_hash}\n{privkey},{pubkey}"
        file = open("user_data/user_account.txt","w")
        file.write(entry)
        file.close()
        self.exists = True
        self.username = uname
        self.privkey = privkey
        self.pubkey = pubkey
        messages().reset()
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

    def delete_all(self):
        self.delete("account")
        self.s.delete()
        self.m.reset()

    def export(self):#TODO add RSA keys
        tree = ET.parse(self.s.path)
        root = tree.getroot()
        profile_details = ET.SubElement(root,"user_details")
        ET.SubElement(profile_details,"username").text = self.username
        ET.SubElement(profile_details,"password").text = self.pass_hash
        tree.write(os.path.join(self.s.download_folder,"user_account_profile.xml"),encoding='UTF-8',xml_declaration=True)
        return True
        
    def import_settings(self,path):
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            user_details = root.find("user_details")
            uname = user_details.find("username").text
            pword = user_details.find("password").text
            root.remove(user_details)
            tree.write(self.s.path)
            self.s = settings()
            self.create(uname,pword)
        except Exception as e:
            raise Exception("invalid file")
            

            
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
    recipient: str
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
                     recipient string NOT NULL,
                     sent_time real,
                     contents string);"""
        self.c.execute(command)

    def reset(self):
        self.c.execute("DROP TABLE Messages")
        self.conn.commit()
        self.__init__()

    def store_message(self,message):
        if not self.get_message(message.token):
            self.c.execute(f"""INSERT INTO Messages (id,author,recipient,sent_time,contents)
                            VALUES ("{message.token}","{message.author}","{message.recipient}",{message.send_time},"{message.content}");""")
            self.conn.commit()
            return True
        else:
            return False

    def store_messages(self,messages):
        for message in messages:
            self.store_message(message)

    def get_message_from_recipient(self,user):#returns all messages to a given user
        self.c.execute(f"""SELECT * FROM Messages WHERE recipient="{user}" AND recipient != author;""")
        rows = self.c.fetchall()
        messages = []
        for row in rows:
            messages.append(message_store(row[1],row[2],row[4],row[3],row[0]))
        return messages
          
    def get_messages(self,user):#returns all messages from a given user
        self.c.execute(f"""SELECT * FROM Messages WHERE author="{user}" AND recipient != author;""")
        rows = self.c.fetchall()
        messages = []
        for row in rows:
            messages.append(message_store(row[1],row[2],row[4],row[3],row[0]))
        return messages

    def get_message(self,token):#returns a singular message with the token passed
        self.c.execute(f"""SELECT * FROM Messages WHERE id="{token}";""")
        rows = self.c.fetchall()
        if len(rows) == 0:
            return False
        return rows[0]
    def get_users(self):
        self.c.execute("SELECT DISTINCT author FROM Messages")
        results = self.c.fetchall()
        self.c.execute("SELECT DISTINCT recipient FROM Messages")
        results1 = self.c.fetchall()
        return list(dict.fromkeys((results+results1)))

    def most_recent_message(self):
        self.c.execute("SELECT MAX(sent_time) FROM Messages")
        result = self.c.fetchall()
        return result[0][0]
    
    def delete_message(self,identifier):
        self.c.execute(f"""DELETE FROM Messages WHERE id="{identifier}";""")
        self.conn.commit()
        return True

    def edit_message(self,token,new_message):
        self.c.execute(f"""UPDATE Messages SET contents = "{new_message}" WHERE id="{token}";""")
        self.conn.commit()
        return True
    
class settings():
    def __init__(self,path="user_data/settings.xml"):
        self.path = path
        try:
            tree = ET.parse(self.path)
            root = tree.getroot()
            settings_tree = root.find("settings")
            self.download_folder = settings_tree.find("download_folder").text
            colour_tree = settings_tree.find("colours")
            self.text_colour = colour_tree.find("text_colour").text
            self.background_colour = colour_tree.find("background_colour").text
        except:
            self.download_folder = str(pathlib.Path.home() / "Downloads")
            self.text_colour = "black"
            self.background_colour = "white"
            root = ET.Element("root")
            settings_sub = ET.SubElement(root,"settings")
            colours = ET.SubElement(settings_sub,"colours")
            ET.SubElement(colours,"text_colour").text = self.text_colour
            ET.SubElement(colours,"background_colour").text = self.background_colour
            ET.SubElement(settings_sub,"download_folder").text = self.download_folder
            tree = ET.ElementTree(root)
            tree.write(self.path,encoding='UTF-8',xml_declaration=True)
        self.tree = tree
        
    def update(self,setting,new):
        for thing in self.tree.findall(f".//{setting}"):
            thing.text = new
        self.tree.write(self.path,encoding='UTF-8',xml_declaration=True)
        self.__init__(self.path)
        
    def delete(self):
        os.remove(self.path)

    
if __name__== "__main__":
    None
