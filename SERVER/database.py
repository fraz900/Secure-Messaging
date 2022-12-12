import sqlite3
import time


class info():
    def __init__(self):
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
                    FOREIGN KEY(username) REFERENCES Users(username)
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
def delete_table(table):
    info_c.execute(f"DROP TABLE {table}")
    info_conn.commit()


class tokens():
    def __init__(self,time_limit=600):
        self.token_conn = sqlite3.connect("resources/tokens.db", check_same_thread=False)
        self.token_c = self.token_conn.cursor()
        self.time_limit = time_limit
        #TODO add authentication tokens table + methods
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
    print(i)


