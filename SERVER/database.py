import sqlite3

PATH = "resources/info.db"
conn = sqlite3.connect(PATH)
c = conn.cursor()
def create_tables():
    command = """CREATE TABLE IF NOT EXISTS Users (
username string PRIMARY KEY,
password string NOT NULL,
account_creation_time text NOT NULL);"""
    c.execute(command)

    command = """CREATE TABLE IF NOT EXISTS Logins(
IP_address string,
time text,
username string,
FOREIGN KEY(username) REFERENCES Users(username)
PRIMARY KEY(IP_address,time)); 
"""
    c.execute(command)

    command = """CREATE TABLE IF NOT EXISTS Messages(
id integer PRIMARY KEY,
sending_user string NOT NULL,
sent_time text,
recieving_user string NOT NULL,
FOREIGN KEY(sending_user) REFERENCES Users(username),
FOREIGN KEY(recieving_user) REFERENCES Users(username));"""
    c.execute(command)

def add_user(uname,pword,time):
    c.execute(f"""INSERT INTO Users (username,password,account_creation_time)
    VALUES ("{uname}","{pword}","{time}")""")
    conn.commit()

def delete_table(table):
    c.execute(f"DROP TABLE {table}")
    conn.commit()
create_tables()
#add_user("test2","test3","2021-04-23")

c.execute("""SELECT * FROM Users""")
rows = c.fetchall()
for row in rows:
    print(row)
#create_tables()
