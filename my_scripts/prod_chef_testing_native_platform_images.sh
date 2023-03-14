#!/bin/bash
wget -O /tmp/customboot_v1.sh https://artifacthub-tip.oraclecorp.com/decs-dev-local/Others/customboot_v1.sh
/bin/sh /tmp/customboot_v1.sh -i native -r OCI_NATIVE_CB.json -m "saikrishna.rathod@oracle.com"
reboot -f
