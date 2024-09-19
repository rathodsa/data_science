"""

Name        : experian_pipeline.py
Description : This pipeline will process the ESDD inbound files and Credit/Debit Snapshot data and
              creates a monthly outbound extract to Experian.

"""

import sys
import boto3
import click
import datetime
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as func
from pyspark.sql.types import StructType, StructField, StringType


@click.command
@click.argument('property_file')
@click.argument('process_dt')
def experian_runner(property_file, process_dt):
    main([property_file, process_dt])


# --------------------------------------* main() *---------------------------------#
def main(args):
    try:
        if len(args) < 2:
            raise Exception("Usage: spark-submit <script_name.py> <parameter file> <YYYYMMDD> ")
    except Exception as e:
        raise e

    print(get_datetime(), ": Experian Pipeline is started.\n")

    properties_file, process_dt = args[0], args[1]
    properties_file_list = properties_file.split("/", 3)
    code_bucket = properties_file_list[2]
    property_key = properties_file_list[3]

    # Parse Parameter file:
    param_dict = parseParameterFile(proc_bucket_name=code_bucket, prop_key=property_key)

    # Assign variables:
    inc_bucket_name = param_dict.get("experian.s3path.incoming_bucket_name")
    proc_bucket_name = param_dict.get("experian.s3path.processing_bucket_name")
    incoming_folder = param_dict.get("experian.s3path.incoming_folder")
    proc_folder = param_dict.get("experian.s3path.processing_folder")
    bnk_id = param_dict.get("experian.schema.bnk_id")
    cr_cust_extr_snpst = param_dict.get("experian.s3path.cr_cust_extr_snpst")
    dr_cust_extr_snpst = param_dict.get("experian.s3path.dr_cust_extr_snpst")
    out_bucket_name = param_dict.get("experian.s3path.outgoing_bucket_name")
    outgoing_folder_path = param_dict.get("experian.s3path.outgoing_folder")

    # Clear processing bucket:
    delete_all_files_s3(proc_bucket_name, proc_folder)
    print(get_datetime(), ": All files in processing bucket are deleted")

    # Clear outbound bucket:
    delete_all_files_s3(out_bucket_name, outgoing_folder_path)
    print(get_datetime(), ": All files in outbound bucket are deleted")

    output_fields = [
        "firstname", "lastname", "addr_line1_tx", "addr_line2_tx", "city_tx", "state_cd", "pst_area_cd",
        "bnk_id", "parnt_cust_id"
    ]

    output_file_path = f's3://{out_bucket_name}/{outgoing_folder_path}'

    cr_schema = StructType([StructField("src_cust_id", StringType(), True),
                            StructField("acct_ref_nb", StringType(), True),
                            StructField("acct_nb", StringType(), True),
                            StructField("rel_cd", StringType(), True),
                            StructField("entp_prty_id", StringType(), True),
                            StructField("acct_id", StringType(), True),
                            StructField("pst_cd", StringType(), True),
                            StructField("src_acct_id", StringType(), True),
                            StructField("parnt_cust_id", StringType(), True),
                            StructField("acct_orgn_cd", StringType(), True),
                            StructField("acct_orgn_desc_tx", StringType(), True),
                            StructField("rwrd_prod_cd", StringType(), True),
                            StructField("rwrd_prod_desc_tx", StringType(), True),
                            StructField("prtfl_id", StringType(), True),
                            StructField("prtfl_nm", StringType(), True),
                            StructField("bus_entp_prty_id", StringType(), True),
                            StructField("cust_acct_own_type_cd", StringType(), True),
                            StructField("etl_acct_opn_dt", StringType(), True),
                            StructField("cre_ts", StringType(), True),
                            StructField("rwrd_acct_nb", StringType(), True)
                            ])

    dr_schema = StructType([StructField("src_cust_id", StringType(), True),
                            StructField("bnk_id", StringType(), True),
                            StructField("acct_nb", StringType(), True),
                            StructField("rel_cd", StringType(), True),
                            StructField("sub_prod_cd", StringType(), True),
                            StructField("entp_prty_id", StringType(), True),
                            StructField("acct_id", StringType(), True),
                            StructField("pst_cd", StringType(), True),
                            StructField("src_acct_id", StringType(), True),
                            StructField("parnt_cust_id", StringType(), True),
                            StructField("acct_type_cd", StringType(), True),
                            StructField("prtfl_id", StringType(), True),
                            StructField("prtfl_nm", StringType(), True),
                            StructField("bus_entp_prty_id", StringType(), True),
                            StructField("cust_acct_own_type_cd", StringType(), True),
                            StructField("etl_acct_opn_dt", StringType(), True),
                            StructField("cre_ts", StringType(), True)
                            ])

    # Call function to parse inbound schemas:
    schema_cust = parseInboundSchema(param_dict, "experian.schema.cust")
    schema_name = parseInboundSchema(param_dict, "experian.schema.name")
    schema_addr = parseInboundSchema(param_dict, "experian.schema.addr")
    schema_addr_usg = parseInboundSchema(param_dict, "experian.schema.addr_usg")

    # Move incoming files from incoming to processing bucket:
    proc_bucket_name, proc_folder = moveIncomingFiles(inc_bucket_name, proc_bucket_name, incoming_folder, proc_folder,
                                                      process_dt)

    # Initialize Spark session
    spark = SparkSession.builder.config("spark.driver.memory", "15g").getOrCreate()

    # Extract incoming file paths:
    cust_file, name_file, addr_file, addr_usg_file = extractIncomingFiles(proc_bucket_name, proc_folder)

    # Load incoming files:
    df_cust, df_name, df_addr, df_addr_usg = loadIncomingFiles(spark, cust_file, name_file, addr_file, addr_usg_file)

    # Apply Filter condition on the incoming data:
    df_cust_fltr = filterInboundData(df_cust, schema_cust, "cust_tp", "I")
    df_name_fltr = filterInboundData(df_name, schema_name, "primary_nm_ind", "Y")
    df_addr_fltr = filterInboundData(df_addr, schema_addr, "addr_tp", "C")
    df_addr_usg_fltr = filterInboundData(df_addr_usg, schema_addr_usg, "exp_dt", "12/31/9999")

    # Generate Credit Debit Snapshot Data:
    df_cr_snpst_raw = spark.read.format("orc").schema(cr_schema).load(cr_cust_extr_snpst)
    df_dr_snpst_raw = spark.read.format("orc").schema(dr_schema).load(dr_cust_extr_snpst)

    df_cr_dr_snpst = genCreditDebitData(spark, df_cr_snpst_raw, df_dr_snpst_raw)

    # Generate customer dataframe:
    df_cust_output = genCustData(bnk_id, df_cr_dr_snpst, df_cust_fltr, df_name_fltr, df_addr_fltr, df_addr_usg_fltr,
                                 output_fields)

    # Generate the outbound data:
    df_cust_output, out_bucket_name, s3_bucket = genOutboundData(df_cust_output, out_bucket_name, output_fields)

    # Generate the outbound extract:
    genOutboundExtract(df_cust_output, output_file_path, out_bucket_name, outgoing_folder_path, process_dt)

    # Delete files in Processing bucket:
    delete_all_files_s3(proc_bucket_name, proc_folder)

    # Stop the spark session
    spark.stop()


# --------------------------------------* parseParameterFile() *---------------------------------#

def parseParameterFile(proc_bucket_name, prop_key):
    print(get_datetime(), ": Parsing the Parameter File..........")
    file_content = get_file_content(bucket_name=proc_bucket_name, object_key=prop_key)
    param_dict = transform_to_dict(file_content)
    print(get_datetime(), ": Parameter File is successfully parsed.\n")
    return param_dict


# --------------------------------------* parseInboundSchema() *---------------------------------#

def parseInboundSchema(param_dict, schema_type):
    print(get_datetime(), ": Parsing inbound schemas for ", schema_type)
    return [value for key, value in param_dict.items() if key.startswith(schema_type)]


# --------------------------------------* moveIncomingFiles() *---------------------------------#

def moveIncomingFiles(inc_bucket_name, proc_bucket_name, incoming_folder, proc_folder, process_dt):
    incoming_files = extract_files_from_bucket(bucket_name=inc_bucket_name, folder_path=incoming_folder)
    incoming_files = list(filter(None, incoming_files))

    if not incoming_files:
        raise Exception(f'No incoming files found in path: {incoming_folder}')

    unprocessed_keys = get_unprocessed_file_keys(bucket_name=inc_bucket_name, folder_path=incoming_folder)

    if not unprocessed_keys:
        raise Exception(f'No unprocessed files found in path: {incoming_folder}')
    print(get_datetime(), ": Move files from Incoming to Processing bucket\n")

    for file_key in unprocessed_keys:
        if process_dt in file_key:
            source_file = file_key
            dest_file = f'{proc_folder}/{source_file.split("/")[-1]}'
            copy_s3(inc_bucket_name, proc_bucket_name, source_file, dest_file)
            print(dest_file, "moved to Processing bucket")

    return proc_bucket_name, proc_folder


# --------------------------------------* extractIncomingFiles() *---------------------------------#
def extractIncomingFiles(proc_bucket_name, proc_folder):
    print(get_datetime(), ": Processing the files in processing folder.......\n")

    files_in_s3 = extract_files_from_bucket(bucket_name=proc_bucket_name, folder_path=proc_folder)

    # Store the inbound file names in a list
    files_in_s3 = list(filter(None, files_in_s3))

    # Get the inbound file names:
    cust_files = filter_s3_files_by_string(file_string="cust_full_2", files=files_in_s3)
    name_files = filter_s3_files_by_string(file_string="name_full_2", files=files_in_s3)
    addr_files = filter_s3_files_by_string(file_string="address_full_2", files=files_in_s3)
    addr_usg_files = filter_s3_files_by_string(file_string="addr_usg_full_2", files=files_in_s3)

    cust_file_path = get_bucket_path(bucket_name=proc_bucket_name, folder=proc_folder, file=cust_files[0])
    name_file_path = get_bucket_path(bucket_name=proc_bucket_name, folder=proc_folder, file=name_files[0])
    addr_file_path = get_bucket_path(bucket_name=proc_bucket_name, folder=proc_folder, file=addr_files[0])
    addr_usg_file_path = get_bucket_path(bucket_name=proc_bucket_name, folder=proc_folder, file=addr_usg_files[0])

    return cust_file_path, name_file_path, addr_file_path, addr_usg_file_path


# --------------------------------------* loadIncomingFiles() *---------------------------------#
def loadIncomingFiles(spark, cust_file_path, name_file_path, addr_file_path, addr_usg_file_path):
    print(get_datetime(), ": Load the files in processing bucket into dataframes.")

    df_cust = spark.read.option("header", "false").csv(cust_file_path)

    df_name = spark.read.option("header", "false").csv(name_file_path)

    df_addr = spark.read.option("header", "false").csv(addr_file_path)

    df_addr_usg = spark.read.option("header", "false").csv(addr_usg_file_path)

    return df_cust, df_name, df_addr, df_addr_usg


# --------------------------------------* filterInboundData() *---------------------------------#

def filterInboundData(df_input, schema, fltr_col, fltr_cond):
    print(get_datetime(), ": Apply filter on the inbound data :", fltr_col, " = ", fltr_cond)
    for i in range(0, len(schema), 3):
        df_input = df_input.withColumn(schema[i], func.col("_c0").substr(int(schema[i + 1]), int(schema[i + 2])))

    df_input = df_input.drop("_c0")
    df_input_filtered = df_input.filter(func.trim(func.col(fltr_col)) == fltr_cond)

    return df_input_filtered


# --------------------------------------* genCreditDebitData() *---------------------------------#
def genCreditDebitData(spark, df_cr_snpst_raw, df_dr_snpst_raw):
    # Creating Credit /Debit dataframe
    print(get_datetime(), ": Reading Credit Debit Snapshot data...........")

    df_cr_snpst = df_cr_snpst_raw.select("entp_prty_id", "parnt_cust_id")
    df_dr_snpst = df_dr_snpst_raw.select("entp_prty_id", "parnt_cust_id")
    df_cr_dr_snpst = df_cr_snpst.union(df_dr_snpst).distinct()

    return df_cr_dr_snpst.persist()


# --------------------------------------* genCustData() *---------------------------------#

def genCustData(bnk_id, df_cr_dr_snpst, df_cust_fltr, df_name_fltr, df_addr_fltr, df_addr_usg_fltr, output_fields):
    # Joining Customer and Name dataframes
    print(get_datetime(), ": Joining Customer and Name dataframes")
    df_customerName = df_cust_fltr.join(df_name_fltr, ["eci"])

    # Joining Address and Address Usage
    print(get_datetime(), ": Joining Address and Address Usage")
    df_customerAddress = df_addr_fltr.join(df_addr_usg_fltr, ["eci"])

    # Creating the Customer Data dataframe
    print(get_datetime(), ": Create customer core dataframe")
    df_customerData = df_customerName.join(df_customerAddress, ["eci"])
    # print(get_datetime(), ": df_customerData count = ", df_customerData.count(), "\n")

    # Joining with Credit/Debit Snapshot
    print(get_datetime(), ": Joining Customer Core data with credit debit data")
    df_cust_crdr = df_customerData.join(df_cr_dr_snpst, df_customerData.eci == df_cr_dr_snpst.entp_prty_id)

    # Ordering the Customer Data dataframe
    print(get_datetime(), ": set bnk_id")
    df_cust_bnk_id = df_cust_crdr.withColumn("bnk_id", func.lit(bnk_id))

    print(get_datetime(), ": select all columns")
    df_cust_fields = df_cust_bnk_id.select(output_fields)

    # Trim all the columns in the output dataframe:
    print(get_datetime(), ": trim all columns")
    df_cust_output = trim_all_columns_in_df(df=df_cust_fields)

    return df_cust_output


# --------------------------------------* genOutboundData() *---------------------------------#

def genOutboundData(df_cust_output, out_bucket_name, output_fields):
    s3_resource = boto3.resource('s3')
    s3_bucket = s3_resource.Bucket(out_bucket_name)

    # Writing the Customer Data into dataframe:
    df_cust_output = df_cust_output.withColumn("experian_data", func.concat_ws("|", *df_cust_output.columns))
    df_cust_output = df_cust_output.drop(*output_fields)

    # Remove duplicate records
    df_cust_output_distinct = df_cust_output.distinct()

    return df_cust_output_distinct, out_bucket_name, s3_bucket


# --------------------------------------* genOutboundExtract() *---------------------------------#
def genOutboundExtract(df_cust_output, output_file_path, out_bucket_name, outgoing_folder_path, process_dt):
    # Reduce the number of partitions to one:
    df_cust_output = df_cust_output.coalesce(1).persist()

    # write data to outgoing folder
    print(get_datetime(), ": Writing data into outbound file")
    write_df_to_path(df_cust_output, output_file_path)

    # Get file names in outbound bucket
    file_keys = get_unprocessed_file_keys(bucket_name=out_bucket_name, folder_path=outgoing_folder_path)

    # Rename the outbound file
    for file_key in file_keys:
        source_name = file_key
        dest_name = f'{outgoing_folder_path}/experian_{process_dt}.txt'
        move_s3(out_bucket_name, out_bucket_name, source_name, dest_name)
        print(get_datetime(), ": Outbound file is created - ", dest_name)


# --------------------------------------* move_s3() *---------------------------------#


def move_s3(src_bucket_nm, dest_bucket_nm, source_nm, dest_nm):
    # Copy the file to a new name
    copy_s3(src_bucket_nm, dest_bucket_nm, source_nm, dest_nm)

    # Delete the outbound file with old name
    s3_resource = boto3.resource('s3')
    s3_resource.Object(src_bucket_nm, source_nm).delete()


# --------------------------------------* copy_s3 *------------------------#
def copy_s3(src_bucket_nm, dest_bucket_nm, source_nm, dest_nm):
    s3_resource = boto3.resource('s3')
    copy_source = {'Bucket': src_bucket_nm, 'Key': source_nm}
    bucket = s3_resource.Bucket(dest_bucket_nm)
    obj = bucket.Object(dest_nm)
    obj.copy(copy_source)


# --------------------------------------* delete_all_files_s3() *---------------------------------#

def delete_all_files_s3(proc_bucket_name, proc_folder):
    s3_objects = get_s3objects(proc_bucket_name, proc_folder)
    for obj in s3_objects:
        obj.delete()



# -------------------------------------* Helpers *---------------------------------#


def extract_files_from_bucket(bucket_name: str, folder_path: str):
    files = [file.key.split(f"{folder_path}/")[1] for file in get_s3objects(bucket_name, folder_path)]
    return files


def get_s3objects(bucket_name: str, folder_path: str):
    s3_resource = boto3.resource('s3')
    s3_bucket = s3_resource.Bucket(bucket_name)
    s3_objects = s3_bucket.objects.filter(Prefix=folder_path)
    return s3_objects


def get_file_content(bucket_name: str, object_key: str):
    s3_client = boto3.client('s3')
    s3_response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    file_content = s3_response['Body'].read().decode('utf-8')
    return file_content


def transform_to_dict(file_content):
    param_dict = {}
    for line in file_content.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            key, value = line.split(" = ")
            param_dict[key] = value
    return param_dict


def get_unprocessed_file_keys(bucket_name: str, folder_path: str):
    s3_objs = get_s3objects(bucket_name=bucket_name, folder_path=folder_path)
    return [file.key
            for file in s3_objs
            if '_SUCCESS' not in file.key]


def filter_s3_files_by_string(file_string: str, files: list):
    return [s3_file for s3_file in files if file_string in s3_file]


def get_bucket_path(bucket_name: str, folder: str, file: str):
    return f's3://{bucket_name}/{folder}/{file}'


def trim_all_columns_in_df(df: DataFrame):
    # Trim all the columns in the output dataframe:
    for c_name in df.columns:
        df = df.withColumn(c_name, func.trim(func.col(c_name)))
    return df


def write_df_to_path(df: DataFrame, path: str):
    df.write.mode("overwrite").text(path)


def print_dict(dict_to_print: dict):
    for key, value in dict_to_print.items():
        print(f"{key}: {value}")


def get_datetime():
    current_time = datetime.datetime.now()
    return current_time


# -------------------------------------* module *---------------------------------#

if __name__ == "__main__":
    main(sys.argv[1:])

# --------------------------------------* END *---------------------------------#
