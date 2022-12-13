import tkinter as tk
from PIL import Image, ImageTk
from online.client import *
from user_data.user_utils import user
import os
import time
import threading
import ctypes

class GUI():

    def __init__(self):
        self.c = connection()
        self.u = user()
        user32 = ctypes.windll.user32
        self.resolution = user32.GetSystemMetrics(0),user32.GetSystemMetrics(1)
        
    def start(self):
        if self.c.ping():
            if self.u.exists:
                try:
                    check = self.c.login(self.u.username,self.u.pass_hash,hashed=True)
                    if not check:
                        self.u.delete("account")
                        self.login()
                    else:
                        self.main()
                except Exception as e:
                    self.u.delete("account")
                    self.login()
            else:
                self.login()
        else:
            #add offline mode
            self.error("Connection error, cannot connect to server.\n Please try again later")

    def error(self,error_message):
        top = tk.Tk()
        top.title("ERROR")
        top.geometry("300x100")
        
        error_label = tk.Label(top, text = error_message, font=('calibre',10, 'bold'))  
        error_label.config(fg="red")
        error_label.grid(row=3,column=1)
        top.resizable(False,False)
        top.mainloop()
        
    def login(self):
        
        c = connection()
        top = tk.Tk()
        top.title("login")
        canvas=tk.Canvas(top, width=400, height=500)
        canvas.grid(row=1,column=0)

        top.geometry("450x500")
        frame = tk.Frame(top)
        name_var=tk.StringVar()
        passw_var=tk.StringVar()
        def handler():
            threading.Thread(target=start_loading).start()
            #start_loading()
            t = threading.Thread(target=submit).start()
            try:
                t.join()
            except:
                None
        def submit():
            name=name_var.get()
            password=passw_var.get()
            try:
                check = self.c.login(name,password)
                if check:
                    self.u.create(name,self.c._hash(password))
                    top.destroy()
                    self.main()
            except Exception as e:
                login_error.config(text="username or password incorrect",fg="red")
            end_loading()
            
            name_var.set("")
            passw_var.set("")
        def register():#TODO add username taken error
            name=name_var.get()
            password=passw_var.get()
            check = self.c.create_account(name,password)
            if check:
                login_error.config(text="Account created",fg="green")
                self.u.create(name,self.c._hash(password))
                time.sleep(1)
                top.destroy()
                self.main()
            else:
                login_error.config(text="Error creating account",fg="red")
        txt_frm = tk.Frame(top,width=400,height=250)
        txt_frm.grid(row=0,column=0, sticky="n")
        name_label = tk.Label(txt_frm, text = 'Username', font=('calibre',10, 'bold'))  
        name_entry = tk.Entry(txt_frm,textvariable = name_var, font=('calibre',10,'normal'))
        passw_label = tk.Label(txt_frm, text = 'Password', font = ('calibre',10,'bold'))
        passw_entry = tk.Entry(txt_frm, textvariable = passw_var, font = ('calibre',10,'normal'), show = '*')
        sub_btn=tk.Button(txt_frm,text = 'Submit', command = handler)
        reg_btn = tk.Button(txt_frm,text="Register",command=register)
        
        login_error = tk.Label(txt_frm,text="",font=("calibre",10))

        logo_image = Image.open("GUI_resources/assets/ball.png")

        resized_image= logo_image.resize((300,205), Image.ANTIALIAS)
        new_image= ImageTk.PhotoImage(resized_image)

        photo = ImageTk.PhotoImage(resized_image)
        label = tk.Label(txt_frm, image = photo)
        label.image = photo
        label.grid(row=0,column=1)
        name_label.grid(row=1,column=0)
        name_entry.grid(row=1,column=1)
        passw_label.grid(row=2,column=0)
        passw_entry.grid(row=2,column=1)
        sub_btn.grid(row=3,column=1)
        reg_btn.grid(row=5,column=1)
        login_error.grid(row=4,column=1)

        imagelist = []
        things = os.listdir("GUI_resources/assets/loading")
        for item in things:
            imagelist.append(os.path.join("GUI_resources/assets/loading",item))
        giflist = []
        for imagefile in imagelist:
            photo = Image.open(imagefile)
            giflist.append(photo)
        global repeat
        repeat = True
        def start_loading(n=1):
            gif = giflist[n%len(giflist)]
            top.resizer = resizer = ImageTk.PhotoImage(gif.resize((50,50),Image.ANTIALIAS))
            img = canvas.create_image(235,25, image=top.resizer)
            if repeat:
                timer_id = top.after(100, start_loading, n+1)
            else:
                canvas.delete(img)
        def end_loading():
            global repeat
            repeat = False
        #start_loading()
        top.resizable(False,False)
        top.mainloop()

        
    def main(self):
        top = tk.Tk()
        size = f"{self.resolution[0]}x{self.resolution[1]}"
        #size = "600x700"
        top.geometry(size)
        top.title("messaging_screen")
        top.configure(bg="cyan")

        #canvas=tk.Canvas(top, width=self.resolution[0], height=self.resolution[1])
        #canvas = tk.Canvas(top,width=600,height=350)
        #canvas.grid(row=0,column=0)

        top.grid_rowconfigure(0, weight=0)
        top.grid_columnconfigure(0, weight=0)
        message = tk.StringVar()
        def send():
            content = message.get()
            message.set("")
            recipient = "tester"#TODO add textbox for this
            self.c.send_user_message(content,recipient)
        def exiter():
            top.destroy()
            exit()
        def messages():#TODO make some GUI shit FML (and store it)
            content = self.c.check_messages()
            for message in content:
                print()
                print(message)
        frame = tk.Frame(top,width=400,height=100,bg="red")
        frame.grid(row=1,column=0, sticky="n")
        
        message_entry = tk.Entry(frame,textvariable = message, font=('calibre',10,'normal'))
        message_entry.grid(row=1,column=0)
        
        send_button = tk.Button(frame,text = "send", command = send)
        send_button.grid(row=1,column=1,padx=10,pady=10)

        exit_button = tk.Button(frame,text="exit",command=exiter)
        exit_button.grid(row=2,column=1)

        check_message_button = tk.Button(frame,text="messages",command=messages)#TESTING ONLY TODO
        check_message_button.grid(row=3,column=1)
        
        top.resizable(True,True)
        top.mainloop()
        
if __name__ == "__main__":
    g = GUI()
    g.main()
    #g.login()
