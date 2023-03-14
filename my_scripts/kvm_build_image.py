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
from logging.handlers import TimedRotatingFileHandler

#log paths
#log_file_path = os.path.dirname(os.path.abspath(__file__))
log_file_path = '/home/gitlab-runner/logs/'
log_file_name = "kvm_linux_on_prem_image_build.log"
# Logging config
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', '%m-%d-%Y %H:%M:%S')
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
# Commands
export_variable_command = 'export LC_ALL=en_US.utf-8;export LANG=en_US.utf-8'
shut_command = f"init 0"
destroy_host_command = f"virsh undefine"
delete_host_command = f"virsh destroy"
clean_command = "cd /tmp;" \
                "wget http://pds-chef-infrastructure.us.oracle.com/dis_chef_repo/cleanup_script/image_cleanup.py;" \
                "chmod +x image_cleanup.py;./image_cleanup.py"
search_string = "Chef run process exited unsuccessfully|Chef client finished|ORC Client finished"
grep_command = f"egrep -i '{search_string}' /root/.stinstall.log"
chef_completion_check = "Chef Client finished"
orc_completion_check = "ORC Client finished"
cloud_package_6 = "yum install -y cloud* --enablerepo=ol6_latest"
cloud_package_7 = "yum install -y cloud* --enablerepo=ol7_latest"
cloud_package_8 = "yum install -y cloud-init.noarch --enablerepo=ol8_appstream"
str_list_to_search = ["OL_PATCH_SUCCESSFUL", "SECURITY AND KERNEL PATCH IS ALREADY UPDATED"]


def check_png(ip):
    loop_val = True
    while loop_val is True:
        my_png = "ping -c 3 %s | tail -2 | grep -i packets | awk '{print $4 }'" % ip
        out1 = subprocess.run([my_png], stdout=PIPE, stderr=PIPE, shell=True)
        res = out1.stdout.decode("utf-8")
        response = res.strip()
        if int(response) == 0:
            # logger.info("Installation is complete and hence VM is not connecting")
            return response
        if int(response) == 3:
            # logger.info(f"It is waiting for Installation to finish for {ip}")
            time.sleep(180)


def host_check(ip_address):
    try:
        socket.gethostbyname(ip_address)
    except socket.gaierror:
        logger.error("DNSLookupFailure")
        exit(1)


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


def get_hostname_to_connect(build_type, data):
    if build_type == 'OVM':
        return data["host_to_connect1"]
    else:
        return data["host_to_connect2"]


def get_complete_host_name(host_name):
    return f"{host_name}.us.oracle.com"


def load_input_params(args):
    provided_version = args.version
    if args.json_file:
        with open(args.json_file) as json_data:
            data = json.load(json_data)
            version_details = data[provided_version]
            return data, version_details
    else:
        # print("Invalid json file parameter")
        logger.error("Invalid json file parameter")


def wait_to_complete(timeout):
    time.sleep(timeout)


def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--json_file', help="JSON file to be processed")
        parser.add_argument('--version', help="version to be processed")
        args = parser.parse_args()
        data, version_details = load_input_params(args)
        build_type = version_details['build_type']
        version = version_details['version']
        sub_version = version_details['sub_version']
        mac_address = version_details['mac_address']
        host_name = version_details['host_name']
        ip_address = version_details['ip_address']
        username = data['username']
        base_dir = version_details['base_dir']
        first_password_to_connect = str(base64.b64decode(data['first_pass']).decode("utf-8"))
        password = str(base64.b64decode(data['std_pass']).decode("utf-8"))
        logger.info(f"Script execution started with parameters : \n"
                    f"{build_type}, {version}, {sub_version}, {mac_address}, {host_name}, {ip_address}")
        install_command = "virt-install -d " \
                          "--mac=%s -n %s --os-type=Linux --ram=6192 --vcpus=2 " \
                          "'--extra-args=ks=http://slc16izo.us.oracle.com/ks/OVM_KVM-LINUX-%s0u%s-X8664.cfg ip=%s " \
                          "netmask=255.255.248.0 gateway=10.229.112.1 dns=10.231.225.65' --virt-type kvm --disk " \
                          "path=/data/ap_imaging/%s,size=50 " \
                          "--location http://adcab485.us.oracle.com/bootable/OracleLinux/%s/%s/%s/x86_64/ " \
                          "--graphics vnc,listen=0.0.0.0" % (mac_address, host_name, version, sub_version, ip_address,
                                                             host_name, version, sub_version, base_dir)
        # get hostname to connect
        host_to_connect = get_hostname_to_connect(build_type, data)
        # Establish the session
        session = establish_ssh_session(host_to_connect, username, password)
        #command execution
        destroy_host_command = f"virsh undefine"
        delete_host_command = f"virsh destroy"
        destroy_host_command = f"{destroy_host_command} {host_name}"
        delete_host_command = f"{delete_host_command} {host_name}"
        execute_command(export_variable_command, session)
        execute_command(destroy_host_command, session)
        time.sleep(5)
        execute_command(delete_host_command, session)
        time.sleep(5)
        exec_result = execute_command(install_command, session, True)
        logger.info(f"-----------Installation started------------\n"
                    f"Installation command : {install_command}\n"
                    f"Build Type : {build_type}")
        logger.info(f"Installation is in progress on {host_name}. please wait....")
        time.sleep(180)
        logger.info("----------------------------------------------------------\n"
                    f"{exec_result}\n"
                    "----------------------------------------------------------\n")
        time.sleep(1000)
        ping_response = check_png(ip_address)
        logger.info(f"ping response check is completed.\n ping response : {ping_response}")
        if int(ping_response) == 0:
            logger.info("Able ping the server.. hence trying xm start.. ")
            start_server_command = f"virsh start {host_name}"
            exec_result = execute_command(start_server_command, session)
            logger.info("----------------------------------------------------------\n"
                        f"{exec_result}\n"
                        "----------------------------------------------------------\n")
            if "Error" in str(exec_result) or "error" in str(exec_result):
                logger.info("There is error in the xm start .. so we are destroying and trying start again.. ")
                _destroy_host_command = f"{destroy_host_command} {host_name}"
                _delete_host_command = f"{delete_host_command} {host_name}"
                execute_command(_destroy_host_command, session)
                logger.info(f"destroy of hostname {host_name} is completed")
                exec_result = execute_command(start_server_command, session)
                logger.info("----------------------------------------------------------\n"
                            f"{str(exec_result)}\n"
                            "----------------------------------------------------------\n")
                if "Started" in str(exec_result):
                    logger.info("VM started successfully and able to connect")
        execute_command(export_variable_command, session)
        session.close()
        full_host_name = get_complete_host_name(host_name)
        logger.info(f"Complete hostname : {full_host_name}")
        comp_version = str(version) + 'u' + str(sub_version)
        print(comp_version)
        for i in range(20):
            session = establish_ssh_session(full_host_name, username, first_password_to_connect)
            if not session:
                session = establish_ssh_session(full_host_name, username, password)
            if session:
                exec_result = execute_command(grep_command, session)
                logger.info(f"----------- grep command result ------------\n"
                            f"hostname : {full_host_name}\n"
                            f"result : {exec_result}")
                result_overlay = exec_result['stdout']
                print(result_overlay)
                if len(result_overlay) > 1:
                    if chef_completion_check in result_overlay[0] and chef_completion_check in result_overlay[1]:
                        logger.info(f"Overlay is completed for hostname : {full_host_name} and server is ready to connect")
                        time.sleep(300)
                        if comp_version == 'OL6u4' or comp_version == 'OL6u6':
                            logger.info(f"Running patching script on {full_host_name} for {comp_version}")
                            patch_command = 'cd /tmp;wget https://pds-chef-dr-infrastructure.us.oracle.com/dis_chef_repo/' \
                                        'security/ol_cpu_patching.py;chmod +x ol_cpu_patching.py;python2 ol_cpu_patching.py ' \
                                        '--monthly --security-patch --force-fix --touek4'
                        else:
                            logger.info(f"Running patching script on {full_host_name} for {comp_version}")
                            patch_command = 'cd /tmp;wget https://pds-chef-dr-infrastructure.us.oracle.com/dis_chef_repo/' \
                                        'security/ol_cpu_patching.py;chmod +x ol_cpu_patching.py;python2 ol_cpu_patching.py ' \
                                        '--monthly --security-patch --force-fix'
                        # session = establish_ssh_session(full_host_name, username, password)
                        exec_result = execute_command(patch_command, session, True)
                        if str(exec_result) is None:
                            logger.error(f"Patching is either not completed or got hung on {full_host_name} ")
                        else:
                            logger.info("----------------------------------------------------------\n"
                                    f"{exec_result}\n"
                                    "----------------------------------------------------------\n")
                        if any([substring in str(exec_result) for substring in str_list_to_search]):
                            logger.info(f"Patching is complete on {full_host_name}")
                        else:
                            logger.info(f"Patching did not finish or it has errors on {full_host_name}..")
                            exit(1)
                        logger.info(f"proceeding with cloud package install on {full_host_name}")
                        if str(version) == 'OL6':
                            exec_cloud_result = execute_command(cloud_package_6, session, True)
                        elif str(version) == 'OL7':
                            exec_cloud_result = execute_command(cloud_package_7, session, True)
                        elif str(version) == 'OL8':
                            exec_cloud_result = execute_command(cloud_package_8, session, True)
                        else:
                            print("=========")
                        logger.info(f"proceeding with cleanup on {full_host_name}")
                        session = establish_ssh_session(full_host_name, username, password)
                        execute_command(clean_command, session)
                        logger.info(f"Image cleanup complete on {full_host_name}. Shutting down the Instance..")
                        execute_command(shut_command, session)
                        logger.info(f"Shutdown complete on {full_host_name}, copying the image to standard location")
                        copy_command = "cp -r /data/ap_imaging/%s /data/kvm/VirtualDisk/pipeline_2022/%s/%su%s_default_dev_kvm_v20220123"% (host_name, build_type, version, sub_version)
                        session = establish_ssh_session(host_to_connect, username, password)
                        exec_result = execute_command(copy_command, session, True)
                        logger.info("----------------------------------------------------------\n"
                                    f"{exec_result}\n"
                                    "----------------------------------------------------------\n")
                        logger.info(f"Image build completed for {full_host_name}")
                        break
                    elif orc_completion_check in result_overlay[0] and orc_completion_check in result_overlay[1]:
                        logger.info(f"Overlay is completed for hostname : {full_host_name} and server is ready to connect")
                        time.sleep(300)
                        if comp_version == 'OL6u4' or comp_version == 'OL6u6':
                            logger.info(f"Running patching script on {full_host_name} for {comp_version}")
                            patch_command = 'cd /tmp;wget https://pds-chef-dr-infrastructure.us.oracle.com/dis_chef_repo/' \
                                        'security/ol_cpu_patching.py;chmod +x ol_cpu_patching.py;python2 ol_cpu_patching.py ' \
                                        '--monthly --security-patch --force-fix --touek4'
                        else:
                            logger.info(f"Running patching script on {full_host_name} for {comp_version}")
                            patch_command = 'cd /tmp;wget https://pds-chef-dr-infrastructure.us.oracle.com/dis_chef_repo/' \
                                        'security/ol_cpu_patching.py;chmod +x ol_cpu_patching.py;python2 ol_cpu_patching.py ' \
                                        '--monthly --security-patch --force-fix'
                        # session = establish_ssh_session(full_host_name, username, password)
                        exec_result = execute_command(patch_command, session, True)
                        if str(exec_result) is None:
                            logger.error(f"Patching is either not completed or got hung on {full_host_name} ")
                            sys.exit(1)
                        else:
                            logger.info("----------------------------------------------------------\n"
                                    f"{exec_result}\n"
                                    "----------------------------------------------------------\n")
                        if any([substring in str(exec_result) for substring in str_list_to_search]):
                            logger.info(f"Patching is complete on {full_host_name}")
                        else:
                            logger.info(f"Patching did not finish or it has errors on {full_host_name}..")
                            exit(1)
                        logger.info(f"proceeding with cloud package install on {full_host_name}")
                        if str(version) == 'OL6':
                            exec_cloud_result = execute_command(cloud_package_6, session, True)
                        elif str(version) == 'OL7':
                            exec_cloud_result = execute_command(cloud_package_7, session, True)
                        elif str(version) == 'OL8':
                            exec_cloud_result = execute_command(cloud_package_8, session, True)
                        else:
                            print("=========")
                        logger.info(f"proceeding with cleanup on {full_host_name}")
                        session = establish_ssh_session(full_host_name, username, password)
                        execute_command(clean_command, session)
                        logger.info(f"Image cleanup complete on {full_host_name}. Shutting down the Instance..")
                        execute_command(shut_command, session)
                        logger.info(f"Shutdown complete on {full_host_name}, copying the image to standard location")
                        copy_command = "cp -r /data/ap_imaging/%s /data/kvm/VirtualDisk/pipeline_2022/%s/%su%s_default_dev_kvm_v20220423"% (host_name, build_type, version, sub_version)
                        session = establish_ssh_session(host_to_connect, username, password)
                        exec_result = execute_command(copy_command, session, True)
                        logger.info("----------------------------------------------------------\n"
                                    f"{exec_result}\n"
                                    "----------------------------------------------------------\n")
                        logger.info(f"Image build completed for {full_host_name}")
                        break
                else:
                    logger.info(f"Overlay not finished.trying again with root user for {full_host_name}.")
                    time.sleep(600)
            else:
                logger.info(f"unable to connect to hostname : {full_host_name} "
                            f"with username : {username}.Trying to connect again...")
                time.sleep(300)
        logger.info(f"Image build finished for major version : {version}and minor version: {sub_version} "
                    f"on the host {host_name}")
        session.close()

    except Exception as ex:
        logger.error("Exception occurred: " % ex)


if __name__ == '__main__':
    main()