import os
import sys
import time

def wait_for_ssh(ip):
    loop_val = True 
    max_wait = 600
    counter = 0
    while loop_val is True:
        cmd = '/usr/bin/nc -zv -w 2 %s 22' %(ip)
        ssh_running = os.system(cmd)
        if ssh_running == 0:
            loop_val = false 
        else:
            print("current wait time is %s seconds"% counter)
        if counter > max_wait:
            print("max time %s exceeded"% max_wait)
        time.sleep(10)
        counter += 10 
ip = sys.argv[1]
wait_for_ssh(ip)
