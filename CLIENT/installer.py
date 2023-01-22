import socket
import os
import sys
import pathlib
import tkinter as tk
from tkinter import filedialog as fd
from tkinter import ttk
def main():
    default_install = str(pathlib.Path.home() / "Downloads")

    top = tk.Tk()
    top.title("installer")
    top.geometry("500x450")
    main_file = ""

    shortcut = tk.IntVar()
    start_after = tk.IntVar()
    def new_download_folder():
        filepath = fd.askdirectory()
        if not filepath:
            return False
        download_path_entry.configure(state=tk.NORMAL)
        download_path_entry.delete(0,tk.END)
        download_path_entry.insert(0,filepath)
        download_path_entry.configure(state=tk.DISABLED)
        return True

    def installer(path,success_indicator,shortcut,start_after):
        SERVER_IP = "127.0.0.1"
        PORT = 12345
        INSTALL_LOCATION = os.path.join(path,"Secure_Messaging")
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_IP,PORT))
        s.recv(1024)
        s.sendall("200".encode())
        s.recv(1024)
        s.sendall("in".encode())

        num_of_files = int((s.recv(1024)).decode())
        pb = ttk.Progressbar(top,orient="horizontal",mode="determinate",length=num_of_files*10)
        pb.grid(row=5,column=0)
        value = 0
        pb["value"] = value
        top.update_idletasks()
        
        s.sendall("200".encode())
        s.recv(1024)
        s.sendall("200".encode())
        while True:
            holder = (s.recv(4096)).decode()
            s.sendall("200".encode())
            if holder == "data":
                break
            else:
                os.makedirs(os.path.split(os.path.join(INSTALL_LOCATION,holder))[0],exist_ok=True)
                open(os.path.join(INSTALL_LOCATION,holder),"w").close()
                value += 10
                pb["value"] = value
                top.update_idletasks()
                
        while True:
            name = (s.recv(4096)).decode()
            s.sendall("200".encode())
            if name == "finished":
                break
            else:
                os.makedirs(os.path.split(os.path.join(INSTALL_LOCATION,name))[0],exist_ok=True)
                if os.path.split(os.path.join(INSTALL_LOCATION,name))[1] == "MAIN.py":
                    main_file = os.path.join(INSTALL_LOCATION,name)
                file = open(os.path.join(INSTALL_LOCATION,name),"wb")
                keep_alive = True
                while keep_alive:
                    data = s.recv(8000)
                    s.sendall("200".encode())
                    try:
                        if data.decode() == "end":
                            keep_alive=False
                        else:
                            file.write(data)
                    except:
                        file.write(data)
                file.close()
                value += 10
                pb["value"] = value
                top.update_idletasks()
                
        success_indicator.configure(text="Download finished",fg="green")
        if shortcut.get() == 1:
            import win32com.client
            icon = os.path.join(INSTALL_LOCATION,r"GUI_resources\assets\icon.ico")
            pather = os.path.join(str(pathlib.Path.home() / "Desktop"),"Secure Messaging.lnk")
            target = main_file
            shell = win32com.client.Dispatch("Wscript.Shell")
            shortcut = shell.CreateShortCut(pather)
            shortcut.Targetpath = target
            shortcut.IconLocation = icon
            shortcut.WorkingDirectory = INSTALL_LOCATION
            shortcut.save()
        if start_after.get() == 1:
            os.startfile(main_file,cwd=os.path.split(main_file)[0])
           

        
    download_path_entry = tk.Entry(top,font=('calibre',10,'normal'),width=30)
    download_path_entry.insert(0,default_install)
    download_path_entry.xview_moveto(1)
    download_path_entry.configure(state=tk.DISABLED)
    download_path_entry.grid(row=0,column=0)

    download_path_button = tk.Button(top,text="change",command=new_download_folder)
    download_path_button.grid(row=0,column=1)

    tk.Checkbutton(top,text="Create a shortcut?",variable=shortcut).grid(row=1,column=0)
    tk.Checkbutton(top,text="Start program after installation?",variable=start_after).grid(row=2,column=0)

    success_indicator = tk.Label(top,text="",font=('calibre',10, 'bold'))
    success_indicator.grid(row=4,column=0)
                                                        
    submit_button = tk.Button(top,text="Install",command= lambda:installer(download_path_entry.get(),success_indicator,shortcut,start_after))
    submit_button.grid(row=3,column=0)

if __name__ == "__main__":
    main()
