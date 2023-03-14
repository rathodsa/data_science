#!env python3
import sys
import os
PROG_PATH = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
sys.path.append(PROG_PATH)
import argparse
import examples.arg_processor as arg_processor
from oci_oit_resource import common
from oci_oit_resource.instance import Instance


def main(inst_bvs_args):
    """ Process options to create config, stop instance and detach it's boot volume

        Args:
            inst_bvs_args (parse_args()): Parsed arguments.
    """
    config_dict = common.create_config_dict(inst_bvs_args)
    instance_object = Instance(config=config_dict)
    compartment_id = arg_processor.get_compartment(inst_bvs_args, config_dict)
    instance_details = instance_object.get_bootvolumes_from_ocid(
        instance_id=inst_bvs_args.instance_id,
        compartment_id=compartment_id,
        availability_domain=inst_bvs_args.ad
    )
    response = []
    for instance in instance_details:
        response.append(instance.id)
    boot_volume = response[0]
    # Stop intance
    instance_object.update_instance_state(
        instance_id=inst_bvs_args.instance_id,
        action="SOFTSTOP"
    )
    # Detach boot volume
    instance_object.detach_bootvolume(
        boot_volume=boot_volume
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to stop instance and detach boot volume")
    # Config Modifications
    config_group = arg_processor.create_config_group(parser)

    inst_bvs_group = parser.add_argument_group('Instance Details',
                                               'Options used to stop instance and detach boot volume')
    inst_bvs_group.add_argument('--instance_id',
                                help="OCID of the instance to return status of."
                                     " Requires either --compartment_id or --compartment_name",
                                required=True)
    inst_bvs_group.add_argument('--compartment_id',
                                help="Compartment OCID, if not supplied we default to tenancy",
                                required=False)
    inst_bvs_group.add_argument('--ad',
                                help="Availability Domain to search",
                                required=True)
    args = parser.parse_args()
    main(args)
