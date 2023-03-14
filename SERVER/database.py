import sqlite3
import time
import secrets

#Object to manage all "information" database interactions
#(Information databases indicates databases that hold data about users)
#(these are differentiated from other databases to enable the defense in depth
#approach described in the security plan)
class info():
    def __init__(self,timeout=3600):
        #Initiates object by ensuring all databases exist and setting constants
        PATH = "resources/info.db"
        self.info_conn = sqlite3.connect(PATH, check_same_thread=False)
        self.info_c = self.info_conn.cursor()
        command = """CREATE TABLE IF NOT EXISTS Users (
                    username string PRIMARY KEY,
                    password string,
                    account_creation_time real NOT NULL,
                    email_address string,
                    pub_key text);"""
        self.info_c.execute(command)

        command = """CREATE TABLE IF NOT EXISTS Logins(
                    IP_address string,
                    time real,
                    username string,
                    FOREIGN KEY(username) REFERENCES Users(username),
                    PRIMARY KEY(IP_address,time)); 
                    """
        self.info_c.execute(command)

        command = """CREATE TABLE IF NOT EXISTS Messages(
                     id string PRIMARY KEY,
                     sending_user string NOT NULL,
                     sent_time real,
                     contents string,
                     recieving_user string NOT NULL,
                     FOREIGN KEY(sending_user) REFERENCES Users(username),
                     FOREIGN KEY(recieving_user) REFERENCES Users(username));"""
        self.info_c.execute(command)

        command = """CREATE TABLE IF NOT EXISTS Auth_Codes(
                    token string PRIMARY KEY,
                    owner string NOT NULL,
                    creation_time real NOT NULL,
                    IP_address string,
                    FOREIGN KEY(owner) REFERENCES Users(username),
                    FOREIGN KEY (IP_address) REFERENCES Logins(IP_address));"""
        self.info_c.execute(command)
        
        command = """CREATE TABLE IF NOT EXISTS TFA_codes(
                    code string PRIMARY KEY,
                    user string NOT NULL,
                    creation_time real NOT NULL,
                    FOREIGN KEY(user) REFERENCES Users(username));"""

        self.info_c.execute(command)
        self.timeout = timeout
        self.cleanup()
        
    def __repr__(self):
        self.info_c.execute("SELECT * FROM Users")
        rows = self.info_c.fetchall()
        for row in rows:
            print(row)
        return ""

    def add_2fa_code(self,code,user):
        #Used to insert a new 2fa code into the tfa database
        current_time = time.time()
        command = f"""INSERT INTO TFA_codes (code,user,creation_time)
                    VALUES("{code}","{user}",{current_time});"""
        self.info_c.execute(command)
        self.info_conn.commit()
        return True

    def check_2fa_code(self,code):
        #checks if a 2fa code is valid, and if so returns the associated user
        current_time = time.time()
        self.info_c.execute(f"""SELECT user FROM TFA_codes WHERE code="{code}" AND ({current_time}-creation_time)<{self.timeout} ;""")
        rows = self.info_c.fetchall()
        if len(rows) == 0:
            return False
        else:
            return rows[0][0]
    def add_user(self,uname,pword,email,pub_key):
        #Adds a new user account to the Users database
        current_time = time.time()
        if not self.check_user(uname):
            self.info_c.execute(f"""INSERT INTO Users (username,password,account_creation_time,email_address,pub_key)
            VALUES ("{uname}","{pword}",{current_time},"{email}","{pub_key}");""")
            self.info_conn.commit()
            return True
        else:
            return False

    def check_pubkey(self,uname):
        #Returns the public key of a given user
        self.info_c.execute(f"""SELECT pub_key from Users WHERE username="{uname}";""")
        rows = self.info_c.fetchall()
        if len(rows) == 0:
            return False
        else:
            return rows[0][0]

    def update_pubkey(self,uname,new_pubkey):
        #Changes the stored public key of a given user
        command = f"""UPDATE Users SET pub_key= "{new_pubkey}" WHERE username = "{uname}";"""
        self.info_c.execute(command)
        self.info_conn.commit()
        return True
    
    def delete_user(self,username):
        #Deletes a user from the username database
        self.info_c.execute(f"""DELETE FROM Users WHERE username="{username}";""")
        self.info_conn.comit()

    def get_email(self,username):
        #Returns the email address associated with a given username
        self.info_c.execute(f"""SELECT email_address FROM Users WHERE username="{username}";""")
        rows = self.info_c.fetchall()
        if len(rows) == 0:
            return False
        else:
            return rows[0][0]
    def check_user(self,username): #returns tuple of format (username,password,creation_time)
        #Used to retrieve information about a given user
        command = f"""SELECT * FROM Users WHERE username="{username}";"""
        self.info_c.execute(command)
        rows = self.info_c.fetchall()
        if len(rows) == 0:
            return False
        else:
            return rows[0]

    
    def log_login(self,IP,username):
        #Creates a log of a login 
        current_time = time.time()
        self.info_c.execute(f"""INSERT INTO Logins(IP_address,time,username)
                            VALUES ("{IP}",{current_time},"{username}");""")
        self.info_conn.commit()

    def add_auth_code(self,token,owner,ip):
        #Used to insert a new auth code into the auth codes database
        current_time = time.time()
        if not self.check_auth_token(token):
            self.info_c.execute(f"""INSERT INTO Auth_Codes(token,owner,creation_time,IP_address)
                                VALUES ("{token}","{owner}",{current_time},"{ip}")""")
            self.info_conn.commit()
            return True
        else:
            return False

    def check_auth_token(self,token,time_limit = None):
        #Checks if an auth token is valid, and if so returns its associated user
        time_limit = self.timeout if time_limit is None else time_limit
        current_time = time.time()
        self.info_c.execute(f"""SELECT owner FROM Auth_Codes
                            WHERE token = "{token}"
                            AND  ({current_time} - creation_time) < {time_limit};""")
        rows = self.info_c.fetchall()
        if len(rows) == 0:
            return False
        else:
            return rows[0][0]
    def cleanup(self,time_limit=None):
        #Deletes records from the database that are older than the time limit
        time_limit = self.timeout if time_limit is None else time_limit
        current_time = time.time()
        command = f"""DELETE FROM Auth_Codes WHERE
                    ({current_time} - creation_time) > {time_limit}"""
        self.info_c.execute(command)
        self.info_conn.commit()

        command = f"""DELETE FROM TFA_codes WHERE ({current_time} - creation_time)>{time_limit}"""
        self.info_c.execute(command)
        self.info_conn.commit()

    def add_message(self,author,recipient,contents):
        #adds a new message record to the messages database
        current_time = time.time()
        check = True
        while check:
            token = secrets.token_hex(32)
            check = self.get_message_from_id(token)
        self.info_c.execute(f"""INSERT INTO Messages(id,sending_user,sent_time,contents,recieving_user)
                            VALUES ("{token}","{author}",{current_time},"{contents}","{recipient}");""")
        self.info_conn.commit()
        return token
        
    def get_message_from_id(self,token):
        #returns a message of a given ID
        self.info_c.execute(f"""SELECT * FROM Messages WHERE id = "{token}";""")
        rows = self.info_c.fetchall()
        if len(rows) == 0:
            return False
        else:
            return rows[0]
    def get_messages_from_user(self,username,time_limit):
        #Returns all messages sent to a specified user in the last "time limit" time
        current_time = time.time()
        command = f"""SELECT * FROM Messages WHERE recieving_user = "{username}" AND sent_time > {time_limit};"""
        self.info_c.execute(command)
        rows = self.info_c.fetchall()
        if len(rows) == 0:
            return False
        else:
            return rows

    def get_messages_from_author(self,username,time_limit):
        #Returns all messages sent from a specified user in the last "time limit" time
        command = f"""SELECT * FROM Messages WHERE sending_user = "{username}" AND sent_time > {time_limit};"""
        self.info_c.execute(command)
        rows = self.info_c.fetchall()
        if len(rows) == 0:
            return False
        else:
            return rows

    def delete_message(self,token):
        #Deletes a specified message from the database
        command = f"""DELETE FROM Messages WHERE id = "{token}";"""
        self.info_c.execute(command)
        self.info_conn.commit()
        return True

    def edit_message(self,token,new_content):
        #Updates the content of a given message
        command = f"""UPDATE Messages SET contents= "{new_content}" WHERE id= "{token}";"""
        self.info_c.execute(command)
        self.info_conn.commit()
        return True
    def change_password(self,pword,user):
        #Updates the password of a given user
        self.info_c.execute(f"""UPDATE Users SET password="{pword}" WHERE username="{user}";""")
        self.info_conn.commit()
        return True

    def delete_table(self,table):
        #removes a given table
        self.info_c.execute(f"DROP TABLE {table}")
        self.info_conn.commit()

#Object used to manage all system data databases    
class tokens():
    def __init__(self,time_limit=600):
        #Initiates object by ensuring database exists and setting constants
        self.token_conn = sqlite3.connect("resources/tokens.db", check_same_thread=False)
        self.token_c = self.token_conn.cursor()
        self.time_limit = time_limit
        command = """CREATE TABLE IF NOT EXISTS key_tokens(
    id string PRIMARY KEY,
    key BLOB NOT NULL,
    creation_time real NOT NULL);"""
        self.token_c.execute(command)
        self.token_conn.commit()
        
    def __repr__(self):
        self.token_c.execute("SELECT * FROM key_tokens")
        rows = self.token_c.fetchall()
        for row in rows:
            print(row)
        return ""
    
    def add_key_token(self,key,token):
        #adds a new AES key token to the database
        if not self.check_token(token):
            print()
            print(key)
            print()
            current_time = time.time()
            command = f"""INSERT INTO key_tokens(id,key,creation_time)
            VALUES ("{token}","{key}",{current_time})"""
            self.token_c.execute(command)
            self.token_conn.commit()
            return True
        else:
            self.cleanup()
            return False
        
    def check_token(self,token,time_limit=None):
        #Checks if a token exists and is valid, and if so returns its associated key
        time_limit = self.time_limit if time_limit is None else time_limit
        current_time = time.time()
        command = f"""SELECT key FROM key_tokens WHERE id="{token}"
                    AND ({current_time} - creation_time) < {time_limit}"""
        self.token_c.execute(command)
        rows = self.token_c.fetchall()
        if len(rows) == 0:
            return False
        else:
            return rows[0][0]
    def cleanup(self,time_limit=None):
        #Deletes expired key token pairs
        time_limit = self.time_limit if time_limit is None else time_limit
        current_time = time.time()
        command = f"""DELETE FROM key_tokens WHERE
                    ({current_time} - creation_time) > {time_limit}"""
        self.token_c.execute(command)
        self.token_conn.commit()
        
    def close(self):
        self.token_c.close()
        self.token_conn.close()



     
if __name__ == "__main__":
    #For testing only
    j = info()
    #j.info_c.execute("""SELECT password FROM Users,TFA_codes WHERE Users.username=TFA_codes.user AND TFA_codes.code="737609";""")
    print(j)
    #j.delete_table("Users")


