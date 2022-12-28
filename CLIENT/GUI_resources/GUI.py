import tkinter as tk
from tkinter import filedialog as fd
from PIL import Image, ImageTk
from online.client import *
from user_data.user_utils import user,messages
import os
import time
import threading
import ctypes
import datetime

class GUI():

    def __init__(self):
        self.c = connection()
        self.u = user()
        self.m = messages()
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
            #TODO add offline mode(?)
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
        self.fileupload = False
        top = tk.Tk()
        size = f"{self.resolution[0]}x{self.resolution[1]}"
        #size = "600x700"
        top.geometry(size)
        top.title("messaging_screen")
        top.configure(bg="cyan")
        self.c.check_messages()

        top.grid_rowconfigure(0, weight=0)
        top.grid_columnconfigure(0, weight=0)
        message = tk.StringVar()
        def send():
            try:
                friend_num = friends_box.curselection()[0]
                friend = friends_box.get(friend_num)
            except:
                return False
            recipient = friend
            if self.fileupload:
                data = self.c.file_to_bin(self.path)
                name = self.c.upload(data)
                self.c.share(name,friend)
                self.c.send_user_message(f"<file>,{name},{os.path.basename(self.path)}",friend)
                self.fileupload = False
                message.set("")
                message_entry.configure(state="normal",fg="black")
                file_name.configure(text="")
            else:
                content = message.get()
                if content == "":
                    return False
                message.set("")
                self.c.send_user_message(content,recipient)
            messages()
        def exiter():
            top.destroy()

        def messages():
                    
            message_box.delete(0,(message_box.size()-1))
            
            try:
                friend_num = friends_box.curselection()[0]
                friend = friends_box.get(friend_num)
            except:
                return False
            messages_recieved = self.m.get_messages(friend)
            messages_sent = self.m.get_message_from_recipient(friend)
            messages = (messages_recieved+messages_sent)
            messages.sort(key=lambda x: x.send_time)
            count = 0
            self.message_list = []
            for message in messages:#TODO if a message is too long split it over multiple lines
                self.message_list.append(message)
                if message.content.startswith("<file>"):
                    parts = message.content.split(",")
                    message_box.insert(count,f"{message.author}: {parts[2]} <{self.unix_to_normal_time(message.send_time)}>")
                    message_box.itemconfig(count,{"fg":"blue"})
                else:
                    message_box.insert(count,f"{message.author}: {message.content} <{self.unix_to_normal_time(message.send_time)}>")
                count += 1

        def add_friend():
            self.add_friend_window(top,friends_box)

        def settings():
            self.settings_window(top)
            
        def add_file():#TODO add size limit (8mb? (hahaha you're funny, 128kb))
            filepath = fd.askopenfilename()
            filename = os.path.basename(filepath)
            file_name.configure(text=filename)
            self.fileupload = True
            self.path = filepath
            message.set("Sending File")
            message_entry.configure(state="disabled",fg="gray")

        def remove_file():
            self.fileupload = False
            message.set("")
            message_entry.configure(state="normal",fg="black")
            file_name.configure(text="")


        def do_popup(event):
            posy = message_box.winfo_rooty() 
            selected = message_box.nearest((event.y_root-posy))
            message = self.message_list[selected]
            message_box.selection_clear(0, tk.END)
            message_box.selection_set(selected)
            m = tk.Menu(message_box,tearoff=0)
            if message.content.startswith("<file>"):
                m.add_command(label="Download",command=lambda: download(message))
                if message.author == self.u.username:
                    m.add_separator()
                    m.add_command(label="delete")#TODO
            elif message.author == self.u.username:
                m.add_command(label="view info",command= lambda: view_info(message))
                m.add_command(label="edit")#TODO
                m.add_separator()
                m.add_command(label="delete")#TODO
            else:
                m.add_command(label="view info",command= lambda: view_info(message))
            try:
                m.tk_popup(event.x_root,event.y_root)
            finally:
                m.grab_release()
        def view_info(message):
            topper = tk.Toplevel(top)
            topper.geometry("750x250")
            topper.title("Message Info")
            author_label = tk.Label(topper,text=f"Author: {message.author}" ,font=('calibre',10, 'bold'))
            author_label.grid(row=0,column=0)
            recipient_label = tk.Label(topper,text=f"Recipient: {message.recipient}" ,font=('calibre',10, 'bold'))
            recipient_label.grid(row=1,column=0)
            content_label = tk.Label(topper,text=f"Content: {message.content}" ,font=('calibre',10, 'bold'))
            content_label.grid(row=2,column=0)
            send_time_label = tk.Label(topper,text=f"Send time: {message.send_time}" ,font=('calibre',10, 'bold'))
            send_time_label.grid(row=3,column=0)
            token_label = tk.Label(topper,text=f"ID Token: {message.token}" ,font=('calibre',10, 'bold'))
            token_label.grid(row=4,column=0)

        def download(message):#TODO consider threading?
            info = message.content.split(",")
            retrieval = info[1]
            filename = info[2]
            data = self.c.view(retrieval)
            data = data.strip()
            byte_string = self.c.bin_to_bytes(data)
            path = os.path.join(r"c:\Users\Admin\Downloads",filename)#TODO let em pick
            file = open(path,"wb")
            file.write(byte_string)
            file.close()
            self.notif(top,"download complete")

        def logout():
            self.u.delete("account")
            top.destroy()
            self.login()
        frame = tk.Frame(top,width=400,height=100,bg="red")
        frame.grid(row=1,column=0, sticky="n")
        
        message_entry = tk.Entry(frame,textvariable = message, font=('calibre',10,'normal'))
        message_entry.grid(row=1,column=0)

        file_name = tk.Label(frame,text="",font=('calibre',10, 'bold'),fg="blue",bg="red")
        file_name.grid(row=2,column=0)
        
        send_button = tk.Button(frame,text = "Send Message", command = send)
        send_button.grid(row=1,column=1)

        #"friend" here is used to indicate someone you are communicating with, there is no "friending" system
        add_friend_button = tk.Button(frame,text="New Chat",command=add_friend)
        add_friend_button.grid(row=2,column=1)

        exit_button = tk.Button(frame,text="Exit",command=exiter)
        exit_button.grid(row=3,column=1)

        add_file_button = tk.Button(frame,text="Add File",command=add_file)
        add_file_button.grid(row=6,column=1)

        remove_file_button = tk.Button(frame,text="Remove File",command=remove_file)
        remove_file_button.grid(row=7,column=1)

        friends_box = tk.Listbox(frame,selectmode = "single")
        friends = self.m.get_users()
        print(friends)
        count = 1
        for friend in friends:
            friend = friend[0]
            if friend != self.u.username:
                friends_box.insert(count,friend)
                count += 1
        friends_box.grid(row=5,column=0)
        friends_box.bind("<Double-1>", lambda x: messages())
        
        message_box = tk.Listbox(top,selectmode="single",width=100)
        message_box.grid(row=1,column=1,sticky="nsew")
        message_box.bind("<Button-3>", do_popup)

        settings_button = tk.Button(frame,text="Settings",command=settings)
        settings_button.grid(row=7,column=0)

        logout_button = tk.Button(frame,text="Logout",command=logout)
        logout_button.grid(row=8,column=0)
        
        top.resizable(True,True)
        top.mainloop()

    def add_friend_window(self,top,friends_box):
        topper = tk.Toplevel(top)
        topper.geometry("750x250")
        topper.title("Start chat")
        name = tk.StringVar()
        def check():
            uname = name.get()
            name.set("")
            if uname == "":
                error_lbl.configure(text="Please enter a username")
                return False
            if self.c.check_user(uname):
                print(friends_box.size())
                friends_box.insert((friends_box.size()),uname)
                topper.destroy()
            else:
                error_lbl.configure(text="Could not find user")
            
        lbl = tk.Label(topper,text="Enter the username of the person you wish to chat to:" ,font=('calibre',10, 'bold'))
        lbl.grid(row=0,column=1)

        entry_box = tk.Entry(topper,textvariable=name,font=('calibre',10,'normal'))
        entry_box.grid(row=1,column=1)

        submit_button = tk.Button(topper,text="Start Chat",command=check)
        submit_button.grid(row=2,column=1)

        error_lbl = tk.Label(topper,text="" ,font=('calibre',10, 'bold'),fg="red")
        error_lbl.grid(row=3,column=1)

    def settings_window(self,top):#TODO
        topper = tk.Toplevel(top)
        topper.geometry("750x250")
        topper.title("Settings")

        #download file (file explorer and entry input)


        #Account deletion
        
    def unix_to_normal_time(self,time):
        new = datetime.datetime.fromtimestamp(time)
        timer = new.strftime("%H:%M %d/%m/%Y")
        return timer

    def notif(self,top,message):
        topper = tk.Toplevel(top)
        topper.geometry("500x200")
        topper.title("Notification")
        tk.Label(topper,text=message,font=('calibre',10, 'bold')).grid(row=1.column=1)
        
if __name__ == "__main__":
    g = GUI()
    g.main()
    #g.login()
