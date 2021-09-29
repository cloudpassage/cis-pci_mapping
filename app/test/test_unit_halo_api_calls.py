import imp
import os
import sys

module_name = 'cispcimapping'
current_dir = os.path.dirname(os.path.abspath(__file__))
module_path = os.path.join(current_dir, '../')
sys.path.append(module_path)
fp, pathname, description = imp.find_module(module_name)
cis_pci_mapping = imp.load_module(module_name, fp, pathname, description)


def test_get_configuration_policy_list():
    config = cis_pci_mapping.ConfigHelper()
    halo_api_caller_obj = cis_pci_mapping.HaloAPICaller(config)
    halo_api_caller_obj.authenticate_client()
    csm_plc_lst = halo_api_caller_obj.get_configuration_policy_list()
    csm_plc_lst_list = csm_plc_lst[0]
    assert csm_plc_lst_list['count'] == 145


def test_get_configuration_policy_details():
    config = cis_pci_mapping.ConfigHelper()
    halo_api_caller_obj = cis_pci_mapping.HaloAPICaller(config)
    halo_api_caller_obj.authenticate_client()
    csm_plc_det = halo_api_caller_obj.get_configuration_policy_details(config.target_policy_id)
    policy_details = csm_plc_det[0]
    assert policy_details['policy']['name'] == config.target_policy_name
