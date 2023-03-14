import sqlite3
import os
import time
from dataclasses import dataclass
import xml.etree.cElementTree as ET
import pathlib
from online.encryption import RSA
#Main class to be imported into other modules
#Stores user account information and encaspulates
#other information objects
class user():
    def __init__(self):
        #Initiates object by creating encapsulated objects
        #and retrieving stored information
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
            self.pubkey = keys[1]
            self.privkey = keys[0]
        except:
            self.exists = False
    def __repr__(self):
        if self.exists:
            return(self.username)
        else:
            return "does not exist"
    def create(self,uname,pass_hash,privkey,pubkey):
        #Used to store information about a new user account
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
        #returns basic user account information
        if self.exists:
            return self.username,self.pass_hash
        else:
            return False
        
    def userExists(self):
        #Used to check if a user account exists
        return self.exists
    
    def delete(self,file):
        #Deletes user account information
        matcher = {"account":"user_data/user_account.txt"}
        os.remove(matcher[file])

    def delete_all(self):
        #Deletes all (non-system) user information
        self.delete("account")
        self.s.delete()
        self.m.reset()

    def export(self):
        #Used to create an XML file that can be used
        #to import an account profile to another device
        tree = ET.parse(self.s.path)
        root = tree.getroot()
        profile_details = ET.SubElement(root,"user_details")
        ET.SubElement(profile_details,"username").text = self.username
        ET.SubElement(profile_details,"password").text = self.pass_hash
        ET.SubElement(profile_details,"pub_key").text = self.pubkey
        ET.SubElement(profile_details,"priv_key").text = self.privkey
        tree.write(os.path.join(self.s.download_folder,"user_account_profile.xml"),encoding='UTF-8',xml_declaration=True)
        return True
        
    def import_settings(self,path):
        #Used to import a user account profile from an XML file
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            user_details = root.find("user_details")
            uname = user_details.find("username").text
            pword = user_details.find("password").text
            pubkey = user_details.find("pub_key").text
            privkey = user_details.find("priv_key").text
            root.remove(user_details)
            tree.write(self.s.path)
            self.s = settings()
            self.create(uname,pword,privkey,pubkey)
        except Exception as e:
            raise Exception("invalid file")
            

#Object used to store token values
#(AES key tokens, auth codes)
class tokens_storage():
    def __init__(self):
        None
    def check_key_token(self):
        #Checks if an AES key token exists, and if so returns it
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
        #Stores a new AES key token
        file = open("user_data/key_token.txt","w")
        entry = f"{identifier}\n{key}"
        file.write(entry)
        file.close()
        return True

    def store_auth_code(self,code):
        #Stores a new auth code
        current_time = time.time()
        file = open("user_data/auth_code.txt","w")
        entry = f"{current_time},{code}"
        file.write(entry)
        file.close()
        return True
        
    def check_auth_code(self):
        #checks if a stored auth code exists,
        #and if so returns it
        file = open("user_data/auth_code.txt","r")
        content = file.read()
        file.close()
        content = content.split(",")
        check_time = float(content[0])
        code = content[1]
        return check_time,code

    def delete(self,file):
        #Deletes stored tokens
        matcher = {"key":"user_data/key_token.txt"}
        os.remove(matcher[file])

#Dataclass used to represent messages
@dataclass()
class message_store:
    author: str
    recipient: str
    content: str
    send_time: float
    token: str

#Object used to represent and interact with the messages
#database architecture
class messages():
    def __init__(self):
        #Initiates object by making sure the database exists
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
        #Deletes all stored messages
        self.c.execute("DROP TABLE Messages")
        self.conn.commit()
        self.__init__()

    def store_message(self,message):
        #Adds a new message to the database
        if not self.get_message(message.token):
            self.c.execute(f"""INSERT INTO Messages (id,author,recipient,sent_time,contents)
                            VALUES ("{message.token}","{message.author}","{message.recipient}",{message.send_time},"{message.content}");""")
            self.conn.commit()
            return True
        else:
            return False

    def store_messages(self,messages):
        #Adds a list of messages to the database
        for message in messages:
            self.store_message(message)

    def get_message_from_recipient(self,user):
        #returns all messages to a given user
        self.c.execute(f"""SELECT * FROM Messages WHERE recipient="{user}" AND recipient != author;""")
        rows = self.c.fetchall()
        messages = []
        for row in rows:
            messages.append(message_store(row[1],row[2],row[4],row[3],row[0]))
        return messages
          
    def get_messages(self,user):
        #returns all messages from a given user
        self.c.execute(f"""SELECT * FROM Messages WHERE author="{user}" AND recipient != author;""")
        rows = self.c.fetchall()
        messages = []
        for row in rows:
            messages.append(message_store(row[1],row[2],row[4],row[3],row[0]))
        return messages

    def get_message(self,token):
        #returns a singular message with the token given
        self.c.execute(f"""SELECT * FROM Messages WHERE id="{token}";""")
        rows = self.c.fetchall()
        if len(rows) == 0:
            return False
        return rows[0]
    def get_users(self):
        #Returns a list of all users who have sent messages to
        #or recieved messages from the user
        self.c.execute("SELECT DISTINCT author FROM Messages")
        results = self.c.fetchall()
        self.c.execute("SELECT DISTINCT recipient FROM Messages")
        results1 = self.c.fetchall()
        return list(dict.fromkeys((results+results1)))

    def most_recent_message(self):
        #Returns the time of the user's most recently sent or recieved
        #message stored in the database
        self.c.execute("SELECT MAX(sent_time) FROM Messages")
        result = self.c.fetchall()
        return result[0][0]
    
    def delete_message(self,identifier):
        #Deletes a message identified by the given id
        self.c.execute(f"""DELETE FROM Messages WHERE id="{identifier}";""")
        self.conn.commit()
        return True

    def edit_message(self,token,new_message):
        #updates the contents of a message
        self.c.execute(f"""UPDATE Messages SET contents = "{new_message}" WHERE id="{token}";""")
        self.conn.commit()
        return True

#Object used to represent and interact with the
#Settings XML file
class settings():
    def __init__(self,path="user_data/settings.xml"):
        #Initiates object by either retrieving existing settings
        #or creating a default settings file
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
        #Changes a specified setting
        for thing in self.tree.findall(f".//{setting}"):
            thing.text = new
        self.tree.write(self.path,encoding='UTF-8',xml_declaration=True)
        self.__init__(self.path)
        
    def delete(self):
        #Delets stored settings
        os.remove(self.path)

    
if __name__== "__main__":
    None
