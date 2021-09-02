#!/usr/bin/env python3.9
import base64
import json
import urllib.parse
import urllib.request
from datetime import datetime

import cloudpassage

from . import utility


class HaloAPICaller(object):

    def __init__(self, config):
        self.halo_api_auth_url = config.halo_api_auth_url
        self.halo_api_auth_args = config.halo_api_auth_args
        self.halo_api_hostname = config.halo_api_hostname
        self.halo_api_version = config.halo_api_version
        self.halo_api_port = int(config.halo_api_port)
        self.halo_api_key_id = config.halo_api_key_id
        self.halo_api_key_secret = config.halo_api_key_secret
        self.halo_api_auth_token = config.halo_api_auth_token
        self.target_policy_name = config.target_policy_name
        self.mapping_file_name = config.mapping_file_name
        self.sheet_name = config.sheet_name
        self.excel_engine_type = config.excel_engine_type
        self.mapping_type = config.mapping_type

    # Dump debug info
    @classmethod
    def dump_token(cls, token, expires):
        if token:
            utility.Utility.log_stdout("AuthToken=%s" % token)
        if expires:
            utility.Utility.log_stdout("Expires in %s minutes" % (expires / 60))

    @classmethod
    def get_http_status(cls, code):
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
    @classmethod
    def add_auth(cls, req, kid, sec):
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
                utility.Utility.log_stderr("Failed to connect [%s] to '%s'" % (e.reason, url))
            elif hasattr(e, 'code'):
                msg = self.get_http_status(e.code)
                utility.Utility.log_stderr("Failed to authorize [%s] at '%s'" % (msg, url))
                data = e.read()
                if data:
                    utility.Utility.log_stderr("Extra data: %s" % data)
                utility.Utility.log_stderr("Likely cause: incorrect API keys, id=%s" % kid)
            else:
                utility.Utility.log_stderr("Unknown error fetching '%s'" % url)
            return None

    def get_initial_link(self, from_date, events_per_page):
        url = "%s:%d/%s/events?per_page=%d" % (
            self.halo_api_hostname, self.halo_api_port, self.halo_api_version, events_per_page)
        if from_date:
            url += "&since=" + from_date
        return url

    def get_event_batch(self, url):
        return self.do_get_request(url, self.halo_api_auth_token)

    def do_get_request(self, url, token):
        req = urllib.request.Request(url)
        req.add_header("Authorization", "Bearer " + token)
        try:
            fh = urllib.request.urlopen(req)
            return fh.read(), False
        except IOError as e:
            auth_error = False
            if hasattr(e, 'reason'):
                utility.Utility.log_stderr("Failed to connect [%s] to '%s'" % (e.reason, url))
            elif hasattr(e, 'code'):
                msg = self.get_http_status(e.code)
                utility.Utility.log_stderr("Failed to fetch events [%s] from '%s'" % (msg, url))
                if e.code == 401:
                    auth_error = True
            else:
                utility.Utility.log_stderr("Unknown error fetching '%s'" % url)
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
                utility.Utility.log_stderr("Failed to connect [%s] to '%s'" % (e.reason, url))
            if hasattr(e, 'code'):
                msg = self.get_http_status(e.code)
                utility.Utility.log_stderr("Failed to make request: [%s] from '%s'" % (msg, url))
                if e.code == 401:
                    auth_error = True
            if (not hasattr(e, 'reason')) and (not hasattr(e, 'code')):
                utility.Utility.log_stderr("Unknown error fetching '%s'" % url)
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
                utility.Utility.log_stderr("Failed to connect [%s] to '%s'" % (e.reason, url))
            if hasattr(e, 'code'):
                msg = self.get_http_status(e.code)
                utility.Utility.log_stderr("Failed to make request: [%s] from '%s'" % (msg, url))
                if e.code == 401:
                    auth_error = True
            if (not hasattr(e, 'reason')) and (not hasattr(e, 'code')):
                utility.Utility.log_stderr("Unknown error fetching '%s'" % url)
            return None, auth_error

    def authenticate_client(self):
        url = "%s:%d/%s" % (self.halo_api_hostname, self.halo_api_port, self.halo_api_auth_url)
        response = self.get_auth_token(url, self.halo_api_auth_args, self.halo_api_key_id, self.halo_api_key_secret)
        if response:
            auth_resp_obj = json.loads(response)
            if 'access_token' in auth_resp_obj:
                self.halo_api_auth_token = auth_resp_obj['access_token']
            if 'expires_in' in auth_resp_obj:
                self.expires = auth_resp_obj['expires_in']
        return self.halo_api_auth_token

    def get_firewall_policy_list(self):
        url = "%s:%d/%s/firewall_policies/" % (self.halo_api_hostname, self.halo_api_port, self.halo_api_version)
        (data, auth_error) = self.do_get_request(url, self.halo_api_auth_token)
        if data:
            return json.loads(data), auth_error
        else:
            return None, auth_error

    def get_firewall_policy_details(self, policy_id):
        url = "%s:%d/%s/firewall_policies/%s" % (
            self.halo_api_hostname, self.halo_api_port, self.halo_api_version, policy_id)
        (data, auth_error) = self.do_get_request(url, self.halo_api_auth_token)
        if data:
            return json.loads(data), auth_error
        else:
            return None, auth_error

    def get_configuration_policy_list(self):
        url = "%s:%d/%s/policies/" % (self.halo_api_hostname, self.halo_api_port, self.halo_api_version)
        (data, auth_error) = self.do_get_request(url, self.halo_api_auth_token)
        if data:
            return json.loads(data), auth_error
        else:
            return None, auth_error

    def get_configuration_policy_details(self, policy_id):
        url = "%s:%d/%s/policies/%s" % (self.halo_api_hostname, self.halo_api_port, self.halo_api_version, policy_id)
        (data, auth_error) = self.do_get_request(url, self.halo_api_auth_token)
        if data:
            return json.loads(data), auth_error
        else:
            return None, auth_error

    def create_firewall_policy(self, policy_data):
        url = "%s:%d/%s/firewall_policies" % (self.halo_api_hostname, self.halo_api_port, self.halo_api_version)
        json_data = json.dumps(policy_data)
        (data, auth_error) = self.do_post_request(url, self.halo_api_auth_token, json_data)
        if data:
            return json.loads(data), auth_error
        else:
            return None, auth_error

    def create_configuration_policy(self, policy_data):
        url = "%s:%d/%s/policies" % (self.halo_api_hostname, self.halo_api_port, self.halo_api_version)
        json_data = json.dumps(policy_data)
        (data, auth_error) = self.do_post_request(url, self.halo_api_auth_token, json_data)
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

    def extract_policy_rules_have_pci(self, policy_details_tuple, cp_rule_id_lst, fltrd_pcirule_lst):
        policy_details = policy_details_tuple[0]
        rule_id_lst_has_pci = cp_rule_id_lst
        plc_rules_lst = []
        for rule in policy_details['policy']['rules']:
            current_rule_id = rule.get('cp_rule_id')
            current_rule_name = rule.get('name')
            if current_rule_id in rule_id_lst_has_pci:
                for pci_ruleinfo_elmnt in fltrd_pcirule_lst:
                    if pci_ruleinfo_elmnt[0] == current_rule_id:
                        rule.update(
                            user_notes='PCI-DSS Req: ' + pci_ruleinfo_elmnt[1] + ', PCI_Title: ' + pci_ruleinfo_elmnt[
                                2] + ', PCI_Description: ' + pci_ruleinfo_elmnt[3])
                        rule.update(name='PCI-DSS-' + pci_ruleinfo_elmnt[1] + '-' + current_rule_name)
                plc_rules_lst.append(rule)
        current_time = utility.Utility.date_to_iso8601(datetime.now())
        policy_details['policy']['name'] = "PCI-DSS_" + self.target_policy_name + "_" + current_time
        policy_details['policy']['rules'] = plc_rules_lst
        return policy_details

    def extract_policy_rules_have_hipaa(self, policy_details_tuple, cp_rule_id_lst, fltrd_hipaarule_lst):
        policy_details = policy_details_tuple[0]
        rule_id_lst_has_hipaa = cp_rule_id_lst
        plc_rules_lst = []
        for rule in policy_details['policy']['rules']:
            current_rule_id = rule.get('cp_rule_id')
            current_rule_name = rule.get('name')
            if current_rule_id in rule_id_lst_has_hipaa:
                for hipaa_ruleinfo_elmnt in fltrd_hipaarule_lst:
                    if hipaa_ruleinfo_elmnt[0] == current_rule_id:
                        rule.update(user_notes='HIPAA Req: ' + hipaa_ruleinfo_elmnt[1] + ', HIPAA_Title: ' +
                                               hipaa_ruleinfo_elmnt[
                                                   2] + ', HIPAA_Description: ' + hipaa_ruleinfo_elmnt[3])
                        rule.update(name='HIPAA-' + hipaa_ruleinfo_elmnt[1] + '-' + current_rule_name)
                plc_rules_lst.append(rule)
        current_time = utility.Utility.date_to_iso8601(datetime.now())
        policy_details['policy']['name'] = "HIPAA_" + self.target_policy_name + "_" + current_time
        policy_details['policy']['rules'] = plc_rules_lst
        return policy_details

    def extract_policy_rules_have_nist(self, policy_details_tuple, cp_rule_id_lst, fltrd_nistrule_lst):
        policy_details = policy_details_tuple[0]
        rule_id_lst_has_nist = cp_rule_id_lst
        plc_rules_lst = []
        for rule in policy_details['policy']['rules']:
            current_rule_id = rule.get('cp_rule_id')
            current_rule_name = rule.get('name')
            if current_rule_id in rule_id_lst_has_nist:
                for nist_ruleinfo_elmnt in fltrd_nistrule_lst:
                    if nist_ruleinfo_elmnt[0] == current_rule_id:
                        rule.update(
                            user_notes='NIST Req: ' + nist_ruleinfo_elmnt[1] + ', NIST_Title: ' + nist_ruleinfo_elmnt[
                                2] + ', NIST_Description: ' + nist_ruleinfo_elmnt[3])
                        rule.update(name='NIST-' + nist_ruleinfo_elmnt[1] + '-' + current_rule_name)
                plc_rules_lst.append(rule)
        current_time = utility.Utility.date_to_iso8601(datetime.now())
        policy_details['policy']['name'] = "NIST_" + self.target_policy_name + "_" + current_time
        policy_details['policy']['rules'] = plc_rules_lst
        return policy_details

    def credentials_work(self):

        """
        Attempts to authenticate against Halo API
        """

        good = True
        try:
            self.authenticate_client()
        except cloudpassage.CloudPassageAuthentication:
            good = False
        return good
