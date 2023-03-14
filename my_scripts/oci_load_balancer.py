#!/usr/bin/python3
""" Script for creating and terminating lbs """
import argparse
import json
import os
import sys
# from threading import Thread
import yaml
from yaml import Loader
from oci.regions import REGIONS
import arg_processor
from oci_oit_resource.lbas import LB
from oci_oit_resource.compartment import Compartment
from oci_oit_resource.vcn import VCN
import oci_oit_resource.common as common


def list_lb_options(lb_args, oci_config, lb_object):
    """ Function to list LB parameters """
    compartment = arg_processor.get_compartment(lb_args, oci_config)
    if lb_args.list:
        lbs = lb_object.list(compartment_id=compartment)
        for l_b in lbs:
            print(f"Name: {l_b.display_name}")
            print(f"OCID: {l_b.id}")
    if lb_args.list_shapes:
        lb_shapes = lb_object.list_shapes(compartment_id=compartment)
        print("Load Balancer Shapes:")
        for lb_shape in lb_shapes:
            print(f"Name: {lb_shape.name}")  # Debug
    if lb_args.list_policies:
        lb_policies = lb_object.list_policies(compartment_id=compartment)
        print("Load Balancer Policies")
        for policy in lb_policies:
            print(f"Name: {policy.name}")
    if lb_args.list_protocols:
        lb_protocols = lb_object.list_protocols(compartment_id=compartment)
        print("Load Balancer Protocols")
        for protocol in lb_protocols:
            print(f"Name: {protocol.name}")


def main():
    """ Main function that will process the command line options and actions"""
    lb_args = parser.parse_args()
    # Define the config_file
    oci_config = common.config_parse(lb_args)
    if lb_args.show_config:
        print(json.dumps(oci_config, indent=4, sort_keys=True))
    # Setup Module lbs.
    compartment_object = Compartment(config=oci_config)
    vcn_object = VCN(config=oci_config)
    lb_object = LB(config=oci_config)
    # Run the options sub methods.
    arg_processor.list_compartment_options(lb_args, oci_config, compartment_object)
    arg_processor.list_vcn_options(lb_args, oci_config, vcn_object)
    list_lb_options(lb_args, oci_config, lb_object)
    # If create_new was sent.
    if lb_args.create_new:
        # Check that we got the parameters we require to create an instance
        if not lb_args.json_file and not lb_args.yaml_file and not lb_args.lb_name:
            sys.exit("ERROR: You did not specify instance parameters please use"
                     " --json_file, --yaml_file or --lb_name")
        # If a json file was sent parse it into a list of dictionaries.
        if lb_args.json_file:
            print("Parsing JSON File")
            with open(lb_args.json_file) as json_file_content:
                lb_details = json.load(json_file_content)
        # If a yaml file was sent parse it into a list of dictionaries.
        elif lb_args.yaml_file:
            print("Parsing YAML File")
            with open(lb_args.yaml_file) as yaml_file_content:
                lb_details = yaml.load(yaml_file_content, Loader)
        # Create with json or yaml
        if lb_args.json_file or lb_args.yaml_file:
            # Process create
            for lb_detail in lb_details:
                lb_detail['lb_object'] = lb_object
                lb_detail['vcn_object'] = vcn_object
                lb_create_response = lb_object.create(**lb_detail)
                print(f"Name: {lb_create_response.display_name}")
                print(f"ID: {lb_create_response.id}")
        # Create with command lines options
        else:
            # Process create
            print(lb_args)
    if lb_args.terminate:
        if lb_args.lb_ids:
            for lb_id in lb_args.lb_ids:
                delete_response = lb_object.delete(lb_id=lb_id)
                print(delete_response.lifecycle_state)


if __name__ == "__main__":
    env_vars = os.environ
    parser = argparse.ArgumentParser(description=""" Script that can be used to
                                     create new, list existing, and delete
                                     OCI load balancers""")
    # Config Modifications
    lb_config_group = parser.add_argument_group('Config Modifications',
                                                'Options used for manipulating config')
    lb_config_group.add_argument('--config',
                                 help="Path to your config file, defaults to $HOME/.oci/config",
                                 required=False,
                                 default=env_vars['HOME'] + '/.oci/config')
    lb_config_group.add_argument('--show_config',
                                 help="Show JSON output of configuration", required=False,
                                 default=None,
                                 action='store_true')
    lb_config_group.add_argument('--region',
                                 help="Use if you need to override the region",
                                 required=False,
                                 choices=REGIONS,
                                 metavar='REGION')
    lb_config_group.add_argument('--tenancy',
                                 help="Use if you need to override the tenancy",
                                 required=False)
    # List objects
    lb_list_group = parser.add_argument_group('List objects', 'Options used to list objects in OCI')
    lb_list_group.add_argument('--list_regions',
                               help='Option to list available regions',
                               required=False,
                               default=None,
                               action='store_true')
    lb_list_group.add_argument('--list_compartments',
                               help="Option to list available compartments",
                               default=None,
                               action='store_true')
    lb_list_group.add_argument('--list_availability_domains',
                               help="Option to list availability domains in compartment",
                               default=None,
                               action='store_true')
    lb_list_group.add_argument('--list_vcns',
                               help="Option to list available VCNs in a compartment, "
                                    "it's recommended to use this with --compartment_id",
                               default=None,
                               action='store_true')
    lb_list_group.add_argument('--list_subnets',
                               help='Option to list all subnets in compartment/vcn',
                               default=None,
                               action='store_true')
    lb_list_group.add_argument('--list_shapes',
                               help="Option to list available shapes",
                               required=False,
                               default=None,
                               action='store_true')
    lb_list_group.add_argument('--list_policies',
                               help='Option to list LB policies in a compartment',
                               default=None,
                               action='store_true')
    lb_list_group.add_argument('--list_protocols',
                               help="Option to list LB protocols in a compartment",
                               default=None,
                               action='store_true')
    # Actions
    lb_action_group = parser.add_argument_group('Actions', 'Options that specify an action')
    lb_action_group.add_argument('--create_new',
                                 help="Create new lb",
                                 required=False,
                                 default=None,
                                 action='store_true')
    lb_action_group.add_argument('--terminate',
                                 help="Terminate lb",
                                 required=False,
                                 default=None,
                                 action='store_true')
    lb_action_group.add_argument('--list',
                                 help="List LBS",
                                 required=False,
                                 default=None,
                                 action='store_true')
    # Action Options
    lb_action_option_group = parser.add_argument_group('Options for Actions',
                                                       'Options to be used with an action')
    lb_action_option_group.add_argument('--lb_ids',
                                        help="lb ID (used with --terminate) ex."
                                        "test1,test2,test3",
                                        required=False,
                                        type=arg_processor.list_str)
    lb_action_option_group.add_argument('--json_file',
                                        help="JSON file with lb parameters, see README.md",
                                        required=False)
    lb_action_option_group.add_argument('--yaml_file',
                                        help="YAML file with lb parameters, see README.md",
                                        required=False)
    lb_action_option_group.add_argument('--compartment_id',
                                        help="Use to supply the compartmentid for the lb",
                                        required=False)
    main()
