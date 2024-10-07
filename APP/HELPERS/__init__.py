# -*- coding: utf-8 -*-

__author__ = ["Jason Smith"]
__credits__ = ["Jason Smith"]
__email__ = ["jasons2@cisco.com"]

# PKG/MODULE IMPORTS
import argparse
from getpass import getpass
import os
import shutil
import subprocess
from pathlib import Path
import yaml
import re
import logging
from logging import INFO, DEBUG


# CONSTANTS IMPORTS
from CONSTANTS import LOGGING_DIR
from CONSTANTS import LOGGING_FORMAT
from CONSTANTS import JOB_DIR
from CONSTANTS import IPV4_PATTERN
from CONSTANTS import ANSIBLE_PLAYBOOK_REL_PATH
from CONSTANTS import ANSIBLE_HOST_VARS_REL_PATH
from CONSTANTS import ANSIBLE_TMP_REL_PATH
from CONSTANTS import ANSIBLE_TEMPLATE_REL_PATH
from CONSTANTS import ANSIBLE_CHG_VALID_REL_PATH


# UTILITY FUNCTIONS
def setupLogging(name: str, log_file: str, c_level: int, f_level):
    """
    Sets up a logger that writes both to the console and a file.

    :param name: The name of the logger.
    :param log_file: The file path where the log will be written.
    :param level: The logging level. Default is logging.INFO.
    :returns: logger: A logger instance

    """

    # Create a custom logger
    logger = logging.getLogger(name)
    logger.setLevel(f_level)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(LOGGING_DIR.joinpath(log_file))

    # Create formatters and add it to handlers
    c_format = logging.Formatter(LOGGING_FORMAT)
    f_format = logging.Formatter(LOGGING_FORMAT)

    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Set level for handlers
    c_handler.setLevel(c_level)
    f_handler.setLevel(f_level)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger


# Create a logger for this module
logger = setupLogging(__name__, "ezConfig", INFO, DEBUG)


def getArgs() -> dict:
    """Collect command line arguments

    :return: NameSpace object
    """
    parser = argparse.ArgumentParser(description="Collects input from user.")
    group = parser.add_mutually_exclusive_group()

    # Add arguments
    parser.add_argument("-u", "--username", required=True, type=str, help="FedEx Tacacs User Id")
    parser.add_argument("-p", "--password", type=str, help="FedEx Tacacs Password")
    group.add_argument("--job", type=str, help="Name of directory in JOBS Directory defining changes to be made")

    args = parser.parse_args()

    if not args.password:
        setattr(args, "password", getpass("Please enter your Password: "))

    return args


def shortenFQDN(fqdn: str) -> str:
    """
    Truncates Fully Qualified Domain Name and returns the hostname.
    If an IPv4 address is encountered, it is returned unchanged.

    :param fqdn Fully Qualified Domain Name
    "return: hostname str"""

    if IPV4_PATTERN.search(fqdn):
        return fqdn

    elif "." in fqdn:
        return fqdn.split(".")[0]

    return fqdn


def find_yaml_file(directory: Path) -> str:
    """
    Finds a file with the suffix .yml or .yaml in the specified directory.
    Raises an error if multiple .yml or .yaml files are found or if the directory does not exist.

    :param directory: Path to the directory to search
    :return: Filename of the .yml or .yaml file
    :raises: NotADirectoryError if the directory does not exist
             FileNotFoundError if no .yml or .yaml files are found
             ValueError if multiple .yml or .yaml files are found
    """
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"The directory {directory} does not exist.")

    yaml_files = [f for f in os.listdir(directory) if f.endswith((".yml", ".yaml"))]

    if len(yaml_files) == 0:
        raise FileNotFoundError(f"No .yml or .yaml files found in {directory}.")
    elif len(yaml_files) > 1:
        raise ValueError(f"Multiple .yml or .yaml files found in {directory}.")

    return yaml_files[0]


def get_job_details(file_path: Path) -> dict:
    """
    Reads a YAML file and returns its contents as a dictionary.

    :param file_path: Path to the YAML file
    :return: Dictionary containing the YAML file contents
    """
    try:
        job_yaml_file = find_yaml_file(file_path)
    except (FileNotFoundError, ValueError) as e:
        raise FileNotFoundError(f"Error: The file {file_path} was not found. {e}")
    except NotADirectoryError as e:
        raise NotADirectoryError(f"Error: {e}")

    try:
        with open(file_path.joinpath(job_yaml_file), "r") as file:
            data = yaml.safe_load(file)
            return data
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: The file {file_path} was not found.")
    except yaml.YAMLError as exc:
        raise yaml.YAMLError(f"Error parsing YAML file: {exc}")


def create_yaml_files(content: dict, dest_dir: str, dest_filename: str) -> None:

    with open(dest_dir.joinpath(dest_filename), "w") as yaml_file:
        yaml.dump(content, yaml_file, default_flow_style=False)


def create_or_replace_directory(directory: Path, base_directory: Path = JOB_DIR) -> None:
    """
    Creates a new directory. If the directory already exists, it removes the existing directory
    and creates a new one with the same name. Ensures the directory is within the base directory.

    :param directory: Path to the directory to create or replace
    :param base_directory: The base directory within which the new directory should be created
    :raises: ValueError if the directory is outside the base directory
    """
    # Get the absolute paths
    abs_directory = os.path.abspath(directory)
    abs_base_directory = os.path.abspath(base_directory)

    # Ensure the directory is within the base directory
    if not abs_directory.startswith(abs_base_directory):
        raise ValueError("The specified directory is outside the allowed base directory.")

    # Remove the existing directory if it exists
    if os.path.exists(abs_directory):
        shutil.rmtree(abs_directory)

    # Create the new directory
    os.makedirs(abs_directory)


def copy_directory_contents(src, dest):
    """Copy contents of one directory to another.

    Args:
        src: source directory
        dest: destination directory
    Returns:
    """

    # Ensure the destination directory exists
    try:

        os.makedirs(dest, exist_ok=True)

        for item in os.listdir(src):
            src_path = os.path.join(src, item)
            dest_path = os.path.join(dest, item)

            if os.path.isdir(src_path):
                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, dest_path)
    except Exception:
        raise OSError(f"Unable to copy contents of {src} to {dest}")


def create_ansible_playbook_dirs(working_dir: object) -> dict:
    """Create Ansible directories

    :param working_dir: jobs directory
    """
    playbook_dirs = [
        working_dir,
        working_dir.joinpath(ANSIBLE_PLAYBOOK_REL_PATH),
        working_dir.joinpath(ANSIBLE_HOST_VARS_REL_PATH),
        working_dir.joinpath(ANSIBLE_TMP_REL_PATH),
        working_dir.joinpath(ANSIBLE_TEMPLATE_REL_PATH),
        working_dir.joinpath(ANSIBLE_CHG_VALID_REL_PATH),
    ]

    # CREATE DIRECTORIES
    try:
        list(map(lambda dir_path: create_or_replace_directory(dir_path), playbook_dirs))

    except (OSError, ValueError) as o:
        raise OSError(f"Error occured while creating working environment. {o}")


def copy_jinja2_template(template_name: str, change_directory: Path) -> None:
    """
    Copy the jinja2 template provided to the ansible template directory

    :param change_directory: top level job directory
    :param template_name: jinja2 template filename

    """
    path_to_template = change_directory.parent
    template_name = path_to_template.joinpath(template_name)

    # Copy file to directory
    shutil.copy(template_name, change_directory.joinpath(ANSIBLE_TEMPLATE_REL_PATH))


def create_ansbile_task(jinja2_filename: str, change_dir: Path) -> None:
    """
    Create ansible task (yaml file) in playbooks directory.

    :param jinja2_filename: filename of jinja2 template required for change
    :param change_dir: directory where temporary ansible files are stored
    :return: task_name filename of yaml file created
    """
    # Declare Ansible Directories
    tmp_dir = change_dir.joinpath(ANSIBLE_TMP_REL_PATH)
    playbook_dir = change_dir.joinpath(ANSIBLE_PLAYBOOK_REL_PATH)

    # Declare variables needed to build task
    config_filename = jinja2_filename.replace(".j2", "config.txt")
    config_path = str(tmp_dir) + "/{{ inventory_hostname  }}_" + config_filename
    task_name = jinja2_filename.replace(".j2", "_task.yml")

    task = [
        {
            "name": "Render Configuration",
            "template": {"src": jinja2_filename, "dest": config_path},
        },
        {
            "name": "Apply Configuration",
            "cisco.ios.ios_config": {"src": config_path, "save_when": "modified"},
        },
    ]

    create_yaml_files(
        task,
        playbook_dir,
        task_name,
    )

    return task_name


# ANSIBLE HELPER FUNCTIONS
def create_main_playbook(playbook: dict, change_dir: Path, playbook_name: str) -> None:
    """
    Builds main playbook that runs all dynamically created tasks

    :param playbook The main playbook
    :param change_dir Top level directory for current change
    :param playbook_name Name for main playbook

    """
    playbook_dir = change_dir.joinpath(ANSIBLE_PLAYBOOK_REL_PATH)

    create_yaml_files(playbook, playbook_dir, playbook_name)


def create_ansible_inventory(
    hosts: list,
    change_dir: Path,
    ansible_connection: str = "network_cli",
    ansible_network_os: str = "ios",
) -> None:
    """
    Build the dictionary that will be used to create the inventory yaml file.

    :param ansible_hostname: hostname of device
    :param change_dir: directory where temporary ansible files are stored
    :param ansible_connection: defaults to network_cli but will accept others as parameters
    :param ansible_network_os: defaults to ios but will accept others as parameters

    """

    # initialize variables
    inventory = {"all": {"hosts": {}}}
    playbook_dir = change_dir.joinpath(ANSIBLE_PLAYBOOK_REL_PATH)

    for host in hosts:
        short_hostname = shortenFQDN(host)

        inventory["all"]["hosts"].update(
            {
                short_hostname: {
                    "ansible_host": host,
                    "ansible_connection": ansible_connection,
                    "ansible_network_os": ansible_network_os,
                }
            }
        )

    create_yaml_files(inventory, playbook_dir, "inventory.yml")


def create_hostvars(j2_vars: dict, change_dir: Path, short_host_name) -> None:
    """
    Build dictionary that will be used to create the Host Vars YAML file

    :param j2_vars dictionary instance with key/value var_name: value
    :param change_dir top level working directory for this change.
    :param short_host_name short name for device
    """
    hostvar_dir = change_dir.joinpath(ANSIBLE_HOST_VARS_REL_PATH)

    create_yaml_files(j2_vars, hostvar_dir, short_host_name)


def create_collect_config_tasks(change_dir) -> list:
    """Dynamically build Ansible task to take config snapshot.

    :param change_dir Top level directory for change

    """
    change_validation_dir = change_dir.joinpath(ANSIBLE_CHG_VALID_REL_PATH)
    playbook_dir = change_dir.joinpath(ANSIBLE_PLAYBOOK_REL_PATH)

    pre_change_task = [
        {
            "name": "Take Configuration Snapshot",
            "cisco.ios.ios_config": {
                "backup": "true",
                "backup_options": {
                    "filename": "pre_change_show_run_{{ inventory_hostname  }}.txt",
                    "dir_path": str(change_validation_dir),
                },
            },
        }
    ]

    post_change_task = [
        {
            "name": "Take Configuration Snapshot",
            "cisco.ios.ios_config": {
                "backup": "true",
                "backup_options": {
                    "filename": "post_change_show_run_{{ inventory_hostname  }}.txt",
                    "dir_path": str(change_validation_dir),
                },
            },
        }
    ]

    create_yaml_files(pre_change_task, playbook_dir, "gather_prechange_config_task.yml")

    create_yaml_files(post_change_task, playbook_dir, "gather_postchange_config_task.yml")


def run_ansible_playbook(username: str, password: str, playbook_path: str, inventory_path: str) -> tuple:
    """
    Run Ansible Playbooks

    :param username: username of devices to be configured
    :param password: password of devices to be configured
    :param playbook_path: location of playbook file
    :param inventory_path: location of inventory file
    :returns: ansible output and results from ansible run

    """
    os.environ["ANSIBLE_HOST_KEY_CHECKING"] = "False"

    command = [
        "ansible-playbook",
        "-i",
        inventory_path,
        playbook_path,
        "--extra-vars",
        f"ansible_user={username} ansible_password={password}",
    ]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    play_recap_found = False
    results = ""
    ansible_output = ""

    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break

        if output:
            logger.debug(output.rstrip("\r\n"))
            ansible_output += f"{output}"

            if play_recap_found:
                results += output

            elif "PLAY RECAP" in output:
                play_recap_found = True

    # Capture any remaining output after the process completes
    remaining_output, remaining_error = process.communicate()

    if remaining_output:
        ansible_output += remaining_output

    if remaining_error:
        ansible_output += f"Error: {remaining_error}"

    return ansible_output, results
