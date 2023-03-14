#!/bin/bash
## DATE: 2023-01-23
###PURPOSE: INSTALL CLAMAV AND IGNORE IF CLAMAV IS ALREADY INSTALLED
### Version 1.6 ##
### Added removal of old Chef rpm and install of latest chef rpm
### Version 1.5 ##
### Added fix for clamav startup issue and precheck for python version
### Version 1.4 ##
### added https option to download chef rpm and tarball
### Version 1.3 ##
### added patch for missing chef rpm
### added patch for yum hung
### added enhancement for systemctl freshclam start and also logging for space issue
### Version 1.2 ##
### added patch for rpm related to yum on 14th Dec 2021
### Version 1.1 ##
### added patch for python issue related to yum and space issue  on 10th Dec 2021

###UPDATE THE LOG AND DB WITH THE STATUS
update_db_and_log()
{
  echo -e "\nHostname: $host_name - Clamav_Install_Status: $clamav_status - Freshclam_Process_Status: $freshclam_status - Cron_Clamav_Status: $cron_status - Service_Clamav_Status: $clamav_service_status - Service_Clamonacc_status: $clamonacc_service_status - Chef_Recipe_Exec_Status: $chef_exec_status - Clamav version: $clamav_version - Space_Issue_Status: $space_issue " >> $logfile
  curl -k -X 'POST' \
  'https://logfuse-api-dev.appoci.oraclecorp.com/api/v1/oitsvclog/' \
  -H 'accept: application/json' \
  -H 'X-API-KEY: ZXlKMGVYQWlPaUpLVjFRaUxDSmhiR2NpT2lKSVV6STFOaUo5LmV5SmxlSEFpT2pFMk9UYzNNRE16TXpNc0ltbGhkQ0k2TVRZek5EWXpNVE16TXl3aWMzVmlJam95ZlEuMmVaaUZSWnRZZk52ZmhjM3FWTHVOdXk5WmY0Y1lJYjJEbUk1WE9XcU5ySQ==' \
  -H 'Content-Type: application/json' \
  -d '{
    "service_name": "clamav_report",
    "host_name": "'"$host_name"'",
    "clamav_status": "'"$clamav_status"'",
    "freshclam_status": "'"$freshclam_status"'",
    "cron_status": "'"$cron_status"'",
    "clamav_service_status": "'"$clamav_service_status"'",
    "clamonacc_service_status": "'"$clamonacc_service_status"'",
    "chef_exec_status": "'"$chef_exec_status"'",
    "clamav_version": "'"$clamav_version"'",
    "space_issue_status": "'"$space_issue"'"
  }'
}

claminstallstatus()
{
  clam_output=`rpm  -qa --last | grep -i clamav`
  if [ $? -eq 0 ]
  then
    echo -e  "\n###Below is the clamav output###\n">> $logfile
    echo -e "$clam_output" >> $logfile
    echo -e "\n###End of clamav output###\n">> $logfile
    clamav_status="CLAMAV_IS_INSTALLED"
  else
    echo -e  "\n###Below is the clamav output###\n">> $logfile
    echo -e "$clam_output" >> $logfile
    echo -e "\n###End of clamav output###\n">> $logfile
    clamav_status="CLAMAV_INSTALL_FAILED"
  fi
}

####VERIFYING THE CLAMAV SERVICES
verify_service_status()
{
  clamav_version=`rpm -qa | grep -w clamav-0`
  echo -e "Starting the verification of clamav services">> $logfile
  ####FRESHCLAM DAEMON VERIFICATION
  freshclam_cmd=`ps -ef | grep -v grep | grep -i freshclam`
  if [ $? -eq 0 ]
  then
    echo -e  "\n###Below is the freshclam output###\n">> $logfile
    echo -e "$freshclam_cmd" >> $logfile
    echo -e "\n###End of freshclam output###\n">> $logfile
    freshclam_status="FRESHCLAM_DAEMON_STARTED"
  else
    echo -e  "\n###Below is the freshclam output###\n">> $logfile
    echo -e "$freshclam_cmd" >> $logfile
    echo -e "\n###End of freshclam output###\n">> $logfile
    echo -e "\nFreshclam daemon is not running\n">> $logfile
    freshclam_status="FRESHCLAM_DAEMON_FAILED"
  fi
  ####CLAMAV CRON VERIFICATION
  cron_clam_cmd=`ls -ltr /etc/cron.d/clamd_scanner_cron`
  if [ $? -eq 0 ]
  then
    echo -e  "\n###Below is the output of clamav cron###\n">> $logfile
    echo -e "$cron_clam_cmd" >> $logfile
    echo -e "\n###End of output of clamav cron###\n">> $logfile
    cron_status="CLAMAV_CRON_ENTRY_SUCCESSFUL"
  else
    echo -e  "\n###Below is the output of clamav cron###\n">> $logfile
    echo -e "$cron_clam_cmd" >> $logfile
    echo -e "\n###End of output of clamav cron###\n">> $logfile
    echo -e "\nFailed to have the clamav cron entry\n">> $logfile
    cron_status="CLAMAV_CRON_ENTRY_FAILED"
  fi
  ####CLAMAV SERVICE STATUS
  if [ $os_version -eq 6 ]
  then
    service_cmd=`/sbin/service clamd status`
    exit_stat=`echo $?`
  else
    service_cmd=`/bin/systemctl status clamd@scan.service`
    exit_stat=`echo $?`
    clamonacc_service_cmd=`/bin/systemctl status clamonacc.service`
    clamonacc_exit_stat=`echo $?`
    if [ $clamonacc_exit_stat -eq 0 ]
    then
       clamonacc_service_status="CLAMONACC_SERVICE_RUNNING"
    elif [ $clamonacc_exit_stat -eq 3 ]
    then
       clamonacc_service_status="CLAMONACC_SERVICE_STOPPED"
    elif [ $clamonacc_exit_stat -ne 0 ]
    then
       clamonacc_service_status="CLAMONACC_SERVICE_FAILED"
    fi
  fi
  if [ $exit_stat -eq 0 ]
  then
    echo -e  "\n###Below is the output of clamav service###\n">> $logfile
    echo -e "$service_cmd" >> $logfile
    echo -e "\n###End of output of clamav service###\n">> $logfile
    clamav_service_status="CLAMAV_SERVICE_RUNNING"
  elif [ $exit_stat -eq 3 ]
  then
    echo -e  "\n###Below is the output of clamav service###\n">> $logfile
    echo -e "$service_cmd" >> $logfile
    echo -e "\n###End of output of clamav service###\n">> $logfile
    clamav_service_status="CLAMAV_SERVICE_STOPPED"
  elif [ $exit_stat -ne 0 ]
  then
    echo -e  "\n###Below is the output of clamav service###\n">> $logfile
    echo -e "$service_cmd" >> $logfile
    echo -e "\n###End of output of clamav service###\n">> $logfile
    clamav_service_status="CLAMAV_SERVICE_UNAVAILABLE"
  fi
  echo -e "Starting the verification of clamav services">> $logfile
}

###RUN CHEF CONFIG
runchefConfig()
{
  chef_bvalidation=`/usr/bin/chef-client --version`
  chef_cmd=`rpm -qa | grep -i chef-13.1.31-1.el${mjrvrsn}.x86_64`
 #Instance Chef package
  rpm -e --nodeps ${chef_cmd}
  curl -k -s ${chefRPM}/orc-infra-16.1.15-5.el${mjrvrsn}.x86_64.rpm -o /tmp/orc-infra-16.1.15-5.el${mjrvrsn}.x86_64.rpm
  rpm -Uvh  /tmp/orc-infra-16.1.15-5.el${mjrvrsn}.x86_64.rpm
  if [ $? -eq 0 ]
  then
     echo "Installed Chef RPM successfully" >>$logfile
  else
      echo "ERROR: Installation of Chef RPM failed" >>$logfile
  fi
  ##Create a directory named oldrepo
  ls -ld /etc/yum.repos.d/oldrepo ||  mkdir /etc/yum.repos.d/oldrepo
  ls /etc/yum.repos.d/*.repo | egrep -v 'pditrepo.repo' | mv $(xargs) /etc/yum.repos.d/oldrepo/
  ##CHECK FOR pdit-pditrepo RPM IS LATEST IF NOT UPDATE
  pditrpm_check=`rpm -qa | grep pdit-pditrepo-2.0.20-3`
  if [ $? -ne 0 ]
  then
    echo "Installing latest pdit repo rpm" >>$logfile
    rpm -Uvh http://pd-yum-slc-01.us.oracle.com/pditrepos/LOB/OIT/OL${mjrvrsn}/x86_64/	pdit-pditrepo-2.4.10-1.el${mjrvrsn}.noarch.rpm --force
  fi
  ##CHECK FOR EXISTANCE OF PDITREPO.REPO
  ls -l /etc/yum.repos.d/pditrepo.repo
  if [ $? -eq 0 ]
  then
    echo "pditrepo.repo is available in /etc/yum.repos.d directory" >>$logfile
  else
    ls -l /opt/pdit-pditrepo/bin/update_pditrepo_file.py
    if [ $? -eq 0 ]
    then
      `/opt/pdit-pditrepo/bin/update_pditrepo_file.py -u`
    else
      rpm -Uvh http://pd-yum-slc-01.us.oracle.com/pditrepos/LOB/OIT/OL${mjrvrsn}/x86_64/	pdit-pditrepo-2.4.10-1.el${mjrvrsn}.noarch.rpm --force
      `/opt/pdit-pditrepo/bin/update_pditrepo_file.py -u`
    fi
    ls -l /etc/yum.repos.d/pditrepo.repo
    if [ $? -eq 0 ]
    then
      echo "pditrepo.repo is generated and available in /etc/yum.repos.d directory" >>$logfile
    else
      echo "pditrepo.repo is NOT available" >>$logfile
    fi
  fi
  ##Download Chef Recipe
  curl -k -s  ${chefRepo}/${chef_tar} | tar xv -C /var/
  printf "cookbook_path '/var/chef/cookbooks'\nrole_path '/var/chef/roles'\n" > /root/.client.rb
  ###EXECUTE CHEF RECIPE
  /usr/bin/chef-client -z -c /root/.client.rb -o clamav_install_latest | tee -a /root/clamavinstall.log
  if [ $? -eq 0 ]
  then
    echo "Chef Recipe Execution is successful"  >>$logfile
    chef_exec_status="CHEF_RECIPE_EXEC_SUCCESSFUL"
  else
    echo "Chef Recipe Execution is failed" >>$logfile
    chef_exec_status="CHEF_RECIPE_EXEC_FAILED"
  fi
  ####REVERT THE REPOS
  mv /etc/yum.repos.d/oldrepo/*.repo /etc/yum.repos.d/
  mkdir /var/log/clamav/
  if [ $os_version -ne 6 ]
  then
    /bin/systemctl restart clamav-freshclam.service
  fi
  sleep 300
  if [ $os_version -eq 6 ]
  then
    restart_cmd=`/sbin/service clamd restart`
  else
    restart_cmd=`/bin/systemctl restart clamav-freshclam.service;/bin/systemctl restart clamd@scan.service;/bin/systemctl restart clamonacc.service`
  fi

}

###GET THE OS VERSION
getOSVersion(){
  mjrvrsn=$(uname -r | sed 's/\(.*\)el\(.\).*/\2/g')
  echo -e "\nOs Version is  $mjrvrsn" >>$logfile
}

###Verify Prerequisites
verify_prereq(){
  root_space=`df -hTP | grep -w '/' | awk '{print $(NF-1)}' |awk -F'%' '{print $1}'`
  tmp_space=`df -hTP | grep -w '/tmp' | awk '{print $(NF-1)}' |awk -F'%' '{print $1}'`
  arch=`uname -m`
  if [[ $root_space -gt 95 || $tmp_space -gt 95 || "$arch" != "x86_64" ]];then
    echo -e "\nNo Space left on the device for /root or /tmp" >>$logfile;
    echo -e "Architecture of the machine $arch" >>$logfile;
    space_issue="No Space"
    claminstallstatus
    verify_service_status
    update_db_and_log
    exit
  fi
  pyv="$(python -V 2>&1)"
  pyvv=`echo $pyv |awk '{print $NF}'`
  echo -e "Default python that is running on machine is $pyvv" >>$logfile;
  mjrvrsn=$(uname -r | sed 's/\(.*\)el\(.\).*/\2/g')
  if [[ $mjrvrsn -eq 6 && "$pyvv" != "2.6.6" ]]; then
    python_loc=`which python`
    ls ${python_loc}2.6
    if [ $? -eq 0 ]; then
      mv $python_loc ${python_loc}.orig.clam
      ln -s  ${python_loc}2.6 $python_loc
    fi
  elif [[ $mjrvrsn -eq 7 && "$pyvv" != "2.7.5" ]]; then
    python_loc=`which python`
    ls ${python_loc}2.7
    if [ $? -eq 0 ]; then
      mv $python_loc ${python_loc}.orig.clam
      ln -s  ${python_loc}2.7 ${python_loc}
    fi
  else
    echo -e "Correct python is already available $pyvv" >>$logfile;
  fi
}

### Verify Yumhung
verify_yumhung(){
  process_hung=`ps -eo etime,pid,command | grep yum | grep -v grep |awk -F'-' '{if($1>2) print $2}' |awk '{print $2}'|xargs`
  echo -e "hung process details $process_hung" >>$logfile
  for i in $process_hung; do ps -eo etime,pid,command | grep $i | grep -v grep  >>$logfile; if [ $i -ne 1 ]; then kill -9 $i;fi;done
}

revert_python(){
  #python_loc=`which python`
  ls ${python_loc}.orig.clam
  if [ $? -eq 0 ]; then
    mv $python_loc ${python_loc}.test
    mv ${python_loc}.orig.clam ${python_loc}
    echo -e "Original python is restored" >>$logfile;
  fi
}
######VERIFY WHETHER CLAMAV IS ALREADY INSTALLED
verify_clamav()
{
  echo -e "\nStarting the verification of clamav whether it is already installed\n">> $logfile
  if [ $os_version -eq 6 ]
  then
      clam_output=`rpm  -qa --last | grep -i clamav`
  else
      clam_output=`rpm  -qa --last | grep -i 'clamav-0.103.4-1'`
  fi
  if [ $? -eq 0 ]
  then
    echo -e  "\n###Below is the clamav output###\n">> $logfile
    echo -e "$clam_output" >> $logfile
    echo -e "\n###End of clamav output###\n">> $logfile
    clamav_status="CLAMAV_IS_ALREADY_INSTALLED"
    verify_service_status
    echo -e "\nClamav is already installed. So, Exiting the script\n">> $logfile
    update_db_and_log
    exit 0
  fi
  echo -e "\nEnd of verification for clamav whether it is already installed\n">> $logfile
}


###MAIN
logfile=/root/clamavinstall.log
chefRPM=https://pds-chef-infrastructure.us.oracle.com/dis_chef_repo/bdsconfig/Prod/rpms
chefRepo=https://pds-chef-infrastructure.us.oracle.com/dis_chef_repo/bdsconfig/Prod/tarballs
os_version=$(cat /etc/oracle-release |tr -d '[a-z][A-Z]" "'|awk -F "." '{print $1}')
if [ "$os_version" == '' ]
then
os_version=$(cat /etc/redhat-release |tr -d '[a-z][A-Z]" "'|awk -F "." '{print $1}')
fi
export PATH=/usr/bin:/usr/sbin:$PATH
stdate=$(date '+%Y%m%d-%H:%M:%S %Z' --utc)
chef_tar="Agents_CB.tar"
echo "Starting the execution of clamav install script at $stdate" >$logfile
host_name=`hostname -f`
clamav_status="NA"
freshclam_status="NA"
chef_exec_status="NA"
cron_status="NA"
clamav_service_status="NA"
clamonacc_service_status="NA"
clamav_version="Not installed"
space_issue="NA"

####CHECK WHETEHR CLAMAV IS INSTALLED
####CHECK WHETEHR CLAMAV IS INSTALLED
sed -i s/^proxy/#proxy/ /etc/yum.conf
rpm --quiet -qa
if [ $? -ne 0 ]; then
  rm -f /var/lib/rpm/__db.[0-9][0-9]
  rpm --rebuilddb
  yum clean all
fi
unset http_proxy https_proxy
getOSVersion
verify_prereq
verify_yumhung
#verify_clamav
runchefConfig
revert_python
claminstallstatus
verify_service_status
enddate=$(date '+%Y%m%d-%H:%M:%S %Z' --utc)
echo "Clamav install execution completed at $enddate" >>$logfile
update_db_and_log

