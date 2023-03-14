declare -r comp_ocid="$1"
declare -r image_name="$2"

sudo /root/bin/oci setup repair-file-permissions --file /root/.oci/config
sudo /root/bin/oci compute image list --config-file /root/.oci/config --compartment-id $comp_ocid --lifecycle-state AVAILABLE --display-name $image_name | jq -r '.data[0].id'
