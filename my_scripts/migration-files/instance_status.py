#!env python3
import sys
import os
PROG_PATH = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
sys.path.append(PROG_PATH)
import argparse
import examples.arg_processor as arg_processor
from oci_oit_resource import common
from oci_oit_resource.compartment import Compartment
from oci_oit_resource.instance import Instance
from oci_oit_resource.exceptions import CompartmentException


def main(instance_args):
    """ Process options to create config and search by instance name and return
        statuses.

        Args:
            instance_args (parse_args()): Parsed arguments.
    """
    config_dict = common.create_config_dict(instance_args)
    instance_object = Instance(config=config_dict)
    compart_object = Compartment(config=config_dict)
    if instance_args.compartment_id:
        compartment_id = instance_args.compartment_id
    elif instance_args.compartment_name:
        compartment_id = compart_object.get_compartment_from_name(
            instance_args.compartment_name
        )
    else:
        raise CompartmentException("Either --compartment_name or --compartment_id"
                                   " needs to be sent to script.")
    instance_details = instance_object.get_instances_from_name(
        instance_name=instance_args.instance_name,
        compartment_id=compartment_id
    )
    response = []
    seperator = '; '
    for instance in instance_details:
        response.append(instance.lifecycle_state)
    print(seperator.join(response))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to get the instance status"
                                                 " using the instance name.  Can "
                                                 "return multiple statuses if multiple"
                                                 " instances exist with same name.")
    # Config Modifications
    config_group = arg_processor.create_config_group(parser)
    instance_group = parser.add_argument_group('Instance Details',
                                               'Options used for instance search')
    instance_group.add_argument('--instance_name',
                                help="Name of the instance to return status of."
                                     " Requires either --compartment_id or --compartment_name",
                                required=True)
    instance_group.add_argument('--compartment_id',
                                help="Compartment OCID",
                                required=False)
    instance_group.add_argument('--compartment_name',
                                help="Compartment Name to search",
                                required=False)
    args = parser.parse_args()
    main(args)
