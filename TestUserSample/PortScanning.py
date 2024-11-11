# LudolfJLab14.py

"""
    Name: Joshua Ludolf
    Class: CSEC 1436_60L
    Date: Nov. 22, 2022

    Purpose: Port Scanning GUI Program

    Pseudocode:
        1. Create the main window that will hold all of the widgets
        2. Create Buttons, Create Scroll Text, Create Text Inputs
        3. Add functions to buttons

"""

import socket
import tkinter as tk  # this will import the tkinter library and the "as tk" part makes it easier for the program to
                      # call from tkinter library
from tkinter import scrolledtext  # this will import the scrolled text class from the tkinter library

Mainwin = None  # this is the main window on which all my elements will reside
entryTextIP = None  # global widget for text entry for ip
entryTextTimeOut = None  # global widget for text entry for timeout
stMessageBox = None  # global widget for scrolled text


def ReadListOfPortNumbers():
    Infile = open("ListOfPortNumbers.csv", "r")
    next(Infile)
    AllLines = Infile.read().split("\n")
    AllWordsList = []
    for Aline in AllLines:
        AllWordsList.append(Aline.lower())
    return AllWordsList


def ReadList():
    global stMessageBox
    WordsLsit = ReadListOfPortNumbers()
    MsgBoxStr = ""
    for Aword in WordsLsit:
        MsgBoxStr += Aword + "\n"
    stMessageBox.insert(tk.INSERT, MsgBoxStr)


def PortScan(IP, PNDnary):
    """
        This function will scan all the ports from the dictionary (PNDictionary) , of one IP Address and display it to the terminal
    """
    global Mainwin
    global stMessageBox
    global entryTextTimeOut
    MsgBoxStr = ""
    try:
        Timeout = float(entryTextTimeOut.get())

    except ValueError:
        MsgBoxStr = "Timeout is not a decimal or whole number!"
        stMessageBox.insert(tk.INSERT, MsgBoxStr)
        Mainwin.update_idletasks()

    if Timeout > 0:
        if Timeout <= 1:

            TargetIP = socket.gethostbyname(IP)
            for APN in PNDnary.keys():
                ComputerCommunitcation = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                ComputerCommunitcation.settimeout(Timeout)
                if (ComputerCommunitcation.connect_ex((TargetIP, APN))) == 0:
                    MsgBoxStr += (
                        f"IP Address: {IP} , Port Number: {APN} , Port Name: {PNDnary[APN][0]} , Port Description: {PNDnary[APN][1]}\n")
                else:
                    MsgBoxStr += ""

            stMessageBox.insert(tk.INSERT, MsgBoxStr)
            Mainwin.update_idletasks()

        else:
            MsgBoxStr = (
                f"Timeout {Timeout} is too long as it is greater than 1 second and is a really long time in the real world!")
            stMessageBox.insert(tk.INSERT, MsgBoxStr)
            Mainwin.update_idletasks()
    else:
        MsgBoxStr = (f"Timeout {Timeout} is not greater than 0 (Not Possible)!")
        stMessageBox.insert(tk.INSERT, MsgBoxStr)
        Mainwin.update_idletasks()
    


def ReadPopularPortFile(FileName):
    """
        This function reads the file of popular port numbers and returns a dictionary
        FileName: The name of the file to read

        returns is a dictionary: 

        key is the port number as an integer
        value is the list which is the port name and port description

        {1:[name, description], 
        21:[name, description], 
        80:[name, description]
        .......}

    """
    PNDictionary = {}  # This is the blank dictionary
    try:
        Ifile = open(FileName, "r")
        next(Ifile)
        for Aline in Ifile:
            AlineParts = Aline.strip().split(",")  # break each line into a list of three strings
            ValueList = []  # this list is the value list
            ValueList.append(AlineParts[1])
            ValueList.append(AlineParts[2])
            PNDictionary[int(AlineParts[0])] = ValueList

    except FileNotFoundError:
        print(f"File {FileName} was not found")
        exit(0)

    return PNDictionary


def ScanIP():
    global Mainwin
    global entryTextIP
    global stMessageBox

    PNDnary = ReadPopularPortFile("ListOfPortNumbers.csv")
    IP = "" + entryTextIP.get()
    if IP.find('.') == 3:
        IPWithoutDecimals = "".join(IP.split('.'))
        lowercaseLetters = "a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z"
        uppercaseLetters = lowercaseLetters.upper()
        for num in IPWithoutDecimals:

            if num in lowercaseLetters.split(',') or num in uppercaseLetters.split(','):
                MsgBoxStr = "Invalid IP Address, IP can't have alphabetical letters in it!"
                stMessageBox.insert(tk.INSERT, MsgBoxStr)
                Mainwin.update_idletasks()
                break

            else:
                pass

        try:
            PortScan(IP, PNDnary)

        except socket.gaierror:
            MsgBoxStr = "Port Scan couldn't be perform due to IP Address not being an IP Address"
            stMessageBox.insert(tk.INSERT, MsgBoxStr)
            Mainwin.update_idletasks()






    else:
        MsgBoxStr = ("Invalid IP Address, IP must have three decimals (no more and no less) and must contain numbers ("
                     "float or integers)!")
        stMessageBox.insert(tk.INSERT, MsgBoxStr)
        Mainwin.update_idletasks()


def ClearEntry():
    global entryTextIP
    global stMessageBox

    entryTextIP.delete("0", "end")  # This will delete all the contents of the entry box from position 0 to the end
    stMessageBox.delete("1.0", "end")  # the first position in the message box is 1.0 (float)


def CreateMainWindow():
    """
        This module creates the Main Window and "paints" the various widgets on the window
    """
    global Mainwin
    global entryTextIP
    global entryTextTimeOut
    global stMessageBox

    Mainwin.geometry("600x300")
    Mainwin.title("GUI Port Scanner by Joshua Ludolf")

    lblTimeOut = tk.Label(Mainwin, text="Connection Timeout")
    lblTimeOut.grid(row=0, column=0)
    lblIP = tk.Label(Mainwin, text="IP Number To Scan")
    lblIP.grid(row=0, column=2)

    entryTextIP = tk.Entry(Mainwin, width=13)
    entryTextIP.grid(row=0, column=3)

    entryTextTimeOut = tk.Entry(Mainwin, width=10)
    entryTextTimeOut.grid(row=0, column=1)

    btnClear = tk.Button(Mainwin, text="Clear", command=ClearEntry)
    btnClear.grid(row=4, column=3, sticky="NW")

    stMessageBox = tk.scrolledtext.ScrolledText(Mainwin, width=50, height=8)
    stMessageBox.grid(row=2, column=0, columnspan=3, rowspan=2)

    btnRead = tk.Button(Mainwin, text="Read Ports", command=ReadList)
    btnRead.grid(row=4, column=0, sticky="NW")

    btnScan = tk.Button(Mainwin, text="Scan IP Num", command=ScanIP)
    btnScan.grid(row=4, column=1, sticky="NW")


def main():
    global Mainwin
    Mainwin = tk.Tk()  # I am creating a main window which is a class of tk library
    Mainwin.configure(background='light grey')

    CreateMainWindow()
    Mainwin.mainloop()  # This is the call that keeps painting the main window on the screen forever - until user
                        # kills the program


if __name__ == "__main__":
    main()
