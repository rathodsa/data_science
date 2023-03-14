import argparse
import os
import json
from oci.regions import REGIONS
from oci_oit_resource.instance import Instance
import oci_oit_resource.common as common


def main(image_args):
    """ Main function that will process the command line options and actions"""
    # Define the config_file
    oci_config = common.config_parse(image_args)
    # Setup Module instance.
    instance_object = Instance(config=oci_config)
    # Create the images
    if image_args.create:
        resp = instance_object.create_image_from_vm(
            instance_id=image_args.instance_id,
            compartment_id=image_args.compartment_id,
            display_name=image_args.display_name
        )
    if image_args.export:
        resp = instance_object.export_image(
            image_id=image_args.image_id,
            bucket_name=image_args.bucket_name,
            namespace_name=image_args.namespace_name,
            object_name=image_args.display_name
        )
    if image_args.import_image:
        resp = instance_object.import_image(
            bucket_name=image_args.bucket_name,
            namespace_name=image_args.namespace_name,
            object_name=image_args.display_name,
            display_name=image_args.display_name,
            operating_system=image_args.operating_system,
            os_version=image_args.os_version
        )
    print(f"Display name: {resp.display_name}")
    print(f"ID: {resp.id}")
    print(f"Created time: {resp.time_created}")
    if image_args.write_output:
        output_file = image_args.display_name + ".json"
        output = {
            "image_name": image_args.display_name,
            "image_id": resp.id,
            "created_at": resp.time_created
        }
        with open(output_file, "w") as outfile:
            json.dump(output, outfile, indent=4)


if __name__ == "__main__":
    env_vars = os.environ
    parser = argparse.ArgumentParser(description="Script to create an image from an instance.")
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

    image = parser.add_argument_group('Instance Details',
                                      'Options used to attach volume to instance id')
    image.add_argument('--instance_id',
                       help="OCID of the instance to return status of.",
                       required=False)
    image.add_argument('--compartment_id',
                       help="OCID of the instances compartment.",
                       required=False)
    image.add_argument('--display_name',
                       help="Display name for the instance you are creating.",
                       required=False)
    image.add_argument('--write_output',
                       help="Write JSON output to file., File name will be instance name.json",
                       default=False,
                       action="store_true",
                       required=False)
    image.add_argument('--create',
                       help="Create image from VM",
                       default=False,
                       action="store_true",
                       required=False)
    image.add_argument('--export',
                       help="Export Image.",
                       default=False,
                       required=False,
                       action="store_true")
    image.add_argument('--import_image',
                       help="Import from ObjectStore",
                       default=False,
                       required=False,
                       action="store_true")
    image.add_argument('--image_id',
                       help="Image OCID",
                       default=None,
                       required=False)
    image.add_argument("--bucket_name",
                       help="Object Store Bucket Name",
                       default=None,
                       required=False)
    image.add_argument('--namespace_name',
                       help="Object Store Namespace Name",
                       default=None,
                       required=False)
    image.add_argument('--operating_system',
                       help="Operating System for import image",
                       default=None,
                       required=False)
    image.add_argument('--os_version',
                       help="Operating System Version for image import",
                       default=None,
                       required=False)
    args = parser.parse_args()
    main(args)
