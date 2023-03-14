import argparse
import json
import time
import socket
import paramiko
import subprocess
from subprocess import PIPE
import base64
import os
import logging
import sys


log_file_path = '/home/gitlab-runner/logs'
log_file_name = 'on_premise_windows.log'
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter()
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(formatter)
file_handler = logging.FileHandler(f"{log_file_path}/{log_file_name}")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stdout_handler)
'''LOG_FORMAT = "[%(asctime)s] %(levelname)s %(threadName)s %(message)s"
formatter = logging.Formatter(LOG_FORMAT)
handler = TimedRotatingFileHandler(LOG_FILE_PATH + "on_prem.log",
                                   when='midnight',
                                   interval=1,
                                   backupCount=5, encoding='utf8')
handler.suffix = "%Y-%m-%d"
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)'''


# commands
export_variable_command = 'export LC_ALL=en_US.utf-8;export LANG=en_US.utf-8'
shut_command = f"init 0"
destroy_host_command = f"xm destroy"
delete_host_command = f"xm delete"
pre_cmd = ["/usr/bin/pwsh", "-c"]

def check_png(ip):
    loop_val = True
    while loop_val is True:
        my_png = "ping -c 3 %s | tail -2 | grep -i packets | awk '{print $4 }'" % ip
        out1 = subprocess.run([my_png], stdout=PIPE, stderr=PIPE, shell=True)
        res = out1.stdout.decode("utf-8")
        response = res.strip()
        if int(response) == 3:
            # logger.info("VM is in network")
            return response
        if int(response) == 0:
            # logger.info(f"It is waiting for {ip} to come in network")
            time.sleep(180)


def get_hostname_to_connect(build_type, data):
    if build_type == 'Developer':
        return data["host_to_connect2"]
    else:
        return data["host_to_connect1"]


def load_input_parameters(args):
    provided_version = args.version
    if args.json_file:
        with open (args.json_file) as json_data:
            data = json.load(json_data)
            version_details = data[provided_version]
        return data, version_details
    else:
        logger.info("Invalid json parameter passed")


def ssh_connection(address, username, password):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(address, username=username, password=password, timeout=60)
        return True, client
    except Exception as e:
        return False, None


def establish_ssh_session(host_to_connect, username, password):
    status, session = ssh_connection(host_to_connect, username, password)
    if status:
        return session
    return None


def execute_command(command, session, wait_flag=False, timeout=600):
    if not session:
        # print("Invalid connection session to connect to server.")
        logger.error("Invalid connection session to connect to server.")
    std_in, stdout, stderr = session.exec_command(command=command, timeout=timeout)
    if wait_flag:
        while stdout.channel.recv_exit_status():
            time.sleep(1)
    command_response = {'stdout': stdout.readlines(), 'stderr': stderr.readlines()}
    # session.close()
    return command_response


def chek_firewalld(ip_address):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for i in range(20):
        result = sock.connect_ex((ip_address, 5985))
        if result == 0:
            return result
        else:
            time.sleep(300)
    sock.close()


def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--json_file', help="JSON file to be processed")
        parser.add_argument('--version', help="version to be processed")
        args = parser.parse_args()
        data, version_details = load_input_parameters(args)
        build_type = version_details['build_type']
        mac_address = version_details['mac_address']
        ip_address = version_details['ip_address']
        raw_file = version_details['raw_file']
        username = "root"
        password = str(base64.b64decode(data['std_pass']).decode("utf-8"))
        host_name = version_details['host_name']
        fqdn_host_name = str(host_name) + '.' + str("us.oracle.com")
        host_to_connect = get_hostname_to_connect(build_type, data)
        session = establish_ssh_session(host_to_connect, username, password)
        execute_command(export_variable_command, session)
        actual_trigger_cmd = [f"Import-Module /scratch/native/packer_custom_image_windows/windows/winconnect_legacy.ps1;winconnect_legacy -ComputerName {fqdn_host_name}"]
        actual_status_cmd = [f"Import-module /scratch/native/packer_custom_image_windows/windows/imagingcompleted.ps1;imagingcompleted -i {ip_address}"]
        install_command = "virt-install --mac=%s --name=%s --vnc --hvm --vcpu=2 --ram=6503 " \
                       "--disk /OVS/Repositories/EAE8D11C473147CCBB4686EF6312F038/ISOs/%s" \
                       " --import --os-type=windows --disk path=/OVS/Repositories/EAE8D11C473147CCBB4686EF6312F038/"\
                       "VirtualDisks/%s_root.img" % (mac_address, host_name, raw_file, host_name)
        logger.info(f"-----------Installation started------------\n"
                f"Installation command : {install_command}\n"
                f"Build Type : {build_type}")
        exec_result = execute_command(install_command, session, True)
        time.sleep(180)
        logger.info(f"Command triggered and here is the output..{exec_result} ")
        time.sleep(600)
        ping_response = check_png(ip_address)
        logger.info(f"ping response check is completed.\n ping response : {ping_response}")
        final_trigger_cmd = []
        final_trigger_cmd.extend(pre_cmd)
        final_trigger_cmd.extend(actual_trigger_cmd)
        print(final_trigger_cmd)
        final_status_cmd = []
        final_status_cmd.extend(pre_cmd)
        final_status_cmd.extend(actual_status_cmd)
        print(final_status_cmd)
        if int(ping_response) == 3:
            fire_result = chek_firewalld(ip_address)
            if int(fire_result) == 0:
                logger.info(f"Machine {host_name} is able to ping.and port is open hence trying to trigger the cloud init script")
                trigger_result = subprocess.run(final_trigger_cmd)
                logger.info(f"Trigger result : {trigger_result}")
                if int(trigger_result.returncode) == 0:
                    logger.info(f"The cloud init script is triggered on {host_name} and it is running..")
                else:
                    logger.error(f"Triggering cloud init script had errors")
                    sys.exit(1)
                for i in range(20):
                    check_overlay_status = subprocess.run(final_status_cmd)
                    logger.info(f"cloud init script output : {check_overlay_status}")
                    if int(check_overlay_status.returncode) == 0:
                        time.sleep(1200)
                        logger.info(f"The cloud init script,patching and sysprep is complete on {host_name}")
                        sys.exit(0)
                    else:
                        logger.info(f"Cloud init script still not finished on {host_name}.. trying again")
                        time.sleep(900)
            else:
                logger.info(f"port 5985 is not open on {host_name}")
            print("Cloud init and patching script completed ready for imaging on {host_name}")
    except Exception as ex:
        logger.error("Exception occurred: " % ex)


if __name__ == '__main__':
    main()
