from socket import *
from ssl import *
from tkinter import *
from tkinter.messagebox import *
from tkinter.ttk import *

from email.base64mime import body_encode

BORDER = "-----------------------\n"

top = Tk()
top.title("SMTP Client")
top.geometry('640x480')
global toAddress, n, msg, subject
global cWindow, cbox, contactList
global lines, dList, dMailText
global dCbox, dRecCbox, dWindow, dSubjectEntry
global sCbox, sMailText
toAddress = ['0' for i in range(1000)]

f = open("contacts.ini")
contactList = []
for line in f:
    contactList += [line.strip('\n')]
f.close()


# 点击提交发送人数按钮
def recnumButtonClicked():
    global n
    global toAddress
    try:
        n = int(recnumEntry.get())
    except ValueError:
        showwarning("Warning", "Please make sure to input an integer")
        return
    ls = []
    for i in range(n):
        ls.append(i + 1)
    recComb['value'] = ls


# 点击提交发送地址按钮
def recButtonClicked():
    global toAddress
    try:
        toAddress[recComb.current()] = recEntry.get()
    except NameError:
        showwarning("Warning", "Please input the number of recipients first")
        return


# 点击提交发送内容按钮
def mailButtonClicked():
    global msg, subject
    msg = mailText.get('1.0', 'end')
    subject = subjectEntry.get()


# 切换发送地址
def recCombSelected(event):
    global toAddress
    recEntry.delete(0, END)
    try:
        recEntry.insert(0, toAddress[recComb.current()])
    except NameError:
        return


# 打开通讯录
def contactButtonClicked():
    global cWindow, cbox, contactList
    cWindow = Tk()
    cWindow.title("Contacts")
    cWindow.geometry('320x320')
    cbox = Combobox(cWindow)
    cbox.place(x=80, y=100)
    cbox['value'] = contactList

    OKButton = Button(cWindow, text="OK", command=OKButtonClicked)
    OKButton.place(x=110, y=150, height=30)
    addButton = Button(cWindow, text="add", command=addButtonClicked)
    addButton.place(x=110, y=190, height=30)


# 选择通讯对象
def OKButtonClicked():
    global cWindow, cbox
    recEntry.delete(0, END)
    recEntry.insert(0, cbox.get())
    cWindow.destroy()
    return


# 添加通讯对象
def addButtonClicked():
    global contactList, cbox
    contactList.append(cbox.get())
    cbox['value'] = contactList

    fc = open("contacts.ini", "a")
    fc.write('\n')
    fc.write(cbox.get())
    fc.close()


# 打开草稿
def draftButtonClicked():
    global lines, dList, dMailText, dCbox, dRecCbox, dWindow, dSubjectEntry
    dWindow = Tk()
    dWindow.title("Draft")
    dWindow.geometry('320x320')
    dCbox = Combobox(dWindow)
    dCbox.place(x=80, y=30)
    dCbox.bind('<<ComboboxSelected>>', dCboxSelected)

    dRecLabel = Label(dWindow, text="recipients:")
    dRecLabel.place(x=30, y=70)
    dRecCbox = Combobox(dWindow)
    dRecCbox.place(x=100, y=70)

    dSubjectLabel = Label(dWindow, text="subject:")
    dSubjectLabel.place(x=40, y=100)
    dSubjectEntry = Entry(dWindow)
    dSubjectEntry.place(x=100, y=100)

    dMailText = Text(dWindow, relief=GROOVE)
    dMailText.place(x=40, y=130, height=120, width=250)
    dChooseButton = Button(dWindow, text="Choose", command=dChooseButtonClicked)
    dChooseButton.place(x=120, y=260, height=30)

    cur = 0
    fd = open("drafts.txt")

    while fd.readline() != '':
        while fd.readline() != BORDER:
            pass
        cur = cur + 1
    fd.close()

    fd = open("drafts.txt")
    try:
        lines = int(fd.readline())
    except ValueError:
        return
    dList = [i + 1 for i in range(lines)]
    dCbox['value'] = [i + 1 for i in range(cur)]
    dSubjectEntry.insert(0, fd.readline().strip('\n'))
    for i in range(lines):
        dList[i] = fd.readline().strip('\n')
    dRecCbox['value'] = dList

    templine = fd.readline()
    while templine != BORDER and templine != '':
        dMailText.insert("insert", templine)
        templine = fd.readline()


# 把草稿复制到主窗口
def dChooseButtonClicked():
    global lines, toAddress, dList, dMailText, dWindow, dSubjectEntry
    recnumEntry.delete(0, END)
    try:
        recnumEntry.insert(0, lines)
    except NameError:
        return
    subjectEntry.delete(0, END)
    subjectEntry.insert(0, dSubjectEntry.get())
    recComb['value'] = [i + 1 for i in range(lines)]
    try:
        toAddress = dList
    except NameError:
        return
    mailText.delete('1.0', 'end')
    mailText.insert('insert', dMailText.get('1.0', 'end'))
    dWindow.destroy()


# 切换草稿编号
def dCboxSelected(event):
    global dCbox, lines, dList, dRecCbox, dMailText, dSubjectEntry
    pos = dCbox.current()
    cur = 0
    fd = open("drafts.txt")
    while cur < pos:
        while fd.readline() != BORDER:
            pass
        cur = cur + 1

    try:
        lines = int(fd.readline())
    except ValueError:
        return

    dSubjectEntry.delete(0, END)
    dSubjectEntry.insert(0, fd.readline().strip('\n'))
    dList = [i + 1 for i in range(lines)]
    for i in range(lines):
        dList[i] = fd.readline().strip('\n')
    dRecCbox['value'] = dList

    dMailText.delete('1.0', 'end')
    templine = fd.readline()
    while templine != BORDER and templine != '':
        dMailText.insert("insert", templine)
        templine = fd.readline()


# 已发送
def sentButtonClicked():
    global sCbox, sMailText
    sWindow = Tk()
    sWindow.title("Sent")
    sWindow.geometry('320x320')
    sCbox = Combobox(sWindow)
    sCbox.place(x=80, y=50)
    sCbox.bind('<<ComboboxSelected>>', sCboxSelected)

    sMailLabel = Label(sWindow, text="Mail Content")
    sMailLabel.place(x=10, y=110)
    sMailText = Text(sWindow, relief=GROOVE)
    sMailText.place(x=40, y=130, height=120, width=250)

    cur = 0
    fs = open("sent.txt")

    while fs.readline() != '':
        while fs.readline() != BORDER:
            pass
        cur = cur + 1
    fs.close()

    fs = open("sent.txt")
    sCbox['value'] = [i + 1 for i in range(cur)]

    templine = fs.readline()
    while templine != BORDER and templine != '':
        sMailText.insert("insert", templine)
        templine = fs.readline()


# 切换已发送内容编号
def sCboxSelected(event):
    global sCbox, sMailText
    pos = sCbox.current()
    cur = 0
    fs = open("sent.txt")
    while cur < pos:
        while fs.readline() != BORDER:
            pass
        cur = cur + 1

    sMailText.delete('1.0', 'end')

    templine = fs.readline()
    while templine != BORDER and templine != '':
        sMailText.insert("insert", templine)
        templine = fs.readline()


# 保存为草稿
def saveButtonClicked():
    global toAddress
    fd = open("drafts.txt", "a")
    fd.write(recnumEntry.get() + '\n')
    try:
        fd.write(subject + '\n')
    except NameError:
        showinfo("warning", "Please submit the subject")
        return
    try:
        for i in range(int(recnumEntry.get())):
            fd.write(toAddress[i] + '\n')
    except NameError:
        return
    except ValueError:
        return
    fd.write(mailText.get('1.0', 'end'))
    fd.write(BORDER)
    fd.close()


# 连接发送邮件主函数
def connectButtonClicked():
    global n, toAddress, msg
    responseText.delete("1.0", "end")
    endmsg = "\r\n.\r\n"
    # below message should be fixed and changed by yourself
    mailServer = "yourmailserver"
    fromAddress = "youraddress"
    username = "yourname"
    password = "yourkey"
    serverPort = 587
    flag = True

    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((mailServer, serverPort))
    recv = clientSocket.recv(1024).decode()
    if recv[:3] != '220':
        flag = False
    responseText.insert("insert", recv)

    # 打招呼helo
    heloCommand = "Helo Alice\r\n"
    clientSocket.send(heloCommand.encode())
    recv = clientSocket.recv(1024).decode()
    if recv[:3] != '250':
        flag = False
    responseText.insert("insert", recv)

    # 身份确认
    user_pass_encode64 = body_encode(f"\0{username}\0{password}".encode('ascii'), eol='')
    clientSocket.sendall(f'AUTH PLAIN {user_pass_encode64}\r\n'.encode())
    recv = clientSocket.recv(1024).decode()
    if recv[:3] != '235':
        flag = False
    responseText.insert("insert", recv)

    # TLS
    sslCommand = "STARTTLS\r\n"
    clientSocket.send(sslCommand.encode())
    recv = clientSocket.recv(1024).decode()
    if recv[:3] != '220':
        flag = False
    responseText.insert("insert", recv)

    # wrap socket，之后用secureClientSocket替代clientSocket
    secureClientSocket = wrap_socket(clientSocket, None, None, False, CERT_NONE, PROTOCOL_SSLv23)

    # MAIL FROM，指定发送者
    mailCommand = "MAIL FROM:<" + fromAddress + ">\r\n"
    secureClientSocket.send(mailCommand.encode())
    recv = secureClientSocket.recv(1024).decode()
    if recv[:3] != '250':
        flag = False
    responseText.insert("insert", recv)

    # RCPT TO,指定接收者
    try:
        for i in range(n):
            rcptCommand = "RCPT TO:<" + toAddress[i] + ">\r\n"
            secureClientSocket.send(rcptCommand.encode())
            recv = secureClientSocket.recv(1024).decode()
            if recv[:3] != '250':
                flag = False
            responseText.insert("insert", recv)
    except NameError:
        showwarning("Warning", "Please input the number of recipients first")
        responseText.delete("1.0", "end")
        return
    except TypeError:
        showwarning("Warning", "Please initial toAddresses")
        responseText.delete("1.0", "end")
        return

    # DATA，开始写邮件内容
    dataCommand = "DATA\r\n"
    secureClientSocket.send(dataCommand.encode())
    recv = secureClientSocket.recv(1024).decode()
    if recv[:3] != '354':
        flag = False
    responseText.insert("insert", recv)

    contentType = "text/plain"

    message = 'from:' + fromAddress + '\r\n'
    message += 'to:'
    for i in range(n):
        message += toAddress[i]
        if i != n - 1:
            message += ','
    message += '\r\n'
    try:
        message += 'subject:' + subject + '\r\n'
    except NameError:
        showwarning("warning", "Please sumbit the subject")
    message += 'Content-Type:' + contentType + '\t\n'
    try:
        message += '\r\n' + msg
    except NameError:
        showwarning("Warning", "Please input the message")
        responseText.delete("1.0", "end")
        return

    # 发送邮件主体
    secureClientSocket.send(message.encode())

    # 发送邮件结束信息
    secureClientSocket.send(endmsg.encode())
    recv = secureClientSocket.recv(1024).decode()
    if recv[:3] != '250':
        flag = False
    responseText.insert("insert", recv)

    # 退出连接
    quitCommand = "QUIT\r\n"
    secureClientSocket.send(quitCommand.encode())
    recv = secureClientSocket.recv(1024).decode()
    if recv[:3] != '221':
        flag = False
    responseText.insert("insert", recv)

    # 保存信息到已发送
    if not flag:
        return

    fs = open("sent.txt", "a")
    fs.write('subject:' + subject + '\n')
    fs.write('from:' + fromAddress + '\n')
    try:
        for i in range(int(recnumEntry.get())):
            fs.write('to:' + toAddress[i] + '\n')
    except NameError:
        return
    except ValueError:
        return
    fs.write(mailText.get('1.0', 'end'))
    fs.write(BORDER)
    fs.close()


recnumLabel = Label(top, text="Number of recipients:")
recnumLabel.place(x=90, y=30, height=30)
recnumEntry = Entry(top)
recnumEntry.place(x=230, y=30, height=30)
recLabel = Label(top, text="Recipient ")
recLabel.place(x=100, y=75)
recEntry = Entry(top)
recEntry.place(x=230, y=70, height=30)
recComb = Combobox(top, state='readonly')
recComb.bind('<<ComboboxSelected>>', recCombSelected)
recComb.place(x=165, y=75, width=60)
recnumButton = Button(top, text="Sumbit", command=recnumButtonClicked)
recnumButton.place(x=390, y=30, height=30)
recButton = Button(top, text="Sumbit", command=recButtonClicked)
recButton.place(x=390, y=70, height=30)
subjectLabel = Label(top, text="Subject:")
subjectLabel.place(x=10, y=120, height=30)
subjectEntry = Entry(top)
subjectEntry.place(x=10, y=150, height=30)
mailLabel = Label(top, text="Mail content:")
mailLabel.place(x=150, y=120, height=30)
mailText = Text(top, relief=GROOVE)
mailText.place(x=230, y=120, height=100, width=150)
mailButton = Button(top, text="Sumbit", command=mailButtonClicked)
mailButton.place(x=390, y=150, height=30)
connectButton = Button(top, text="Start Connecting", command=connectButtonClicked)
connectButton.place(x=250, y=250, height=30)
responseLabel = Label(top, text="Responses:")
responseLabel.place(x=50, y=290, height=30)
responseText = Text(top, relief=GROOVE)
responseText.place(x=130, y=300, height=150, width=450)

contactsButton = Button(top, text="Contacts", command=contactButtonClicked)
contactsButton.place(x=500, y=50, height=30)
draftButton = Button(top, text="Drafts", command=draftButtonClicked)
draftButton.place(x=500, y=90, height=30)
sentButton = Button(top, text="Sent", command=sentButtonClicked)
sentButton.place(x=500, y=130, height=30)

saveButton = Button(top, text="Save as Draft", command=saveButtonClicked)
saveButton.place(x=390, y=190, height=30)

top.mainloop()
