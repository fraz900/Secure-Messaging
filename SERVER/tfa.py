import re
import smtplib,ssl
import os

#Object to represent all email interactions
class Email():
    def __init__(self):
        #Initiates object with constants
        self.address = "securemessagingauthcodes@gmail.com"
        #Password stored enviromently for security reasons
        self.password = os.environ["SecureMessagingEmailPassword"]
        self.smtp_server = "smtp.gmail.com"
        self.port = 465

    def check_email_is_valid(self,email):
        #Checks whether an email is in a valid formats
        first = re.search("^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$",email)
        second = re.search("^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}[.]\w{2,3}$",email)
        if first or second:
            return True
        return False

    def send_email(self,recipient,content):
        #Sends an email to a given recipient with a given content
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.smtp_server, self.port, context=context) as server:
            server.login(self.address, self.password)
            server.sendmail(self.address,recipient,content)

    def send_code(self,recipient,code,username):
        #sends a given 2fa code to a given user of a given address
        content = f"{username}, your authentication code is: {code}"
        subject = "Secure Messaging 2FA code"
        from1 = self.address
        to = recipient
        message = f"""Subject: {subject}\n\n{content}"""
        
        self.send_email(recipient,message)

if __name__ == "__main__":
    #for testing purposes only
    e = Email()
    e.send_code("fc137190@hrsfc.ac.uk",1234,"fraz900")
