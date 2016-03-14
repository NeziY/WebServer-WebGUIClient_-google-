from PyQt4 import QtGui, QtCore, uic
from PyQt4.QtWebKit import QWebView
import socket
import sys  # We need sys so that we can pass argv to QApplication

class Browser(QtGui.QMainWindow, QWebView):
    def __init__(self):
        # Explaining super is out of the scope of this article
        # So please google it if you're not familar with it
        # Simple reason why we use it here is that it allows us to
        # access variables, methods etc in the design.py file
        super(Browser, self).__init__()
        self.ui = uic.loadUi('testClientGui.ui')

        self.csi_thread = Client_Server_Interactive_Thread()
        self.connect(self.csi_thread, QtCore.SIGNAL("display_html(QString)"), self.display_html)
        self.csi_thread.start()

        self.ui.go_bttn.clicked.connect(self.get_url_txtbx)

    # -----------------GET TEXT FROM URL TEXT BOX----------------- #

    def get_url_txtbx(self):
        global url_txt
        url_txt = str(self.ui.url_txtbx.text())
        send_msg(url_txt)

    # -----------------DISPLAY HTML TO BROWSER----------------- #

    def display_html(self, html_content):
        if html_content != "google.com":
            self.ui.browser_window.setHtml(html_content)
        else:
            self.ui.browser_window.load(QtCore.QUrl("http://google.com"))

# -----------------QT THREAD TO SEND MSG FROM SERVER TO GUI----------------- #

class Client_Server_Interactive_Thread(QtCore.QThread):
    def __init__(self):
        super().__init__()

    def run(self):
        socket_create()
        while True:
            msg = listen_for_msg()
            self.emit(QtCore.SIGNAL('display_html(QString)'), msg)

# -----------------CREATE SOCKET----------------- #


def socket_create():
    global host
    global port
    global s
    host = '192.168.2.230'
    port = 9989
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

# -----------------LISTENS TO INCOMING DATA FROM SERVER----------------- #


def listen_for_msg():
    data_str = ''
    data = s.recv(1024)
    data_str = str(data[:].decode("utf-8"))
    data_list = data_str.split("\n")
    if data_str != "" and data_str != "google.com":
        print(data_str)
    elif data_str == 'google.com':
        print(data_str)
    return data_str



# -----------------SEND REQUEST FROM USER TO SERVER----------------- #


def send_msg(msg):

        if msg == "server":
            s.send(str.encode(msg, "utf-8"))
        elif msg == "google.com" or msg != "":
            s.send(str.encode(msg, "utf-8"))
        elif msg == "quit":
            s.close()

# -----------------GUI MAIN FUNCTION----------------- #


app = QtGui.QApplication(sys.argv)  # A new instance of QApplication
form = Browser()  # We set the form to be our Browser
form.ui.show()    # Show the form
app.exec_()

