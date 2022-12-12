import sqlite3
import time
##def delete_table(table):
##    info_c.execute(f"DROP TABLE {table}")
##    info_conn.commit()

class info():
    def __init__(self,timeout=3600):
        PATH = "resources/info.db"
        self.info_conn = sqlite3.connect(PATH, check_same_thread=False)
        self.info_c = self.info_conn.cursor()
        command = """CREATE TABLE IF NOT EXISTS Users (
                    username string PRIMARY KEY,
                    password string NOT NULL,
                    account_creation_time real NOT NULL);"""
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
                     id integer PRIMARY KEY,
                     sending_user string NOT NULL,
                     sent_time real,
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
        self.timeout = timeout
        
    def __repr__(self):
        self.info_c.execute("SELECT * FROM Users")
        rows = self.info_c.fetchall()
        for row in rows:
            print(row)
        return ""

    def add_user(self,uname,pword):
        current_time = time.time()
        if not self.check_user(uname):
            self.info_c.execute(f"""INSERT INTO Users (username,password,account_creation_time)
            VALUES ("{uname}","{pword}",{current_time});""")
            self.info_conn.commit()
            return True
        else:
            return False

    def delete_user(self): #TODO
        None

    def check_user(self,username): #returns tuple of format (username,password,creation_time)
        command = f"""SELECT * FROM Users WHERE username="{username}";"""
        self.info_c.execute(command)
        rows = self.info_c.fetchall()
        if len(rows) == 0:
            return False
        else:
            return rows[0]

    def log_login(self,IP,username):
        current_time = time.time()
        self.info_c.execute(f"""INSERT INTO Logins(IP_address,time,username)
                            VALUES ("{IP}",{current_time},"{username}");""")
        self.info_conn.commit()

    def add_auth_code(self,token,owner,ip):
        current_time = time.time()
        if not self.check_auth_token(token):
            self.info_c.execute(f"""INSERT INTO Auth_Codes(token,owner,creation_time,IP_address)
                                VALUES ("{token}","{owner}",{current_time},"{ip}")""")
            self.info_conn.commit()
            return True
        else:
            return False

    def check_auth_token(self,token,time_limit = None):
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

        

class tokens():
    def __init__(self,time_limit=600):
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
    i = info()
    #i.add_user("test","check")
    #i.add_auth_code("ahsgdjh","tester","19123234")
    print(i.check_auth_token("ahsgdjh"))
    print(i)


