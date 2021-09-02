# CIS_Mapping_Tool
CIS Mapping Tool 

## Goal:
The main purpose of this tool is to map the provided configuration policy rules from CIS Controls to PCI, HIPAA, and NIST.

## Requirements:
- CloudPassage Halo API key (with admin privileges).
- Python 3.6 or later including packages specified in "requirements.txt". 
- CIS Mapping Document.

## Installation:
`git clone https://github.com/cloudpassage/cis-pci_mapping.git`

`pip install -r requirements.txt`

## Configuration:
| Variable | Value |
| -------- | ----- |
| HALO_API_KEY_ID | <HALO_API_KEY_ID> |
| HALO_API_KEY_SECRET | <HALO_API_KEY_SECRET> |
| HALO_API_HOSTNAME | https://api.cloudpassage.com |
| HALO_API_PORT | 443 |
| HALO_API_VERSION | v1 |
| TARGET_POLICY_NAME | <TARGET_POLICY_NAME> |
| MAPPING_TYPE | <MAPPING_TYPE> i.e. "PCI, HIPAA, NIST" |
| MAPPING_FILE_NAME | <MAPPING_FILE_NAME> i.e. "Ubuntu-CIS-Control-PCD-DSS-mapping.xlsx" |
| SHEET_NAME | <SHEET_NAME> i.e. "Sheet2" |

## How to the script works:
### 1. Call Authentication
The script authenticates with HALO API system using ID and secret key and receive a bearer token which can be used to fetch resources for 15 minutes until a new token is required.
### 2.	CIS Mapping Document Parser
The script parses the CIS mapping document (based on CIS controls version 7 found on sheet 2) [CIS Mapping Sheet](https://drive.google.com/file/d/1_KCbnLCpvPTwxwzTwC5gofZTIf1YcBDL/view?ts=60da046b).
#### - PCI rules extraction from the mapping document:
The script iterates over all the policy rules found in the sheet and creates a new list of rules that have a valid mapping PCI DSS request number, and ignore any rule having PCI DSS request number equal to “N/A” and then saves the new generated list for later usage.
#### - HIPAA rules extraction from the mapping document:
The script iterates over all the policy rules found in the sheet and creates a new list of rules that have a valid mapping HIPAA request number, and ignore any rule having HIPAA request number equal to “N/A” and then saves the new generated list for later usage.
#### - NIST rules extraction from the mapping document:
The script iterates over all the policy rules found in the sheet and creates a new list of rules that have a valid mapping NIST request number, and ignore any rule having NIST request number equal to “N/A” and then saves the new generated list for later usage.
### 3.	Retrieve All Configuration Policies
The script creates a call to HALO API system to retrieve a list of all configuration policies.
### 4.	Get Configuration Policy ID from Policy Name
The script extracts target configuration policy name from the provided environment variables and then iterates over the generated list of configuration policies retrieved from the previous step (step no. 3) to get the target configuration policy ID.
### 5.	Get Configuration Policy Details
The script creates a call to the HALO API system using the target policy ID obtained from the previous step (step no. 4) to get the configuration policy details that includes the policy rules.
### 6.	Filter target configuration policy rules based on mapping type 
#### - Filter configuration policy rule based on PCI records list from the mapping document
The script iterates over all the target policy rules retrieved from previous step (step no. 5) and filters out every policy rule not found in the generated list of rules that have PCI DSS request number retrieved from the second step (step no. 2). Then the script appends the appropriate PCI_DSS Req number into the rule name and adds the PCI info (PCI-DSS Req, PCI_Title, and PCI_Description) into rule field entitled “user_notes”.
#### - Filter configuration policy rule based on HIPAA records list from the mapping document
The script iterates over all the target policy rules retrieved from previous step (step no. 5) and filters out every policy rule not found in the generated list of rules that have HIPAA request number retrieved from the second step (step no. 2). Then the script appends the appropriate HIPAA Req number into the rule name and adds the HIPAA info (HIPAA Req, HIPAA_Title, and HIPAA_Description) into rule field entitled “user_notes”.
#### - Filter configuration policy rule based on NIST records list from the mapping document
The script iterates over all the target policy rules retrieved from previous step (step no. 5) and filters out every policy rule not found in the generated list of rules that have NIST request number retrieved from the second step (step no. 2). Then the script appends the appropriate NIST Req number into the rule name and adds the NIST info (NIST Req, NIST_Title, and NIST_Description) into rule field entitled “user_notes”.

### 7.	Construct New Policy JSON Object
After the script finishes iterating over the target policy rules and eliminating the rules with no PCI or HIPAA or NIST request number, then the script creates a new policy JSON object containing only the policy rules having PCI or HIPAA or NIST request numbers.
### 8.	Create New Configuration Policy
The script creates a call to the HALO API system and attach the JSON object created from the previous step (step no. 7) to create a new configuration policy having only the rules with PCI or HIPAA or NIST request numbers.

## How to run the tool:
The following commands are for running the mapping script.

`cd cis-pci_mapping/app`

`python runner.py`
