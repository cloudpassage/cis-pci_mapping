# CIS-PCI_Mapping
CIS PCI Mapping Tool 

## Goal:
The main purpose of this tool is to map the provided configuration policy rules from CIS Controls to the Payment Card Industry Data Security Standard (PCI DSS).

## Requirements:
- CloudPassage Halo API key (with admin privileges).
- Python 3.6 or later including packages specified in "requirements.txt".

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

## How to run the tool:
The following commands are for running the mapping script.

`cd cis-pci_mapping/app`

`python runner.py`