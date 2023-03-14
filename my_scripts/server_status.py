import paramiko
import sys
import os
import time
import datetime

class sshconnection:
    def __init__(self,username,password,ipadress):
        self.username = username
        self.password = password
        self.ipaddress = ipaddress

    try:    
        client = paramiko.SSHClient()
        client.connect(hostname=’hostname’,username=’mokgadi’,password=’mypassword’)
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    except:
        raise ValueError :
             