./oci_compute_instance.py --create_new \
--instance_name Smaggard-testing-instance-5 \
--compartment_id ocid1.compartment.oc1..aaaaaaaaeiu7adsx35aegxbrcsdix7yihrxrs5uzuyobwoeexbxy7leitqbq \
--availability_domain LDKe:US-ASHBURN-AD-2 \
--vcn_id ocid1.vcn.oc1.iad.amaaaaaal4gwqoaaomy7rrwy33fy4wat656jbstubk7qu33u5modpf2y3fga \
--subnet_id ocid1.subnet.oc1.iad.aaaaaaaabbhs7jb4gmfvo3liejacmody572ztuyscxcps4yhrlfdhp4dbp4q \
--image_id ocid1.image.oc1.iad.aaaaaaaaffp3cnkpfxibzrdkfnxbitkgxk7al33rrhpzhfnrhfv7ml2xdpyq \
--shape VM.Standard1.2 \
--ocpus 1 \
--memory 4 \
--user_data_file examples/user_data.txt \
--ssh_public_key ../../.ssh/id_rsa.pub

./oci_compute_instance.py --create_new --json_file examples/example.json

./oci_compute_instance.py --terminate --instance_ids <instance_id>,<instance_id>
