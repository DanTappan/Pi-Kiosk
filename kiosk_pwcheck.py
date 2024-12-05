#! /usr/bin/env python3
#
# Simple test program to verify that bcrypt password was saved correctly
#
import bcrypt
from getpass import getpass
from pathlib import Path
from kiosk_cfg import pwdfilename

pwdfile = Path(pwdfilename)

pwd = getpass('enter password:')
with pwdfile.open("rb") as f:
    hashed_pwd = f.read()

if bcrypt.checkpw(bytes(pwd, "utf-8"), hashed_pwd):
    print("It Matches!")
else:
    print("No Match")
    





    
