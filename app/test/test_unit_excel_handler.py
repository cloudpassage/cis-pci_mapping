import imp
import os
import sys

module_name = 'cispcimapping'
current_dir = os.path.dirname(os.path.abspath(__file__))
module_path = os.path.join(current_dir, '../')
sys.path.append(module_path)
fp, pathname, description = imp.find_module(module_name)
cis_pci_mapping = imp.load_module(module_name, fp, pathname, description)


def test_excel_handler():
    config = cis_pci_mapping.ConfigHelper()
    sheet_name = config.sheet_name
    mapping_file_name = config.mapping_file_name
    mapping_file_path = module_path
    excel_engine_type = config.excel_engine_type
    excel_handler_obj = cis_pci_mapping.ExcelHandler()
    df = excel_handler_obj.read_from_excel(sheet_name, mapping_file_name,
                                           mapping_file_path, excel_engine_type)
    assert len(df) == 222