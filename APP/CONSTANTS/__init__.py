# -*- coding: utf-8 -*-

__author__ = ["Jason Smith"]
__credits__ = ["Jason Smith", "Steve Powell"]
__email__ = ["jasons2@cisco.com"]

# IMPORTS
from pathlib import Path
from datetime import datetime
import re
from logging import INFO, DEBUG

# APPLICATION TREE
APP_DIR = Path.cwd()
CONSTANTS_DIR = APP_DIR.joinpath("CONSTANTS")
HELPERS_DIR = APP_DIR.joinpath("HELPERS")
MAIN_DIR = APP_DIR.parent
LOGGING_DIR = MAIN_DIR.joinpath("LOGS")
PROJECT_DIR = MAIN_DIR.joinpath("PROJECTS")

# Logging CONSTANTS
LOG_FILE_NAME = "ezConfig.log"
LOGGING_FORMAT = "[%(asctime)s|%(name)s|%(levelname)s] %(message)s"
LOGGING_LEVEL = DEBUG

# TIME CONSTANTS
NOW = datetime.now().strftime("%H%M%S")
TODAY = datetime.now().strftime("%m%d%y")

# ANSIBLE RELATIVE PATHS
ANSIBLE_PLAYBOOK_REL_PATH = "playbooks/"
ANSIBLE_HOST_VARS_REL_PATH = "playbooks/host_vars/"
ANSIBLE_TMP_REL_PATH = "playbooks/tmp/"
ANSIBLE_TEMPLATE_REL_PATH = "playbooks/templates/"
ANSIBLE_CHG_VALID_REL_PATH = "playbooks/change_validation/"

# REGEX PATTERNS
# Regex pattern to determine if host is IP address
IPV4_PATTERN = re.compile(
    r"\b((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\b"
)

# ANSIBLE TASKS
GATHER_CONFIG_BEFORE_TASK = {
    "name": "Gather pre-change configurations",
    "include_tasks": "gather_prechange_config_task.yml",
    "when": "run_other_playbook",
}

GATHER_CONFIG_AFTER_TASK = {
    "name": "Gather post-change configurations",
    "include_tasks": "gather_postchange_config_task.yml",
    "when": "run_other_playbook",
}
