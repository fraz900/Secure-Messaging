import re
import smtplib,ssl
import os

class Email():
    def __init__(self):
        self.address = "securemessagingauthcodes@gmail.com"
        self.password = os.environ["SecureMessagingEmailPassword"]
        self.smtp_server = "smtp.gmail.com"
        self.port = 465

    def check_email_is_valid(self,email):
        first = re.search("^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$",email)
        second = re.search("^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}[.]\w{2,3}$",email)
        if first or second:
            return True
        return False

    def send_email(self,recipient,content):
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.smtp_server, self.port, context=context) as server:
            server.login(self.address, self.password)
            server.sendmail(self.address,recipient,content)

    def send_code(self,recipient,code,username):
        content = f"{username}, your authentication code is: {code}"
        subject = "Secure Messaging 2FA code"
        from1 = self.address
        to = recipient
        message = f"""Subject: {subject}\n\n{content}"""
        
        self.send_email(recipient,message)

if __name__ == "__main__":
    e = Email()
    e.send_code("fraz900@gmail.com",1234,"fraz900")
