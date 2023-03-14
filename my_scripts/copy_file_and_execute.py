import os
import paramiko


def ssh_connection(username,password,host_to_connect):
    try:
        Client = paramiko.SSHClient()
        Client.set_missing_host_key_policy()
        Client.open_sftp()
        status, session = Client.connect(username=username, password=password, hostname=host_to_connect)
        if status:
            return session
    except exception as e:
        return None, False

def execute_command(session, command, wait_flag=False):
    stdout, stderr = session.exec_command(command=command)

