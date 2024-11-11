#FileGUI.py

"""
    Name: Joshua Ludolf
"""

import tkinter as tk
from tkinter import scrolledtext

MainWin = None
message_box = None
entry_text = None

def New():
    global message_box
    global entry_text
    
    entry_text.delete("0","end")
    message_box.delete("1.0","end")

def Save():
    global message_box
    global entry_text

    
    message = message_box.get("1.0","end")
    

    try:
        file_name = open(entry_text.get(),"w")
        file_name.write(message)
        file_name.close()

    except:
        message_box.insert(tk.INSERT, "The File must have a name!")
    
    

   
    
def Open():
    global message_box
    global entry_text

    msg = ""

    try:
        file_name = entry_text.get()

        in_file = open(file_name, "r")
        all_lines = in_file.read().split("\n")
        for Aline in all_lines:
            msg += Aline + "\n"
    
        message_box.insert(tk.INSERT, msg)
        in_file.close()
    
    except FileNotFoundError:
        message_box.insert(tk.INSERT, "File was not found! Please give an existing file!")

    


    

def CreateMainWindow():
    global MainWin
    global message_box
    global entry_text

    MainWin.geometry("400x300")
    MainWin.title("NotePad - By, Joshua Ludolf")

    btn_new = tk.Button(MainWin, font = "TimesNewRoman", text = "New", command = New)
    btn_new.grid(row=0, column=0)

    btn_save = tk.Button(MainWin, font = "TimesNewRoman", text = "Save", command = Save)
    btn_save.grid(row=0, column=1)

    btn_open = tk.Button(MainWin, font = "TimesNewRoman", text = "Open", command = Open)
    btn_open.grid(row=0, column=2)

    lbl_label = tk.Label(MainWin, font = "TimesNewRoman", text = "File Name:")
    lbl_label.grid(row = 3, column = 0)

    entry_text = tk.Entry(MainWin, font = "TimesNewRoman", width = 10)
    entry_text.grid(row = 3, column = 1)

    message_box = tk.scrolledtext.ScrolledText(MainWin, font = "TimesNewRoman", width = 30, height = 8)
    message_box.grid(row = 1, column = 0, columnspan = 2, rowspan = 2)


    

def main():
    global MainWin
    global entry_text

    MainWin = tk.Tk()
    CreateMainWindow()
    MainWin.mainloop()

   
    

if __name__ == "__main__":
    main()