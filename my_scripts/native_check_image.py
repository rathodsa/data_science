#import subprocess
#from subprocess import PIPE
import paramiko
import time


def ssh_connection(address, username, password):
    print(address, username, password)
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(address, username=username, password=password, timeout=60)
        return client
    except Exception as e:
        return False, None


def establish_ssh_session(serverip, username, password):
    print(username,password,serverip)
    status, session = ssh_connection(serverip, username, password)
    if session:
        return session
    return None


def execute_command(command, session, wait_flag=False, timeout=600):
    if not session:
        print("Session not established")
    std_in, stdout, stderr = session.exec_command(command=command, timeout=timeout)
    wait_counter = 60
    if wait_flag and wait_counter <= 60:
        while stdout.channel.recv_exit_status():
            time.sleep(60)
            wait_counter += 1
    command_response = {'stdout': stdout.readlines(), 'stderr': stderr.readlines()}
    # session.close()
    return command_response


def check_image_in_native(image_name, comp_ocid, serverip, myusername, mypassword):
    print(image_name)
    print(comp_ocid)
    session = establish_ssh_session(serverip, myusername, mypassword)
    servers_first = 'sudo /home/gitlab-runner/test_wrap/stage1.sh $comp_ocid $image_name'
    result = execute_command(servers_first, session)
    if result:
        return result['stdout']
    else:
        print("there is no result")


def main():
    serverip = '100.106.154.20'
    myusername = 'sairatho'
    mypassword = 'P@#ssw0rd'
    image_name = 'peo-ol7u7-qi'
    comp_ocid = 'ocid1.tenancy.oc1..aaaaaaaavbuj6cjizbiv4zjm763rbrtd3dfhpjqhmwk4zn7w5lgz7z7cmnka'
    my_returned_value = check_image_in_native(image_name, comp_ocid, serverip, myusername, mypassword)
    print(my_returned_value)


if __name__ == '__main__':
    main()
