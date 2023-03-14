#!env python3
import sys
import os
PROG_PATH = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
sys.path.append(PROG_PATH)
import argparse
from oci_oit_resource import common
from oci_oit_resource.instance import Instance
import examples.arg_processor as arg_processor


def main(detach_args):
    """ Process options to create config, and detach a volume.

        Args:
            detach_args (parse_args()): Parsed arguments.
    """
    config_dict = common.create_config_dict(detach_args)
    instance_object = Instance(config=config_dict)
    # Detach volume
    instance_object.detach_volume_attachment(
        vol_attachment_id=detach_args.vol_attachment_id
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to stop instance and detach boot volume")
    # Config Modifications
    config_group = arg_processor.create_config_group(parser)

    detach_group = parser.add_argument_group('Instance Details',
                                             'Options used to stop instance and detach boot volume')
    detach_group.add_argument('--vol_attachment_id',
                              help="OCID of the volume to detach.",
                              required=True)
    args = parser.parse_args()
    main(args)
