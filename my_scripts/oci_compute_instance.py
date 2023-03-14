#!/usr/bin/python3
""" Script for creating and terminating instances """
import argparse
import os
import json
import sys
from threading import Thread
import yaml
from yaml import Loader
from oci.regions import REGIONS
import arg_processor
from oci_oit_resource.block_storage import BlockStorage
from oci_oit_resource.instance import Instance
from oci_oit_resource.compartment import Compartment
from oci_oit_resource.vcn import VCN
import oci_oit_resource.common as common


def process_file(args):
    # If a json file was sent parse it into a list of dictionaries.
    if args.json_file:
        print("Parsing JSON File")
        with open(args.json_file) as json_file_content:
            instance_details = json.load(json_file_content)
    # If a yaml file was sent parse it into a list of dictionaries.
    elif args.yaml_file:
        print("Parsing YAML File")
        with open(args.yaml_file) as yaml_file_content:
            instance_details = yaml.load(yaml_file_content, Loader)
    else:
        sys.exit("Didn't find a file.")
    return instance_details


def process_instance(instance):
    if "region" in instance.keys():
        temp_oci_config = instance['config']
        temp_oci_config['region'] = instance['region']
        temp_vcn_object = VCN(config=temp_oci_config)
        temp_instance_object = Instance(config=temp_oci_config)
        temp_compart_object = Compartment(config=temp_oci_config)
        instance['instance_object'] = temp_instance_object
        instance['vcn_object'] = temp_vcn_object
        instance['compartment_object'] = temp_compart_object
        instance['config'] = temp_oci_config

    instance['ssh_key_file'] = instance['instance_object'].process_ssh_key(
        ssh_key_file=instance['ssh_key_file']
    )

    print(f"Creating Instance {instance['instance_name']}")

    if instance['check']:
        # Get list of instances
        if existing_check(instance['instance_name'], instance['compartment_id'], instance['instance_object']):
            print(f"Instance {instance['instance_name']} exists, skipping...")
        else:
            thread = Thread(target=create_instance, kwargs=instance)
            thread.start()
    else:
        # Define the thread
        thread = Thread(target=create_instance, kwargs=instance)
        # Start the thread
        thread.start()


def process_block(**kwargs):
    # print(kwargs)
    if "free_form_tags" not in kwargs['block'].keys():
        kwargs['block']['free_form_tags'] = None
    if "device_name" not in kwargs['block'].keys():
        kwargs['block']["device_name"] = None
    if "is_sharable" not in kwargs['block'].keys():
        kwargs['block']["is_sharable"] = False
    block_id = kwargs['block_object'].create_block_volume(
        compartment_id=kwargs.get('compartment_id'),
        availability_domain=kwargs.get("availability_domain"),
        block_vol_name=kwargs['block']['block_vol_name'],
        size_in_gbs=kwargs['block']['size_in_gbs'],
        free_form_tags=kwargs['block']['free_form_tags'],
        device=kwargs['block']["device_name"],
        is_sharable=kwargs['block']["is_sharable"]
    ).id
    return block_id


def existing_check(instance_name, compartment_id, instance_object):
    instances = instance_object.list_instances(compartment_id=compartment_id)
    temp_instances = []
    for temp_instance in instances:
        if temp_instance.lifecycle_state == "RUNNING":
            temp_instances.append(temp_instance.display_name)
    value = instance_name in temp_instances
    return value


def create_instance(**kwargs):
    """ Create an instance with required kwargs
        Keyword Arguments
            instance_object -- Instance object
            vcn_object -- VCN object
            instance_name -- Name of instances
            compartment_id -- Compartment ID
            availability_domain -- Availability domain
            vcn_id -- VCN id
            subnet_id -- Subnet id
            image_id -- Image id
            shape -- shape
            ssh_key_file -- SSH Key
            user_data_file -- UserData File
    """
    print(kwargs['instance_name'])
    if "user_data_file" not in kwargs.keys():
        kwargs['user_data_file'] = None
    private_ips = []
    public_ips = []
    if (str(kwargs['availability_domain']) in ["1", "2", "3"]):
        ad_list = kwargs['compartment_object'].list_ads(kwargs['compartment_id'])
        for avail_domain in ad_list:
            if avail_domain.name[-1] == str(kwargs['availability_domain']):
                kwargs['availability_domain'] = avail_domain.name
    instance = kwargs['instance_object'].create_instance(**kwargs)
    return_text = f"Name: {instance.display_name}\n"
    return_text += f"ID: {instance.id}\n"
    return_text += f"State: {instance.lifecycle_state}\n"
    return_text += "Interface Data:\n"
    if "block" in kwargs.keys():
        volume_id = process_block(**kwargs)
        kwargs['instance_object'].attach_volume(
            instance_id=instance.id,
            vol_id=volume_id,
            device_type=kwargs['block']['type']
        )
    vnics = kwargs['instance_object'].get_vnics(
        compartment_id=kwargs['compartment_id'],
        instance_id=instance.id
    )
    for vnic in vnics:
        vnic_data = kwargs['vcn_object'].get_vnic(vnic.vnic_id)
        return_text += f"\tPrivate IP: {vnic_data.private_ip}\n"
        private_ips.append(vnic_data.private_ip)
        if vnic_data.public_ip:
            return_text += f"\tPublic IP: {vnic_data.public_ip}\n"
            public_ips.append(vnic_data.public_ip)
    return_text += "\n"
    if kwargs['write_output']:
        output_file = kwargs['instance_name'] + ".json"
        output = {
            "instance_name": kwargs['instance_name'],
            "instance_id": instance.id,
            "private_ips": private_ips,
            "public_ips": public_ips
        }
        with open(output_file, "w") as outfile:
            json.dump(output, outfile, indent=4)
    print(return_text)


def list_instance_options(args, oci_config, instance_object, vcn_object):
    """ Instance Options """
    compartment = arg_processor.get_compartment(args, oci_config)
    if args.list_shapes:
        shapes = instance_object.list_shapes(compartment_id=compartment)
        print("Available shapes")
        printed_shapes = []
        for shape in shapes:
            if shape.shape.startswith("VM") and shape.shape not in printed_shapes:
                printed_shapes.append(shape.shape)
                print(f"Shape: {shape.shape}")
                print(f"CPU: {shape.ocpus} {shape.processor_description}")
                print(f"Memory: {shape.memory_in_gbs} GB")
                print(f"Local Disk: {shape.local_disks} {shape.local_disks_total_size_in_gbs} GB")
                print(f"Network bandwidth: {shape.networking_bandwidth_in_gbps} gbps\n")
    if args.list_images:
        images = instance_object.list_images(compartment_id=compartment)
        print("Available images")
        for image in images:
            print(f"Image Name: {image.display_name}")
            print(f"Disk Size: {image.size_in_mbs} MB")
            print(f"ID: {image.id}\n")
    if args.list:
        print("Instances in compartment")
        instances = instance_object.list_instances(compartment_id=compartment)
        for instance in instances:
            print(f"Name: {instance.display_name}")
            print(f"ID: {instance.id}")
            print(f"State: {instance.lifecycle_state}")
            print("Interface Data:")
            vnics = instance_object.get_vnics(
                compartment_id=compartment,
                instance_id=instance.id
            )
            for vnic in vnics:
                vnic_data = vcn_object.get_vnic(vnic.vnic_id)
                print(f"Private IP: {vnic_data.private_ip}")
                if vnic_data.public_ip:
                    print(f"Public IP: {vnic_data.public_ip}")
            print("\n")


def process_args(parsed_args):
    """ Function to proces arguments for command line created instance """
    if parsed_args.user_data_file:
        user_data = parsed_args.user_data_file
    else:
        user_data = None
    if parsed_args.ocpus:
        # print(parsed_args.ocpus)
        ocpus = float(parsed_args.ocpus)
    else:
        ocpus = None
    if parsed_args.memory:
        memory = float(parsed_args.memory)
    else:
        memory = None
    if parsed_args.nsg_ids:
        nsgs = parsed_args.nsg_ids
    else:
        nsgs = None
    return user_data, ocpus, memory, nsgs


def main():
    """ Main function that will process the command line options and actions"""
    # Parse the arguments.
    args = parser.parse_args()
    # Define the config_file
    oci_config = common.config_parse(args)
    # Setup Module instances.
    compartment_object = Compartment(config=oci_config)
    vcn_object = VCN(config=oci_config)
    instance_object = Instance(config=oci_config)
    block_object = BlockStorage(config=oci_config)
    # Run the options sub methods.
    arg_processor.list_compartment_options(args, oci_config, compartment_object)
    arg_processor.list_vcn_options(args, oci_config, vcn_object)
    list_instance_options(args, oci_config, instance_object, vcn_object)
    # If create_new was sent.
    if args.create_new:
        # Check that we got the parameters we require to create an instance
        if not args.json_file and not args.yaml_file and not args.instance_name:
            sys.exit("ERROR: You did not specify instance parameters please use"
                     " --json_file, --yaml_file or --instance_name")
        # If json or yaml loop the array and start a thread to create each.
        if args.json_file or args.yaml_file:
            instance_details = process_file(args)
            for instance in instance_details:
                instance['instance_object'] = instance_object
                instance['vcn_object'] = vcn_object
                instance['compartment_object'] = compartment_object
                instance['block_object'] = block_object
                instance['config'] = oci_config
                instance['write_output'] = args.write_output
                instance['check'] = args.check_for_existing
                process_instance(instance)
        else:
            ssh_key = instance_object.process_ssh_key(ssh_key_file=args.ssh_public_key)
            user_data, ocpus, memory, nsg_ids = process_args(args)
            if args.check_for_existing:
                # Get list of instances
                if not existing_check(args.instance_name, args.compartment_id, instance_object):
                    create_instance(instance_object=instance_object,
                                    vcn_object=vcn_object,
                                    compartment_object=compartment_object,
                                    block_object=block_object,
                                    instance_name=args.instance_name,
                                    compartment_id=args.compartment_id,
                                    availability_domain=args.availability_domain,
                                    vcn_id=args.vcn_id,
                                    subnet_id=args.subnet_id,
                                    image_id=args.image_id,
                                    shape=args.shape,
                                    ssh_key_file=ssh_key,
                                    ocpus=ocpus,
                                    memory=memory,
                                    nsg_ids=nsg_ids,
                                    user_data_file=user_data)
                else:
                    print(f"Instance {args.instance_name} Exists, skipping...")
            else:
                create_instance(instance_object=instance_object,
                                vcn_object=vcn_object,
                                compartment_object=compartment_object,
                                instance_name=args.instance_name,
                                block_object=block_object,
                                compartment_id=args.compartment_id,
                                availability_domain=args.availability_domain,
                                vcn_id=args.vcn_id,
                                subnet_id=args.subnet_id,
                                image_id=args.image_id,
                                shape=args.shape,
                                ssh_key_file=ssh_key,
                                ocpus=ocpus,
                                memory=memory,
                                nsg_ids=nsg_ids,
                                user_data_file=user_data)

    if args.terminate:
        print("Starting to terminate instance, this will take a few minutes")
        for instance in args.instance_ids:
            print(f"Terminating instance {instance}")
            instance_object.terminate_instance(instance_id=instance)
        print("Finished terminating Instances")


if __name__ == "__main__":
    env_vars = os.environ
    parser = argparse.ArgumentParser(description="""Script that can be used to
                                     create new OCI instances, display current
                                     instances and delete existing
                                     instances.""")
    # Config Modifications
    config_group = parser.add_argument_group('Config Modifications',
                                             'Options used for manipulating config')
    config_group.add_argument('--config',
                              help="Path to your config file, defaults to $HOME/.oci/config",
                              required=False,
                              default=env_vars['HOME'] + '/.oci/config')
    config_group.add_argument('--region',
                              help="Use if you need to override the region",
                              required=False,
                              choices=REGIONS,
                              metavar='REGION')
    config_group.add_argument('--tenancy',
                              help="Use if you need to override the tenancy",
                              required=False)

    # List objects
    list_group = parser.add_argument_group('List objects', 'Options used to list objects in OCI')
    list_group.add_argument('--list_regions',
                            help='Option to list available regions',
                            required=False,
                            default=None,
                            action='store_true')
    list_group.add_argument('--list_compartments',
                            help="Option to list available compartments",
                            default=None,
                            action='store_true')
    list_group.add_argument('--list_availability_domains',
                            help="Option to list availability domains in compartment",
                            default=None,
                            action='store_true')
    list_group.add_argument('--list_vcns',
                            help="""Option to list available VCNs in a compartment,
                            it's recommended to use this with --compartment_id""",
                            default=None,
                            action='store_true')
    list_group.add_argument('--list_subnets',
                            help='Option to list all subnets in compartment/vcn',
                            default=None,
                            action='store_true')
    list_group.add_argument('--list_shapes',
                            help="Option to list available shapes",
                            required=False,
                            default=None,
                            action='store_true')
    list_group.add_argument('--list_images',
                            help="Option list all images in compartment",
                            default=None,
                            action='store_true')
    # Actions
    action_group = parser.add_argument_group('Actions', 'Options that specify an action')
    action_group.add_argument('--create_new',
                              help="Create new instance",
                              required=False,
                              default=None,
                              action='store_true')
    action_group.add_argument('--terminate',
                              help="Terminate instance",
                              required=False,
                              default=None,
                              action='store_true')
    action_group.add_argument('--list',
                              help="List Intances",
                              required=False,
                              default=None,
                              action='store_true')
    action_group.add_argument('--check-for-existing',
                              help="Check for existing instance with same name, and skip if exists.",
                              required=False,
                              default=None,
                              action='store_true')
    # Action Options
    action_option_group = parser.add_argument_group('Options for Actions',
                                                    'Options to be used with an action')
    action_option_group.add_argument('--instance_name',
                                     help="Instance Name (used with --create_new)",
                                     required=False)
    action_option_group.add_argument('--instance_ids',
                                     help="Instance ID (used with --terminate) ex."
                                     "test1,test2,test3",
                                     required=False,
                                     type=arg_processor.list_str)
    action_option_group.add_argument('--json_file',
                                     help="JSON file with instance parameters, see README.md",
                                     required=False)
    action_option_group.add_argument('--yaml_file',
                                     help="YAML file with instance parameters, see README.md",
                                     required=False)
    action_option_group.add_argument('--compartment_id',
                                     help="Use to supply the compartmentid for the instance",
                                     required=False)
    action_option_group.add_argument('--availability_domain',
                                     help="Use to supply availability domain id",
                                     required=False)
    action_option_group.add_argument('--vcn_id',
                                     help="Use to supply the vcn_id for the instance",
                                     required=False)
    action_option_group.add_argument('--nsg_ids',
                                     help="Comma seperated list of Network Security Group OCIDs",
                                     required=False,
                                     default=[None],
                                     type=arg_processor.list_str)
    action_option_group.add_argument('--subnet_id',
                                     help="Use to supply subnet_id for the instance",
                                     required=False)
    action_option_group.add_argument('--image_id',
                                     help='Use to supply image OCID',
                                     required=False)
    action_option_group.add_argument('--shape',
                                     help="Use to supply shape",
                                     required=False)
    action_option_group.add_argument('--ocpus',
                                     help="Use to configure CPU Count for Flex Shape",
                                     required=False)
    action_option_group.add_argument('--memory',
                                     help="Use to configure Memory size for Flex Shape",
                                     required=False)
    action_option_group.add_argument('--ssh_public_key',
                                     help="SSH Public key for instance",
                                     required=False)
    action_option_group.add_argument('--user_data_file',
                                     help="User Data File path, (optional)",
                                     required=False)
    action_option_group.add_argument('--write_output',
                                     help="Write JSON output to file., File name will be instance name.json",
                                     default=False,
                                     action="store_true",
                                     required=False)
    main()
