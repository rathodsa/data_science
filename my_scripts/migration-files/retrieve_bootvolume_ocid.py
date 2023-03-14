#!env python3
import sys
import os
PROG_PATH = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
sys.path.append(PROG_PATH)
import argparse
import examples.arg_processor as arg_processor
from oci_oit_resource import common
from oci_oit_resource.instance import Instance


def main(instance_args):
    """ Process options to create config and return the boot volume OCID.

        Args:
            instance_args (parse_args()): Parsed arguments.
    """
    config_dict = common.create_config_dict(instance_args)
    instance_object = Instance(config=config_dict)
    compartment_id = arg_processor.get_compartment(instance_args, config_dict)
    instance_details = instance_object.get_bootvolumes_from_ocid(
        instance_id=instance_args.instance_id,
        compartment_id=compartment_id,
        availability_domain=instance_args.ad
    )
    response = []
    seperator = '; '
    for instance in instance_details:
        response.append(instance.boot_volume_id)
    print(seperator.join(response))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to get the instance boot volume OCID")
    # Config Modifications
    config_group = arg_processor.create_config_group(parser)
    bv_group = parser.add_argument_group('Instance Details',
                                         'Options used to retrieve boot volume OCID')
    bv_group.add_argument('--instance_id',
                          help="OCID of the instance to return status of. "
                          "Requires either --compartment_id or --compartment_name",
                          required=True)
    bv_group.add_argument('--compartment_id',
                          help="Compartment OCID, if not supplied we default to tenancy",
                          required=False)
    bv_group.add_argument('--ad',
                          help="Availability Domain to search",
                          required=True)
    args = parser.parse_args()
    main(args)
