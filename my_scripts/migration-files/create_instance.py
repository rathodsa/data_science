#!env python3
import sys
import os
PROG_PATH = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
sys.path.append(PROG_PATH)
import argparse
from oci_oit_resource import common
from oci_oit_resource.instance import Instance
from oci_oit_resource.compartment import Compartment
from oci_oit_resource.block_storage import BlockStorage
from oci_oit_resource.vcn import VCN
from oci_oit_resource.exceptions import CompartmentException
import examples.arg_processor as arg_processor


def main(create_rrgs):
    """ Process options to create config, and create a volume.

        Args:
            create_rrgs (parse_args()): Parsed arguments.
    """
    # Create our config from arguments.
    config_dict = common.create_config_dict(create_rrgs)
    # Initialize our objects using the config.
    instance_object = Instance(config=config_dict)
    block_object = BlockStorage(config=config_dict)
    compart_object = Compartment(config=config_dict)
    vcn_object = VCN(config=config_dict)
    # Define compartment id either from --compartment_id or from compartment name.
    if create_rrgs.compartment_id:
        compartment_id = create_rrgs.compartment_id
    elif create_rrgs.compartment_name:
        compartment_id = compart_object.get_compartment_from_name(
            create_rrgs.compartment_name
        )
    else:
        raise CompartmentException("Either --compartment_name or --compartment_id"
                                   " needs to be sent to script.")

    # Parse freeform tags.
    free_form_tags = {"User Email": create_rrgs.user_email}
    # create instance.
    instance_resp = instance_object.create_instance(
        instance_name=create_rrgs.instance_name,
        compartment_id=compartment_id,
        availability_domain=create_rrgs.availability_domain,
        subnet_id=create_rrgs.subnet_id,
        image_id=create_rrgs.image_id,
        shape=create_rrgs.shape,
        ssh_key_file=instance_object.process_ssh_key(ssh_key_file=create_rrgs.key_file),
        free_form_tags=free_form_tags
    )
    # Get the boot volume id from the instance.
    boot_vol_id = instance_object.get_bootvolumes_from_ocid(
        instance_id=instance_resp.id,
        compartment_id=compartment_id,
        availability_domain=create_rrgs.availability_domain)[0].boot_volume_id
    # Resize the boot volume id to required size.
    block_object.resize_boot_volume(
        volume_id=boot_vol_id,
        availability_domain=create_rrgs.availability_domain,
        compartment_id=compartment_id,
        size_in_gbs=create_rrgs.boot_volume_size,
        freeform_tags=free_form_tags
    )
    # Get the vnic of the instance.
    vnic = instance_object.get_vnics(compartment_id=compartment_id, instance_id=instance_resp.id)[0]
    # Get the private ip of the instance.
    private_ip = vcn_object.get_vnic(vnic.vnic_id).private_ip
    # Print Responses
    print(f"{private_ip}; {instance_resp.id}; {compartment_id}; {create_rrgs.availability_domaint}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to create a volume  and attach it to an instance")
    # Config Modifications
    config_group = arg_processor.create_config_group(parser)
    create_group = parser.add_argument_group('Instance Details',
                                             'Options used to create volume and attach it to instance id')

    create_group.add_argument('--instance_id',
                              help="OCID of the instance to return status of.",
                              required=True)
    create_group.add_argument('--availability_domain',
                              help="Availability Domain to create in.",
                              required=True)
    create_group.add_argument('--vol_id',
                              help="OCID of the volume to create.",
                              required=True)
    create_group.add_argument('--compartment_id',
                              help="Compartment OCID.",
                              default=None,
                              required=False)
    create_group.add_argument('--compartment_name',
                              help="Compartment Name",
                              default=None,
                              required=False)
    create_group.add_argument('--instance_name',
                              help="Name to give instance",
                              required=True)
    create_group.add_argument('--shape',
                              help="OCI Shape Name",
                              required=True)
    create_group.add_argument('--image_id',
                              help="OCI Image OCID.",
                              required=True)
    create_group.add_argument('--boot_volume_size',
                              help="Size in GBs to make boot volume",
                              default=None,
                              required=False,
                              type=float)
    create_group.add_argument('--subnet_id',
                              help="Subnet OCID.",
                              required=True)
    create_group.add_argument('--user_email',
                              help="User Email address",
                              required=True)

    args = parser.parse_args()
    main(args)
