import argparse
import json
import sys
import time
import socket
import paramiko
import os
import subprocess
from subprocess import Popen, PIPE


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
def wait_for_ssh(ip):
    loop_val = True
    max_wait = 1000
    counter = 0
    while loop_val is True:
        cmd = '/usr/bin/nc -zv -w 2 %s 22' %(ip)
        ssh_running = os.system(cmd)
        if ssh_running == 0:
            print("vm %s is available for connection"% ip)
            loop_val = false
            return ssh_running
        else:
            print("current wait time is %s seconds"% counter)
        if counter > max_wait:
            print("max time %s exceeded"% max_wait)
        time.sleep(10)
        counter += 10

def check_png(ip):
    loop_val = True
    while loop_val is True:
        my_png = "ping -c 3 %s | tail -2 | grep -i packets | awk '{print $4 }'"%(ip)
        out1 = subprocess.run([my_png],stdout=PIPE,stderr=PIPE,shell=True)
        res = out1.stdout.decode("utf-8")
        print(res)
        rslt = res.strip()
        print(rslt)
        if int(rslt) == 0:
            print("Installation is complete and hence VM is not connecting")
            loop_val = False
            return rslt
        elif int(rslt) == 3:
            print("It is waiting for Installation to finish")
            time.sleep(180)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--json_file',help="JSON file to be proessed")
    args = parser.parse_args()
    if args.json_file:
        print("Parsing JSON file")
        with open(args.json_file) as json_file_content:
            d = json.load(json_file_content)
            type = d['type']
            version = d['version']
            sub_version = d['sub_version']
            mac_addr = d['mac_addr']
            host_name = d['host_name']
            ip = d['ip']
            my_cmd = "virt-install -d --mac=%s -n %s --os-type=Linux --ram=8192 --vcpus=2 '--extra-args=ks=http://slc16izo.us.oracle.com/ks/OVM_KVM-LINUX-%s0u%s-X8664.cfg ip=%s netmask=255.255.248.0 gateway=10.241.88.1 dns=10.231.225.65' --virt-type xen --disk path=/OVS/Repositories/F75CF23BD44F468AA089698044CFEDC9/VirtualDisks/%s_root.img,size=50 --location http://pd-yum-slc-01.us.oracle.com/bootable/OracleLinux/%s/%s/base/x86_64/ --graphics vnc,listen=0.0.0.0"%(mac_addr,host_name,version,sub_version,ip,host_name,version,sub_version)
            print(my_cmd)
            print(type)
            if type == 'OVM':
                 my_server = 'slcav928.us.oracle.com'
            else:
                 my_server = 'slcal653.us.oracle.com'
            password = d['std_pass']
            username = 'root'
            cm1 = 'export LC_ALL=en_US.utf-8'
            cm2 = 'export LANG=en_US.utf-8'
            my_session = SshConnection(my_server, username, password)
            my_session.execute_command(cm1)
            my_session.execute_command(cm2)
            result = my_session.execute_command(my_cmd)
            time.sleep(180)
            result = result
            print(result)
            #my_val = wait_for_ssh(ip)
            #if my_val == 0:
            #    print("the server is available for ssh")
            #else:
            print("waiting for installation to finish and VM become available")
            time.sleep(1000)
            png = check_png(ip)
            print(png)
            print("ping check is complete")
            if int(png) == 0:
                print("ping check working")
                print("we are able to ping the server.. hence trying xm start.. ")
                cm3 = "xm create /OVS/Repositories/F75CF23BD44F468AA089698044CFEDC9/VirtualMachines/%s/vm.cfg"%(host_name)
                my_session = SshConnection(my_server, username, password)
                result2 = my_session.execute_command(cm3)
                result2 = str(result2)
                if "Error" in result2:
                    print("there is error in the xm start .. so we are destroying and trying start again.. ")
                    cm4 = "xm destroy %s"%(host_name)
                    cm5 = "xm delete %s"%(host_name)
                    my_session = SshConnection(my_server, username, password)
                    my_session.execute_command(cm4)
                    print("destroy complete")
                    my_session = SshConnection(my_server, username, password)
                    my_session.execute_command(cm5)
                    print("delete complete")
                    my_session = SshConnection(my_server, username, password)
                    result2 = my_session.execute_command(cm3)
                    result2 = str(result2)
                    print(result2)
                elif "Started" in result2:
                    print("VM started succesfully and able to connect")
            # cm3 = "xm create /OVS/Repositories/F75CF23BD44F468AA089698044CFEDC9/VirtualMachines/%s/vm.cfg"%(host_name)
            # my_session = SshConnection(my_server, username, password)
            # result2 = my_session.execute_command(cm3)
            # time.sleep(10)
            # print(result2)
            # time.sleep(300)
            my_session = SshConnection(my_server, username, password)
            my_session.execute_command(cm1)
            my_session.execute_command(cm2)
            host_name = str(host_name) + str(".us.oracle.com")
            print(host_name)
            time.sleep(600)
            for i in range(20):
                print(username)
                mypass = 'welcome'
                cm4 = 'egrep -i \"Chef run process exited unsuccessfully|Chef client finished\" /root/.stinstall.log'
                my_session1 = SshConnection(host_name, username, mypass)
                if not test:

                    mypass = 'S$1v!@nE_p'
                    my_session1 = SshConnection(host_name, username, mypass)
                out1 = my_session1.execute_command(cm4)
                resul = out1['stdout']
                my_res = str(resul)
                print(my_res)
                if "Chef Client finished" in my_res:
                    print("Overlay is completed and server is ready to connect")
                    break
                else:
                    time.sleep(180)
                    print("Overlay not finished.trying again..")
            print("script finished as of now")
            # my_new_session = SshConnection(host_name, username, password)
            # result1 = my_new_session.execute_command(servers_first)






if __name__ == '__main__':
    main()
