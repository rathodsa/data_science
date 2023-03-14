import argparse
import json
import os
from oci.regions import REGIONS
from oci_oit_resource.block_storage import BlockStorage
import oci_oit_resource.common as common


def main(block_args):
    """ Main function that will process the command line options and actions"""
    # Define the config_file
    oci_config = common.config_parse(block_args)
    # Setup Module BlockStorage.
    block_storage_object = BlockStorage(config=oci_config)
    if block_args.json_file:
        with open(block_args.json_file) as json_file_content:
            replica_details = json.load(json_file_content)
        for replica in replica_details:
            block_storage_object.clone_replica(
                display_name=replica['display_name'],
                compartment_id=replica['compartment_id'],
                replica_id=replica['replica_id']
            )
            print(f"Created Block volume clone {replica['display_name']}")
    else:
        block_storage_object.clone_replica(
            display_name=block_args.display_name,
            compartment_id=block_args.compartment_id,
            replica_id=block_args.replica_id
        )
        print(f"Created Block volume Clone {block_args.display_name}")


if __name__ == "__main__":
    env_vars = os.environ
    parser = argparse.ArgumentParser(description="Script to create an block from an BlockStorage.")
    # Config Modifications
    config = parser.add_argument_group('Config Modifications',
                                       'Options used for manipulating config')
    config.add_argument('--config',
                        help="Path to your config file, defaults to $HOME/.oci/config",
                        required=False,
                        default=env_vars['HOME'] + '/.oci/config')
    config.add_argument('--region',
                        help="Use if you need to override the region",
                        required=False,
                        choices=REGIONS,
                        metavar='REGION')
    config.add_argument('--tenancy',
                        help="Use if you need to override the tenancy",
                        required=False)

    block = parser.add_argument_group('BlockStorage Details',
                                      'Options used to attach volume to BlockStorage id')
    block.add_argument('--display_name',
                       help="Display name for the cloned replica.",
                       required=False)
    block.add_argument('--replica_id',
                       help="Replica OCID",
                       default=None,
                       required=False)
    block.add_argument('--compartment_id',
                       help="Compartment OCID of the replica",
                       required=False)
    block.add_argument('--json_file',
                       help="Path to json file containing replica details",
                       required=False)
    args = parser.parse_args()
    main(args)
