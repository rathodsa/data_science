#!env python3
import sys
import os
PROG_PATH = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
sys.path.append(PROG_PATH)
import argparse
import examples.arg_processor as arg_processor
from oci_oit_resource import common
from oci_oit_resource.instance import Instance


def main(delete_args):
    """ Process options to create config, and terminate an instance..

        Args:
            delete_args (parse_args()): Parsed arguments.
    """
    config_dict = common.create_config_dict(delete_args)
    instance_object = Instance(config=config_dict)
    # delete volume
    instance_object.terminate_instance(
        instance_id=delete_args.instance_id
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to delete a volume to an instance")
    # Config Modifications
    config_group = arg_processor.create_config_group(parser)

    delete_group = parser.add_argument_group('Instance Details',
                                             'Options used to delete volume to instance id')
    delete_group.add_argument('--instance_id',
                              help="OCID of the instance to return status of.",
                              required=True)
    args = parser.parse_args()
    main(args)
