from oci.regions import REGIONS


def get_compartment(args, oci_config):
    """ Get compartment

        Args:
            args -- Parsed parsed_args
            oci_config -- OCI Config object

        Returns:
            str: Compartment OCID
    """
    if args.compartment_id:
        compartment = args.compartment_id
    # Otherwise use tenancy
    else:
        compartment = oci_config['tenancy']
    return compartment


def list_compartment_options(args, oci_config, compartment_object):
    """ Compartment Options

        Args:
            args -- Parsed parsed_args
            oci_config -- OCI Config object
            compartment_object -- Compartment object

        Returns:
            None: Prints output to STDOUT
    """
    # Define the compartment, either provided or root compartment
    compartment = get_compartment(args, oci_config)
    if args.list_regions:
        print("Available regions:")
        for region in REGIONS:
            print(region)
    # If we have a list compartments command, print all compartments
    if args.list_compartments:
        compartments = compartment_object.list_compartments()
        print("Available Compartments")
        for comp in compartments:
            print(f"Name: {comp.name}")
            print(f"Description: {comp.description}")
            print(f"ID: {comp.id}\n")
    if args.list_availability_domains:
        ads = compartment_object.list_ads(compartment)
        print("Available ADs")
        for a_d in ads:
            print(f"Name: {a_d.name}")


def list_vcn_options(args, oci_config, vcn_object):
    """ VCN Options

        Args:
            args -- Parsed parsed_args
            oci_config -- OCI Config object
            vcn_object -- VCN object

        Returns:
            None: Prints output to STDOUT
    """
    compartment = get_compartment(args, oci_config)
    if args.list_vcns:
        vcns = vcn_object.list_vcns(compartment)
        print("Available VCNS in Compartment")
        for vcn in vcns:
            print(f"Name: {vcn.display_name}")
            print(f"Cidr: {vcn.cidr_block}")
            print(f"VCN ID: {vcn.id}\n")
    if args.list_subnets:
        subnets = vcn_object.list_subnets(compartment, args.vcn_id)
        print("Available subnets")
        for subnet in subnets:
            print(f"Name: {subnet.display_name}")
            print(f"CIDR Block: {subnet.cidr_block}")
            print(f"Subnet ID: {subnet.id}")
            print(f"VCN ID: {subnet.vcn_id}\n")


def list_str(values):
    """ Convert strings to list

        Args:
            values -- common seperated list of strings

        Returns:
            list: List created from comma seperated values
    """
    return values.split(',')


def create_config_group(parser_object):
    """ Create argparse config group for use in multiple scripts

        Args:
            parser_object (object): Argparse parser object.

        Returns:
            object: parser argument group.
    """
    config_group = parser_object.add_argument_group('Config Modifications',
                                                    'Options used for manipulating config')
    config_group.add_argument('--user',
                              help="User OCID.",
                              required=True)
    config_group.add_argument('--fingerprint',
                              help="User Fingerprint.",
                              required=True)
    config_group.add_argument('--region',
                              help="Region to use.",
                              required=True,
                              choices=REGIONS)
    config_group.add_argument('--tenancy',
                              help="Tenancy to use.",
                              required=False)
    config_group.add_argument('--key_file',
                              help="File path to user key_file for authentication",
                              required=True)
    return config_group
