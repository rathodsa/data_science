import argparse

import paramiko
import time


def ssh_connection():
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy()
        client.connect(username='sai', password='pass', hostname='host01')
        return client
    except exception as e:
        return False, None


def establish_connection():
    session, status = ssh_connection()
    if status:
        return session


def execute_command(command, session, wait_flag):
    if not session:
        stdout, stderr = session.exec_commnad(commands)
    if wait_flag:
        while stdout.channel.recv_exit_stattus():
            time.sleep(1)
    command_response = {stdout : stdout.readlines(), stderr : stderr.readlines()}
    return command_response

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument()
    parser.parse_args()

if __name__ == '__main__':
    main()