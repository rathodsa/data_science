#!env python3
import sys
import os
PROG_PATH = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
sys.path.append(PROG_PATH)
import argparse
from oci_oit_resource import common
from oci_oit_resource.instance import Instance
import examples.arg_processor as arg_processor


def main(attc_srt_args):
    """ Process options to create config, stop instance and detach it's boot volume

        Args:
            attc_srt_args (parse_args()): Parsed arguments.
    """
    config_dict = common.create_config_dict(attc_srt_args)
    instance_object = Instance(config=config_dict)
    # Attach the boot volume.
    instance_object.attach_boot_volume(
        instance_id=attc_srt_args.instance_id,
        boot_vol_id=attc_srt_args.boot_vol_id
    )
    # Start intance
    instance_object.update_instance_state(
        instance_id=attc_srt_args.instance_id,
        action="START"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to stop instance and detach boot volume")
    # Config Modifications
    config_group = arg_processor.create_config_group(parser)

    attc_srt_group = parser.add_argument_group('Instance Details',
                                               'Options used to start instance and attach boot volume')
    attc_srt_group.add_argument('--instance_id',
                                help="OCID of the instance to return status of.",
                                required=True)
    attc_srt_group.add_argument('--boot_vol_id',
                                help="Boot Volume OCID.",
                                required=False)

    args = parser.parse_args()
    main(args)
