#!env python3
import sys
import os
PROG_PATH = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
sys.path.append(PROG_PATH)
import argparse
from oci_oit_resource import common
from oci_oit_resource.instance import Instance
import examples.arg_processor as arg_processor


def main(attach_args):
    """ Process options to create config, and attach a volume.

        Args:
            attach_args (parse_args()): Parsed arguments.
    """
    config_dict = common.create_config_dict(attach_args)
    instance_object = Instance(config=config_dict)
    # attach volume
    resp = instance_object.attach_volume(
        instance_id=args.instance_id,
        vol_id=attach_args.vol_id
    )
    # Return the volume attachment id.
    print(resp.id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to attach a volume to an instance")
    # Config Modifications
    config_group = arg_processor.create_config_group(parser)

    attach_group = parser.add_argument_group('Instance Details',
                                             'Options used to attach volume to instance id')
    attach_group.add_argument('--instance_id',
                              help="OCID of the instance to return status of.",
                              required=True)
    attach_group.add_argument('--vol_id',
                              help="OCID of the volume to attach.",
                              required=True)
    args = parser.parse_args()
    main(args)
