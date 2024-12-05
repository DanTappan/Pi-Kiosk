#! /usr/bin/env python3
#
# Control kiosk mode browser for h2rgraphics or otherwise

#
import http.server
import cgi
import os
import time
import signal
import errno
import json
import re
import pdb
import threading
import platform
from pathlib import Path
import bcrypt
from kiosk_cfg import pwdfilename, urlfilename

Debug=False
NoThread=False


# to bind this to port 80, execute the following command
# sudo iptables -t nat -I PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 8000

listensocket = 8000

#
# Thread locking
#   
process_lock = threading.Lock()

# password checking
def check_password(pwdstr):

    if pwdstr is None:
        return False
    
    pwdfile = Path(pwdfilename)
    with pwdfile.open("rb") as f:
        hashed_pwd = f.read()

    return bcrypt.checkpw(bytes(pwdstr, "utf-8"), hashed_pwd)
        

def Reboot (arg="reboot"):
    try:
        os.posix_spawn("./do_reboot", ["do_reboot", arg], os.environ)
    except:
        if Debug:
            print("Reboot() - os.posix_spawn failed");
        pass
    
def Shutdown ():
    Reboot("halt")

class ServerURL(dict):
    def __init__(self, url):
        dict.__init__(self, name="url", url=url)
    
#
# Get the URL for web page server
#
def server_url(url=None) :
    urlfile = Path(urlfilename)

    dump = False
    if url != None :
        urldict = ServerURL(url)
        dump = True
    else:
        try:
            urldict = server_url.urldict
        except AttributeError:
            # First time through. 
            # default in case URL file doesn't exist
            urldict =  ServerURL("http://google.com")

            try:
                with urlfile.open() as f:
                    try:
                        dict = json.load(f)
                        urldict = ServerURL(dict["url"])
                    except JSONDecodeError:
                        pass
            except FileNotFoundError:
                pass
                 
    server_url.urldict = urldict
            
    if (dump) :
        urlfile.unlink(missing_ok=True)
        with urlfile.open(mode="w") as f:
            json.dump(urldict, f)

    return urldict["url"]

def ok_response(self, msg):
    self.send_response(200)
    self.send_header("Content-type", "text/html")
    self.end_headers()

    self.wfile.write(bytes("<body><p>", "utf-8"))
    self.wfile.write(bytes(msg, "utf-8"))
    self.wfile.write(bytes("</p></body>", "utf-8"))


def webpage(self, url):
    try:
        with open("index.html") as f:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            for line in f:
                m = re.search("!URL!", line)
                if (m != None):
                    self.wfile.write(bytes('value="', "utf-8"))
                    self.wfile.write(bytes(url, "utf-8"))
                    self.wfile.write(bytes('"\n', "utf-8"))
                else:
                    self.wfile.write(bytes(line, "utf-8"))

    except FileNotFoundError:
        self.send_response(404, "not found")
        self.end_headers();
        self.wfile.write(bytes("<html>", "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        self.wfile.write(bytes("<p>internal error</p>", "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))


def url_form(self, form):

    if not check_password(form.getvalue("Password")):
        self.send_error(403, "invalid password")
        return False
    elif form.getvalue("Set"):
        url = form.getvalue("Url")
        webpage(self, url)
        run_browser(server_url(url))
    elif form.getvalue("Restart") :
        ok_response(self, "Restarting browser")
        run_browser(server_url())
    elif form.getvalue("Reboot"):
        ok_response(self, "Rebooting kiosk")
        Reboot()
    elif form.getvalue("Shutdown"):
        ok_response(self, "Shutting down kiosk")
        Shutdown()

    return True

        
def RunServer(server_class, handler_class ):
    if Debug:
        print("RunServer: port=", listensocket)
    server_address = ('', listensocket)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    
    def _set_redirect(self, location):
        self.send_response(302)
        self.send_header('Location', location)
        self.end_headers()

    def do_GET(self):
        if Debug:
            print("do_GET: ", self.path)
        if (self.path == "/"
            or self.path == "/index.html"
            or self.path == "/index"
            ) :
            with process_lock:
                webpage(self, server_url())
        else:
            super().do_GET()

    def do_POST(self):
        if Debug:
            print("do_POST")
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'}
        )
        with process_lock:
            url_form(self, form)

                
def browser_pid(pid=None):
    if pid != None :
        browser_pid.pid = pid
        return pid
    else :
        try:
            return(browser_pid.pid)
        except AttributeError:
            return 0

def run_browser(url) :
    pid = browser_pid()
    if pid != 0 :
        os.killpg(pid, signal.SIGTERM)
        browser_pid(0)

    pid = os.posix_spawn(
                    "./kiosk_browser",
                    [ "kiosk__browser",
                    url], os.environ,
                    setpgroup=0)
    if Debug:
        print("kiosk_browser pid=", pid, "\n")
    browser_pid(pid)
    
#
# Periodically clean up dead children
#
def periodic():

    if Debug:
        print("Starting periodic thread")

    while True:
        #
        #
        time.sleep(30)
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
            if Debug:
                print("periodic collected ", pid, "\n")
        except ChildProcessError:
            pid = -1
        if pid == browser_pid():
            if Debug :
                print("Browser child died")

            with process_lock:
                browser_pid(0)
                run_browser(server_url())
        
if __name__ == '__main__' :

    if not NoThread:
        t = threading.Thread(target=periodic)
        t.start()

    run_browser(server_url())
    
    if Debug:
        print("Starting Server")
    RunServer(http.server.HTTPServer, MyRequestHandler)
