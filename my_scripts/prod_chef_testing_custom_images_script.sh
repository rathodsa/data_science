#!/bin/bash
wget -O /tmp/customboot_v1.sh https://artifacthub-tip.oraclecorp.com/decs-dev-local/Others/customboot_v1.sh
/bin/sh /tmp/customboot_v1.sh -i custom -r OCI_DEFAULT_CB.json -m “Saikrishna.rathod@oracle.com”
reboot -f
