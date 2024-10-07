#ezConfig 

This script enables a network engineer to easily push configuration(s) to a remote device(s).

#Overview
-Each job will be a directory located in the JOBS directory.
-Each job requires one YAML file and at least one Jinja2 template file.
-The YAML file, called job_definition.yml in the sample_job provided as an example, defines the devices to change, as well
as the variables to use, and the template to apply.

##Example YAML file (excerpt from job_definition.yml in sample_job dir):
- name: remove sccp values
  description: Remove old SCCP values
  device_names: [host1.somedomain.com, host2.somedomain.com, host3.somedomain.com]
  jinja2_template: remove_sccp.j2
  variables:
    on_prem_ip_1: 10.10.10.10
    on_prem_ip_2: 20.20.20.20

##Example Jinja file (remove_sccp.j2 in sample_job dir):
!
no sccp
sccp ccm group 1
 no associate ccm 1 priority 1
 no associate ccm 2 priority 2
!
no sccp ccm {{ on_prem_ip_1 }} identifier 1 version 7.0 
no sccp ccm {{ on_prem_ip_2 }} identifier 2 version 7.0 
!

#How to Use It: 
Example:  ezConfig -u someuser -p somepassword --job some_job_name

The username and password must be valid for all devices which will be changed.
The job name (some_job_name) is a directory in the JOBS directory.  The 
script will automatically find the YAML file in the directory and execute it.

usage:
ezConfig.py [-h] -u USERNAME [-p PASSWORD] [--project PROJECT]

Collects input from user.

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        FedEx Tacacs User Id
  -p PASSWORD, --password PASSWORD
                        FedEx Tacacs Password
  --project PROJECT     Name of directory in Project Directory defining changes to be made
