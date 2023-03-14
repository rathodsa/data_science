import paramiko
import socket
import os
import sys
import time



class SshConnection:
    """Establish SSH connection to remote server"""

    def __init__(self, address, username, password, timeout=600):
        self.address = address
        self.username = username
        self.password = password
        self.timeout = timeout

    def validate_connection(self):
        try:
            socket.gethostbyname(self.address)
        except socket.gaierror:
            raise ValueError("DNSLookupFailure")

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.address, username=self.username, password=self.password, timeout=self.timeout)
            return client
        except paramiko.AuthenticationException:
            raise ValueError("AuthFailure")
        except paramiko.BadHostKeyException:
            raise ValueError("BadHostKey")
        except paramiko.SSHException:
            raise ValueError("SshProtocol")
        except socket.timeout:
            raise ValueError("TimeOut")


    def execute_command(self, command):
        client = self.validate_connection()
        stdin, stdout, stderr = client.exec_command(command=command, timeout=self.timeout)
        command_response = {'stdout': stdout.readlines(), 'stderr': stderr.readlines()}
        client.close()
        return command_response

class PySSH(object):


    def __init__ (self):
        self.ssh = None
        self.transport = None

    def disconnect (self):
        if self.transport is not None:
           self.transport.close()
        if self.ssh is not None:
           self.ssh.close()

    def connect(self,hostname,username,password,port=22):
        self.hostname = hostname
        self.username = username
        self.password = password

        self.ssh = paramiko.SSHClient()
        #Don't use host key auto add policy for production servers
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.load_system_host_keys()
        try:
            self.ssh.connect(hostname,port,username,password)
            self.transport=self.ssh.get_transport()
        except (socket.error,paramiko.AuthenticationException) as message:
#            print "ERROR: SSH connection to " + self.hostname+" failed: " + str(message)
            sys.exit(1)
        return  self.transport is not None

    def runcmd(self,cmd,sudoenabled=False):
        if sudoenabled:
            fullcmd="echo " + self.password + " |   sudo -S -p '' " + cmd
        else:
            fullcmd=cmd
        if self.transport is None:
            return "ERROR: connection was not established"
        session=self.transport.open_session()
        session.set_combine_stderr(True)
        #print "fullcmd ==== "+fullcmd
        if sudoenabled:
            session.get_pty()
        session.exec_command(fullcmd)
        stdout = session.makefile('rb', -1)
        #print stdout.read()
        output=stdout.read()
        session.close()
        return output

cm3 = 'ls -ltr'
host_name = '10.241.90.251'
my_png = "ping -c 3 %s | tail -2 | awk '{print $6 }'"%(host_name)
ssh_r = os.system(my_png)
print(ssh_r)
my_session = SshConnection('10.241.90.251', 'root', 'S$1v!@nE_p')
res = my_session.execute_command(my_png)
res = (res['stdout'])
res1 = my_session.execute_command(cm3)
res0 = res[0].strip()
print(res0)
if res0 == '0%':
  print("It is not connecting")
elif res0 == '100%':
  print("It is connecting ")

