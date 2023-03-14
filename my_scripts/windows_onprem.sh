#!/bin/bash
#sudo python ImageBuild/Windows/oci_compute_instance.py --create_new --json_file "/home/gitlab-runner/windows/native/native2012.json" >> native2012.txt
virst install command to boot the machine
sleep 5m
/usr/bin/pwsh -c 'Import-Module /scratch/native/packer_custom_image_windows/winconnect_legacy.ps1;winconnect_legacy -ComputerName $host_name_fqdn'
sleep 20m
for ((i=1;i<=20;i++));
do
  /usr/bin/pwsh -c 'import-module /scratch/native/packer_custom_image_windows/imagingcompleted.ps1;imagingcompleted -i $ip12'
  if [ "$?" == 0 ]; then
    sleep 30m
    break
  fi
  sleep 15m
done
rm -rf /home/gitlab-runner/testn12.txt
echo "File exist and creating Image.."
