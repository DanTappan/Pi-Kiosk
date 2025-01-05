#
# kiosk configuration variables
#
from os import path

html_index = path.abspath(path.join(path.dirname(__file__), 'index.html'))
pwdfilename=path.abspath(path.join(path.dirname(__file__), './KIOS_PASSWD'))
urlfilename=path.abspath(path.join(path.dirname(__file__), './KIOSK_URL.json'))


