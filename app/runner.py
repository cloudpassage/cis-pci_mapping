#!/usr/bin/python
import os
import sys

from cispcimapping import config_helper
from cispcimapping import custom_enum
from cispcimapping import excel_handler
from cispcimapping import halo_api_caller
from cispcimapping import utility


def main():
    utility.Utility.log_stdout("Mapping Script Started ...")
    config = config_helper.ConfigHelper()
    halo_api_caller_obj = halo_api_caller.HaloAPICaller(config)
    mapping_type = config.mapping_type
    utility.Utility.log_stdout("1- Creating HALO API CALLER Object.")

    """
    First we make sure that all configs are sound...
    """
    utility.Utility.log_stdout("2- Checking the provided configuration parameters")
    check_configs(config, halo_api_caller_obj)

    """
    Retrieving list of configuration policies
    """
    utility.Utility.log_stdout("3- Retrieving list of configuration policies")
    csm_plc_lst = halo_api_caller_obj.get_configuration_policy_list()

    """
    Extract Configuration Policy ID using the provided policy name
    """
    utility.Utility.log_stdout("4- Extract Configuration Policy ID using the provided policy name")
    policy_name = halo_api_caller_obj.target_policy_name
    target_policy_id = halo_api_caller_obj.extract_policy_from_policy_list(csm_plc_lst, policy_name)

    """
    Retrieving target configuration policy details
    """
    utility.Utility.log_stdout("5- Retrieving target configuration policy details")
    csm_plc_det = halo_api_caller_obj.get_configuration_policy_details(target_policy_id)

    """
    Parsing the mapping document/sheet and creating list of rules having PCI/HIPAA/NIST mapping info and ignore rules with no PCI/HIPAA/NIST mapping info 
    """
    utility.Utility.log_stdout(
        "6- Parsing the mapping document/sheet and creating list of rules having PCI/HIPAA/NIST mapping info and ignore rules with no PCI/HIPAA/NIST mapping info")
    parent_dir_name = os.path.dirname(__file__)
    # mapping_file_path = parent_dir_name + '/resources/'
    mapping_file_path = parent_dir_name.replace('\\', '/')

    excel_handler_obj = excel_handler.ExcelHandler()
    df = excel_handler_obj.read_from_excel(halo_api_caller_obj.sheet_name, halo_api_caller_obj.mapping_file_name, mapping_file_path, halo_api_caller_obj.excel_engine_type)

    cp_rule_id_lst = []
    fltrd_info_lst = []

    for index, row in df.iterrows():
        if mapping_type == custom_enum.MappingType.pci.value:
            pci_dss_req_no = str(row['PCI-DSS_Req. #'])
            if pci_dss_req_no != 'nan':
                cp_rule_id = str(row['CP Rule ID'])
                req_no = str(row['PCI-DSS_Req. #'])
                title = str(row['PCI-DSS_Title'])
                description = str(row['PCI-DSS_Description'])
                fltrd_info_elmnt = [cp_rule_id, req_no, title, description]
                cp_rule_id_lst.append(cp_rule_id)
                fltrd_info_lst.append(fltrd_info_elmnt)

        if mapping_type == custom_enum.MappingType.hipaa.value:
            hipaa_req_no = str(row['HIPAA_Req. #'])
            if hipaa_req_no != 'nan':
                cp_rule_id = str(row['CP Rule ID'])
                req_no = str(row['HIPAA_Req. #'])
                title = str(row['HIPAA_Title'])
                description = str(row['HIPAA_Description'])
                fltrd_info_elmnt = [cp_rule_id, req_no, title, description]
                cp_rule_id_lst.append(cp_rule_id)
                fltrd_info_lst.append(fltrd_info_elmnt)

        if mapping_type == custom_enum.MappingType.nist.value:
            nist_req_no = str(row['NIST CSF 1.1'])
            if nist_req_no != 'nan':
                cp_rule_id = str(row['CP Rule ID'])
                req_no = str(row['NIST CSF 1.1'])
                title = str(row['NIST_Title'])
                description = str(row['NIST_Description'])
                fltrd_info_elmnt = [cp_rule_id, req_no, title, description]
                cp_rule_id_lst.append(cp_rule_id)
                fltrd_info_lst.append(fltrd_info_elmnt)

    """
    Filtering the rules of target configuration policy based on the list of rules that have PCI/HIPAA/NIST mapping info generated from the previous step
    """
    utility.Utility.log_stdout(
        "7- Filtering the rules of target configuration policy based on the list of rules that have PCI/HIPAA/NIST mapping info generated from the previous step")
    if mapping_type == custom_enum.MappingType.pci.value:
        filtered_pcihipaanist_policy = halo_api_caller_obj.extract_policy_rules_have_pci(csm_plc_det, cp_rule_id_lst,
                                                                                         fltrd_info_lst)
    if mapping_type == custom_enum.MappingType.hipaa.value:
        filtered_pcihipaanist_policy = halo_api_caller_obj.extract_policy_rules_have_hipaa(csm_plc_det, cp_rule_id_lst,
                                                                                           fltrd_info_lst)
    if mapping_type == custom_enum.MappingType.nist.value:
        filtered_pcihipaanist_policy = halo_api_caller_obj.extract_policy_rules_have_nist(csm_plc_det, cp_rule_id_lst,
                                                                                          fltrd_info_lst)
    """
    creating the new configuration policy with only rules having PCI or HIPAA or NIST mapping info
    """
    utility.Utility.log_stdout(
        "8- creating the new configuration policy with only rules having PCI or HIPAA or NIST mapping info")
    csm_plc_crt_rst = halo_api_caller_obj.create_configuration_policy(filtered_pcihipaanist_policy)
    csm_plc_det = csm_plc_crt_rst[0]
    generated_policy_name = csm_plc_det['policy']['name']
    utility.Utility.log_stdout("9- Configuration Policy [%s] Generated Successfully" % generated_policy_name)
    utility.Utility.log_stdout("Mapping Script Finished.")


def check_configs(config, halo_api_caller):
    halo_api_caller_obj = halo_api_caller
    if halo_api_caller_obj.credentials_work() is False:
        utility.Utility.log_stdout("Halo credentials are bad!  Exiting!")
        sys.exit(1)

    if config.sane() is False:
        utility.Utility.log_stdout("Configuration is bad!  Exiting!")
        sys.exit(1)


if __name__ == "__main__":
    main()
