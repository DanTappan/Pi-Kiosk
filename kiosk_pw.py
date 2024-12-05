#! /usr/bin/env python3
#
# save a hashed password
import bcrypt
from getpass import getpass
from pathlib import Path
from kiosk_cfg import pwdfilename

pwdfile = Path(pwdfilename)

while True:
    print("Setting password for the kiosk control web page", flush=True)
    pwd = getpass('enter password:')
    pwd2 = getpass('re-enter password:')
    if pwd != pwd:
        print("passwords do not match")
        continue
    else:
        hashed_password = bcrypt.hashpw(bytes(pwd, "utf-8"), bcrypt.gensalt())

        with pwdfile.open("wb") as f:
            f.write(hashed_password)
        break




    
