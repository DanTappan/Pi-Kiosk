#! /usr/bin/env python3
#
# Control kiosk mode browser

#
import multipart
from wsgiref.simple_server import make_server
import subprocess
import io
import os
import signal
import time
import json
import re
import threading
from pathlib import Path
import bcrypt
from kiosk_cfg import html_index, pwdfilename, urlfilename, scalefilename

Debug=False

# to bind this to port 80, execute the following command
# sudo iptables -t nat -I PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 8000

listensocket = 8000

#
# Thread locking
#   
process_lock = threading.Lock()

# password checking
def check_password(pwdstr):
    """ Check the entered password against configured password """
    if pwdstr is None:
        return False
    
    pwdfile = Path(pwdfilename)
    try:
        with pwdfile.open("rb") as f:
            hashed_pwd = f.read()

        return bcrypt.checkpw(bytes(pwdstr, "utf-8"), hashed_pwd)
    except FileNotFoundError:
        return True


def reboot (arg="reboot"):
    """ run a subprocess to reboot or halt the system"""
    try:
        args = [
            "./do_reboot",
            arg
        ]
        subprocess.run(args)
    except FileNotFoundError:
        if Debug:
            print("Reboot() failed")
        pass


def shutdown ():
    reboot("halt")


def schedule_task(action, delay):
    """ thread task to perform scheduled work """
    global browser_thread_exit
    browser_thread_exit = True
    time.sleep(delay)
    action()


def schedule(action, delay=2):
    """ schedule an action to occur after a delay"""
    threading.Thread(target=(lambda: schedule_task(action, delay))).start()


class ServerURL(dict):
    def __init__(self, url):
        dict.__init__(self, name="url", url=url)
    
#
# Get the URL for web page server
#
def server_url(url=None) :
    """ Get or set the URL for the displayed webpage """
    urlfile = Path(urlfilename)

    dump = False
    if url is not None :
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
                        json_dict = json.load(f)
                        urldict = ServerURL(json_dict["url"])
                    except json.JSONDecodeError:
                        pass
            except FileNotFoundError:
                pass
                 
    server_url.urldict = urldict
            
    if dump:
        urlfile.unlink(missing_ok=True)
        with urlfile.open(mode="w") as f:
            json.dump(urldict, f)

    return urldict["url"]

def browser_scale(scale=None) :
    """ Get or set the Scale for the displayed webpage """
    scalefile = Path(scalefilename)
    scalefinal = 1.0

    dump = True
    if scale is not None :
        scalefinal = float(scale)
    else:
        try:
            with scalefile.open() as f:
                try:
                    content = f.readline()
                    scalefinal = float(content)
                    dump = False
                except ValueError:
                    pass
        except FileNotFoundError:
            pass
                 
    if dump:
        with scalefile.open(mode="w") as f:
            f.write(str(scalefinal))

    return str(scalefinal)


def webpage(msg=None):
    """ return the HTML body of a webpage. "
        msg" is an optional text to insert
    """
    url = server_url()
    scale = browser_scale()

    try:
        with open(html_index) as f,  io.BytesIO(b'') as of:
            for line in f:
                if re.search("!MSG!", line) is not None:
                    if msg is not None:
                        of.write(bytes('<p>', "utf-8"))
                        of.write(bytes(msg, "utf-8"))
                        of.write(bytes('<br><p>', "utf-8"))
                elif re.search("!URL!", line) is not None:
                        of.write(bytes('value="', "utf-8"))
                        of.write(bytes(url, "utf-8"))
                        of.write(bytes('"\n', "utf-8"))
                else:
                    line = re.sub(
                        rf'(<option\s+value="{re.escape(scale)}")(\s*>)',
                        r'\1 selected\2',
                    line)
                    of.write(line.encode("utf-8"))
            return of.getvalue()

    except FileNotFoundError:
        return None


def url_form(form):

    if not check_password(form.get("Password")):
        body = webpage(msg="Invalid password")
    elif form.get("Select"):
        url = form.get("Dropdown")
        server_url(url)
        body = webpage()
        kill_browser()
    elif form.get("Scale"):
        scale = form.get("ScaleDropdown")
        print(scale)
        browser_scale(scale)
        body = webpage()
        kill_browser()
    elif form.get("Set"):
        url = form.get("Url")
        server_url(url)
        kill_browser()
        body = webpage()
    elif form.get("Restart") :
        body = webpage(msg="Restarting browser")
        kill_browser()
    elif form.get("Reboot"):
        body = webpage(msg="Rebooting kiosk")
        schedule(reboot)
    elif form.get("Shutdown"):
        body = webpage(msg="Shutting down kiosk")
        schedule(shutdown)
    else:
        body = webpage()

    return body


def my_web_app(environ, start_response):
    status = '200 OK'

    if environ['REQUEST_METHOD'] == 'GET':
        body = webpage()
    elif multipart.is_form_request(environ):
        forms, files = multipart.parse_form_data(environ)
        body = url_form(forms)
    else:
        body = None

    if body is None:
        status = "404 not found"
        body = bytes("<html><body><p>internal error</p></body></html>", 'utf-8')

    headers = [('Content-Type', 'text/html'),
               ('Content-Length', str(len(body)))]
    start_response(status, headers)
    return [body]


def run_browser():
    """ start a subprocess running the selected browser """
    url = server_url()
    scale = browser_scale()

    args = [
        "./kiosk_browser",
        url,
        scale
    ]
    try:
        popen = subprocess.Popen(args, start_new_session=True)
    except FileNotFoundError:
        popen = None
    return popen

browser_terminate_process = False
def kill_browser():
    """ signal to shutdown and restart the browser process. This will
        be caught by the browser_thread() """
    global browser_terminate_process
    browser_terminate_process = True


browser_thread_exit = False
#
# Periodically clean up dead children
#
def browser_thread():
    global browser_terminate_process, browser_thread_exit

    while True:
        browser_terminate_process = False
        popen = run_browser()

        if popen is None:
            time.sleep(10)
        else:
            while popen.returncode is None:
                try:
                    popen.wait(1)
                except (subprocess.TimeoutExpired, KeyboardInterrupt):
                    pass
                finally:
                    if browser_terminate_process or browser_thread_exit:
                        try:
                            popen.terminate()
                            os.killpg(popen.pid, signal.SIGTERM)
                        except ProcessLookupError:
                            pass
                        browser_terminate_process = False

                    if browser_thread_exit:
                        return


        
if __name__ == '__main__' :

    threading.Thread(target=browser_thread).start()

    try:
        print(f"webserver listening on port {listensocket}")
        with make_server('', listensocket, my_web_app) as httpd:
            httpd.serve_forever()

    except KeyboardInterrupt:
        browser_terminate_process = True
        browser_thread_exit = True

