#!env python3
import sys
import os
PROG_PATH = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
sys.path.append(PROG_PATH)
import argparse
from oci_oit_resource import common
from oci_oit_resource.instance import Instance
from oci_oit_resource.block_storage import BlockStorage
import examples.arg_processor as arg_processor


def main(create_args):
    """ Process options to create config, and create a volume.

        Args:
            create_args (parse_args()): Parsed arguments.
    """
    config_dict = common.create_config_dict(create_args)
    instance_object = Instance(config=config_dict)
    block_object = BlockStorage(config=config_dict)

    # Parse freeform tags.
    free_form_tags = {"User Email": create_args.user_email}
    # create volume
    volume = block_object.create_block_volume(
        availability_domain=create_args.availability_domain,
        compartment_id=create_args.compartment_id,
        size_in_gbs=create_args.size_in_gbs,
        block_vol_name=create_args.block_vol_name,
        freeform_tags=free_form_tags
    )
    # Attach the volume
    attach_resp = instance_object.attach_volume(
        instance_id=create_args.instance_id,
        vol_id=volume.id
    )
    # Return the volume id.
    print(volume.id)
    # Return the volume attachment id.
    print(attach_resp.id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to create a volume  and attach it to an instance")
    # Config Modifications
    config_group = arg_processor.create_config_group(parser)

    create_group = parser.add_argument_group('Instance Details',
                                             'Options used to create volume and attach it to instance id')
    create_group.add_argument('--instance_id',
                              help="OCID of the instance to return status of.",
                              required=True)
    create_group.add_argument('--vol_id',
                              help="OCID of the volume to create.",
                              required=True)
    create_group.add_argument('--availability_domain',
                              help="Availability Domain to create in.",
                              required=True)
    create_group.add_argument('--block_vol_name',
                              help="Name to give block volume",
                              required=True)
    create_group.add_argument('--block_volume_size',
                              help="Size in GBs to make block volume",
                              required=True,
                              type=float)
    create_group.add_argument('--compartment_id',
                              help="Compartment OCID.",
                              required=True)
    create_group.add_argument('--user_email',
                              help="User Email address",
                              required=True)
    args = parser.parse_args()
    main(args)
