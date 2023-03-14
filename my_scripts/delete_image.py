import argparse
import os
from oci.regions import REGIONS
from oci_oit_resource.instance import Instance
import oci_oit_resource.common as common


def main(image_args):
    """ Main function that will process the command line options and actions"""
    # Get config
    oci_image_config = common.config_parse(image_args)
    # Create Module instance.
    instance_object = Instance(config=oci_image_config)
    # Delete the image
    instance_object.delete_image(
        image_id=image_args.image_id
    )
    print(f"Image {image_args.image_id} was deleted successfully.")


if __name__ == "__main__":
    env_vars = os.environ
    parser = argparse.ArgumentParser(description="Script to create an image from an instance.")
    # image_config Modifications
    image_config = parser.add_argument_group('image_config Modifications',
                                             'Options used for manipulating image_config')
    image_config.add_argument('--config',
                              help="Path to your image_config file, defaults to $HOME/.oci/config",
                              required=False,
                              default=env_vars['HOME'] + '/.oci/config')
    image_config.add_argument('--region',
                              help="Use if you need to override the region",
                              required=False,
                              choices=REGIONS,
                              metavar='REGION')
    image_config.add_argument('--tenancy',
                              help="Use if you need to override the tenancy",
                              required=False)

    image_d = parser.add_argument_group('Instance Details',
                                        'Options used to attach volume to instance id')
    image_d.add_argument('--image_id',
                         help="OCID of the instance to return status of.",
                         required=True)

    args = parser.parse_args()
    main(args)
