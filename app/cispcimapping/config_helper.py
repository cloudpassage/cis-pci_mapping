import os

from .utility import Utility


class ConfigHelper(object):
    """
    This class contains all application configuration variables.

    Attributes:
        halo_api_key_id (str): Halo API key ID, sometimes referred to as 'key id'
        halo_api_key_secret (str): Halo API Key Secret associated with halo_api_key_id
        halo_api_hostname (str): Hostname for Halo API
        halo_api_port (str): Halo API port
        halo_api_version (str): Halo API version
        halo_api_auth_url (str): Halo API authentication URL
        halo_api_auth_args (str): Halo API authentication arguments (grant_type)
        halo_api_auth_token (str): Halo API authentication token
        target_policy_name (str): Name of the policy which its' rules will be mapped from CIS to PCI
        mapping_file_name (str): Name of the document/sheet which contains the mapping rules
        mapping_type (str): Target Mapping Type (PCI, HIPAA, NIST)
    """

    def __init__(self):
        self.halo_api_key_id = os.getenv("HALO_API_KEY_ID", "HARDSTOP")
        self.halo_api_key_secret = os.getenv("HALO_API_KEY_SECRET", "HARDSTOP")
        self.halo_api_hostname = os.getenv("HALO_API_HOSTNAME", "https://api.cloudpassage.com")
        self.halo_api_port = os.getenv("HALO_API_PORT", "443")
        self.halo_api_version = os.getenv("HALO_API_VERSION", "v1")
        self.halo_api_auth_url = "oauth/access_token"
        self.halo_api_auth_args = {'grant_type': 'client_credentials'}
        self.halo_api_auth_token = None
        self.target_policy_name = os.getenv("TARGET_POLICY_NAME", "HARDSTOP")
        self.mapping_file_name =  os.getenv("MAPPING_FILE_NAME", "Ubuntu-CIS-Control-PCD-DSS-mapping.xlsx")
        self.sheet_name = os.getenv("SHEET_NAME", "Sheet2")
        self.excel_engine_type = "openpyxl"
        self.mapping_type = os.getenv("MAPPING_TYPE", "PCI")

    def sane(self):

        """
        Test to make sure that config items for Halo are set.
        Returns:
            True if everything is OK, False if otherwise
        """

        sanity = True
        template = "Required configuration variable {0} is not set!"
        critical_vars = {"HALO_API_KEY_ID": self.halo_api_key_id,
                         "HALO_API_KEY_SECRET": self.halo_api_key_secret,
                         "TARGET_POLICY_NAME": self.target_policy_name}
        for name, varval in critical_vars.items():
            if varval == "HARDSTOP":
                sanity = False
                Utility.log_stdout(template.format(name))
        return sanity
