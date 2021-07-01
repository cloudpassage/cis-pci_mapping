#!/usr/bin/env python3.9
import base64
import json
import os
import sys
import urllib.parse
import urllib.request

from app.src.main import excel_handler


class HaloAPICalls:

    def __init__(self):
        self.auth_url = 'oauth/access_token'
        self.auth_args = {'grant_type': 'client_credentials'}
        self.base_url = 'https://api.cloudpassage.com'
        self.api_ver = 'v1'
        self.port = 443
        self.key_id = '<HALO_API_KEY_ID>'
        self.secret = '<HALO_API_KEY_SECRET>'
        self.auth_token = None
        self.target_policy_name = 'CIS Benchmark for Ubuntu Linux 18.04 LTS v1 (CIS v2.0.1) 2020-11-13 19:42:25-Copy'
        self.mapping_file_name = 'Ubuntu-CIS-Control-PCD-DSS-mapping.xlsx'

    # Dump debug info
    def dump_token(self, token, expires):
        if token:
            print("AuthToken=%s" % token)
        if expires:
            print("Expires in %s minutes" % (expires / 60))

    def get_http_status(self, code):
        if code == 200:
            return "OK"
        elif code == 401:
            return "Unauthorized"
        elif code == 403:
            return "Forbidden"
        elif code == 404:
            return "Not found"
        elif code == 422:
            return "Validation failed"
        elif code == 500:
            return "Internal server error"
        elif code == 502:
            return "Gateway error"
        else:
            return "Unknown code [%d]" % code

    # add authentication token into the request
    def add_auth(self, req, kid, sec):
        combined = kid + ":" + sec
        combined_bytes = combined.encode("utf-8")
        encoded = base64.b64encode(combined_bytes)
        encoded_str = encoded.decode("utf-8")
        req.add_header("Authorization", "Basic " + encoded_str)

    def get_auth_token(self, url, args, kid, sec):
        req = urllib.request.Request(url)
        self.add_auth(req, kid, sec)
        if args:
            args = urllib.parse.urlencode(args).encode("utf-8")
        try:
            fh = urllib.request.urlopen(req, data=args)
            return fh.read()
        except IOError as e:
            if hasattr(e, 'reason'):
                print(sys.stderr, "Failed to connect [%s] to '%s'" % (e.reason, url))
            elif hasattr(e, 'code'):
                msg = self.get_http_status(e.code)
                print(sys.stderr, "Failed to authorize [%s] at '%s'" % (msg, url))
                data = e.read()
                if data:
                    print(sys.stderr, "Extra data: %s" % data)
                print(sys.stderr, "Likely cause: incorrect API keys, id=%s" % kid)
            else:
                print(sys.stderr, "Unknown error fetching '%s'" % url)
            return None

    def get_initial_link(self, from_date, events_per_page):
        url = "%s:%d/%s/events?per_page=%d" % (self.base_url, self.port, self.api_ver, events_per_page)
        if from_date:
            url += "&since=" + from_date
        return url

    def get_event_batch(self, url):
        return self.do_get_request(url, self.auth_token)

    def do_get_request(self, url, token):
        req = urllib.request.Request(url)
        req.add_header("Authorization", "Bearer " + token)
        try:
            fh = urllib.request.urlopen(req)
            return fh.read(), False
        except IOError as e:
            auth_error = False
            if hasattr(e, 'reason'):
                print(sys.stderr, "Failed to connect [%s] to '%s'" % (e.reason, url))
            elif hasattr(e, 'code'):
                msg = self.get_http_status(e.code)
                print(sys.stderr, "Failed to fetch events [%s] from '%s'" % (msg, url))
                if e.code == 401:
                    auth_error = True
            else:
                print(sys.stderr, "Unknown error fetching '%s'" % url)
            return None, auth_error

    def do_put_request(self, url, token, put_data):
        opener = urllib.request.build_opener(urllib.request.HTTPHandler)
        req = urllib.request.Request(url, data=put_data.encode("utf-8"))
        req.add_header("Authorization", "Bearer " + token)
        req.add_header("Content-Type", "application/json")
        req.get_method = lambda: 'PUT'
        try:
            fh = opener.open(req)
            return fh.read(), False
        except IOError as e:
            auth_error = False
            if hasattr(e, 'reason'):
                print(sys.stderr, "Failed to connect [%s] to '%s'" % (e.reason, url))
            if hasattr(e, 'code'):
                msg = self.get_http_status(e.code)
                print(sys.stderr, "Failed to make request: [%s] from '%s'" % (msg, url))
                if e.code == 401:
                    auth_error = True
            if (not hasattr(e, 'reason')) and (not hasattr(e, 'code')):
                print(sys.stderr, "Unknown error fetching '%s'" % url)
            return None, auth_error

    def do_post_request(self, url, token, post_data):
        opener = urllib.request.build_opener(urllib.request.HTTPHandler)
        req = urllib.request.Request(url, data=post_data.encode("utf-8"))
        req.add_header("Authorization", "Bearer " + token)
        req.add_header("Content-Type", "application/json")
        try:
            fh = opener.open(req)
            return fh.read(), False
        except IOError as e:
            auth_error = False
            if hasattr(e, 'reason'):
                print(sys.stderr, "Failed to connect [%s] to '%s'" % (e.reason, url))
            if hasattr(e, 'code'):
                msg = self.get_http_status(e.code)
                print(sys.stderr, "Failed to make request: [%s] from '%s'" % (msg, url))
                if e.code == 401:
                    auth_error = True
            if (not hasattr(e, 'reason')) and (not hasattr(e, 'code')):
                print(sys.stderr, "Unknown error fetching '%s'" % url)
            return None, auth_error

    def authenticate_client(self):
        url = "%s:%d/%s" % (self.base_url, self.port, self.auth_url)
        response = self.get_auth_token(url, self.auth_args, self.key_id, self.secret)
        if response:
            auth_resp_obj = json.loads(response)
            if 'access_token' in auth_resp_obj:
                self.auth_token = auth_resp_obj['access_token']
            if 'expires_in' in auth_resp_obj:
                self.expires = auth_resp_obj['expires_in']
        return self.auth_token

    def get_server_list(self):
        url = "%s:%d/%s/servers" % (self.base_url, self.port, self.api_ver)
        (data, auth_error) = self.do_get_request(url, self.auth_token)
        if data:
            return json.loads(data), auth_error
        else:
            return None, auth_error

    def get_server_group_list(self):
        url = "%s:%d/%s/groups" % (self.base_url, self.port, self.api_ver)
        (data, auth_error) = self.do_get_request(url, self.auth_token)
        if data:
            return json.loads(data), auth_error
        else:
            return None, auth_error

    def get_firewall_policy_list(self):
        url = "%s:%d/%s/firewall_policies/" % (self.base_url, self.port, self.api_ver)
        (data, auth_error) = self.do_get_request(url, self.auth_token)
        if data:
            return json.loads(data), auth_error
        else:
            return None, auth_error

    def get_firewall_policy_details(self, policy_id):
        url = "%s:%d/%s/firewall_policies/%s" % (self.base_url, self.port, self.api_ver, policy_id)
        (data, auth_error) = self.do_get_request(url, self.auth_token)
        if data:
            return json.loads(data), auth_error
        else:
            return None, auth_error

    def get_configuration_policy_list(self):
        url = "%s:%d/%s/policies/" % (self.base_url, self.port, self.api_ver)
        (data, auth_error) = self.do_get_request(url, self.auth_token)
        if data:
            return json.loads(data), auth_error
        else:
            return None, auth_error

    def get_configuration_policy_details(self, policy_id):
        url = "%s:%d/%s/policies/%s" % (self.base_url, self.port, self.api_ver, policy_id)
        (data, auth_error) = self.do_get_request(url, self.auth_token)
        if data:
            return json.loads(data), auth_error
        else:
            return None, auth_error

    def move_server_to_group(self, server_id, group_id):
        url = "%s:%d/%s/servers/%s" % (self.base_url, self.port, self.api_ver, server_id)
        req_data = {"server": {"group_id": group_id}}
        json_data = json.dumps(req_data)
        (data, auth_error) = self.do_put_request(url, self.auth_token, json_data)
        if data:
            return json.loads(data), auth_error
        else:
            return None, auth_error

    def create_server_group(self, group_name, linux_firewall_policy, windows_firewall_policy):
        url = "%s:%d/%s/groups" % (self.base_url, self.port, self.api_ver)
        group_data = {"name": group_name, "policy_ids": [], "tag": None,
                      "linux_firewall_policy_id": linux_firewall_policy,
                      "windows_firewall_policy_id": windows_firewall_policy}
        req_data = {"group": group_data}
        json_data = json.dumps(req_data)
        (data, auth_error) = self.do_post_request(url, self.auth_token, json_data)
        if data:
            return json.loads(data), auth_error
        else:
            return None, auth_error

    def create_firewall_policy(self, policy_data):
        url = "%s:%d/%s/firewall_policies" % (self.base_url, self.port, self.api_ver)
        json_data = json.dumps(policy_data)
        (data, auth_error) = self.do_post_request(url, self.auth_token, json_data)
        if data:
            return json.loads(data), auth_error
        else:
            return None, auth_error

    def create_configuration_policy(self, policy_data):
        url = "%s:%d/%s/policies" % (self.base_url, self.port, self.api_ver)
        json_data = json.dumps(policy_data)
        (data, auth_error) = self.do_post_request(url, self.auth_token, json_data)
        if data:
            return json.loads(data), auth_error
        else:
            return None, auth_error

    def extract_policy_from_policy_list(self, policy_list, policy_name):
        policy_list_data = policy_list[0]
        target_policy_id = None
        for policy in policy_list_data['policies']:
            if policy['name'] == policy_name:
                target_policy_id = policy['id']
        return target_policy_id

    def extract_policy_rules_have_pci(self, policy_details_tuple, cp_rule_id_lst, pci_info_lst):
        policy_details = policy_details_tuple[0]
        rule_id_lst_has_pci = cp_rule_id_lst
        plc_rules_lst = []
        for rule in policy_details['policy']['rules']:
            current_rule_id = rule.get('cp_rule_id')
            current_rule_name = rule.get('name')
            if current_rule_id in rule_id_lst_has_pci:
                for pci_info_elmnt in pci_info_lst:
                    if pci_info_elmnt[0] == current_rule_id:
                        rule.update(user_notes = 'PCI-DSS Req: '+pci_info_elmnt[1]+', PCI_Title: '+pci_info_elmnt[2]+', PCI_Description: '+pci_info_elmnt[3])
                        rule.update(name = 'PCI-DSS-'+pci_info_elmnt[1]+'-'+current_rule_name)
                plc_rules_lst.append(rule)
        policy_details['policy']['name'] = self.target_policy_name + "_with-pci"
        policy_details['policy']['rules'] = plc_rules_lst
        return policy_details


if __name__ == '__main__':

    halo_api_calls_obj = HaloAPICalls()

    halo_api_calls_obj.authenticate_client()

    csm_plc_lst = halo_api_calls_obj.get_configuration_policy_list()

    policy_name = halo_api_calls_obj.target_policy_name
    target_policy_id = halo_api_calls_obj.extract_policy_from_policy_list(csm_plc_lst, policy_name)

    csm_plc_det = halo_api_calls_obj.get_configuration_policy_details(target_policy_id)


    parent_dirname = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    mapping_file_path = parent_dirname + '/resources/'
    mapping_file_path = mapping_file_path.replace('\\', '/')

    excel_handler_obj = excel_handler.ExcelHandler()
    df = excel_handler_obj.read_from_excel(halo_api_calls_obj.mapping_file_name, mapping_file_path)

    cp_rule_id_lst = []
    pci_info_lst = []
    for index, row in df.iterrows():
        pci_dss_req_no = str(row['PCI-DSS Req. #'])
        if pci_dss_req_no != 'nan':
            cp_rule_id = str(row['CP Rule ID'])

            pci_dss_no = str(row['PCI-DSS Req. #'])
            pci_title = str(row['PCI_Title'])
            pci_description = str(row['PCI_Description'])
            pci_info_elmnt = [cp_rule_id, pci_dss_no, pci_title, pci_description]

            cp_rule_id_lst.append(cp_rule_id)
            pci_info_lst.append(pci_info_elmnt)

    filtered_policy_has_pci = halo_api_calls_obj.extract_policy_rules_have_pci(csm_plc_det, cp_rule_id_lst, pci_info_lst)
    csm_plc_crt_rst = halo_api_calls_obj.create_configuration_policy(filtered_policy_has_pci)
    print(csm_plc_crt_rst)

    '''
    excel_handler_obj = excel_handler.ExcelHandler()
    df = excel_handler_obj.read_from_excel('Ubuntu-CIS-Control-PCD-DSS-mapping.xlsx',
                                           'C:/Users/Tom/PycharmProjects/CIS-PCI_Mapping/app/resources/',
                                           0)
    #print(df.index)
    #print(df.columns)
    #print(df.shape)

    plc_rules_lst = []
    for index, row in df.iterrows():
        pci_dss_req_no = str(row['PCI-DSS Req. #'])
        if pci_dss_req_no == 'nan':
            print("No Mapping!")
        else:
            rule_details = {
                "cp_rule_id": str(row['CP Rule ID']),
                "name": str(row['Rule Name']),
                "comment": str(row['CIS Control Description'])
            }
            plc_rules_lst.append(rule_details)
    print(len(plc_rules_lst))

    plc_details = {
        "name": df.loc[0, 'Policy Name'],
        "description": 'cis pci mapping policy',
        "module": custom_enum.Module.csm.name,
        "platform": custom_enum.Platform.linux.name,
        "target_type": custom_enum.TargetType.server.name,
        "rules": plc_rules_lst
    }
    full_plc_data = {
        "policy": plc_details
    }
    print(full_plc_data)
    csm_plc_crt_rst = halo_api_calls_obj.create_configuration_policy(full_plc_data)
    print(csm_plc_crt_rst)
    '''
