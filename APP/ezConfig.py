# -*- coding: utf-8 -*-

__author__ = ["Jason Smith"]
__credits__ = ["Jason Smith"]
__email__ = ["jasons2@cisco.com"]

# TEMP IMPORTS
from pprint import pprint


# IMPORT PKGS/MODULES
import sys
from logging import INFO, DEBUG

# IMPORT CONSTANTS
from CONSTANTS import PROJECT_DIR
from CONSTANTS import GATHER_CONFIG_BEFORE_TASK
from CONSTANTS import GATHER_CONFIG_AFTER_TASK
from CONSTANTS import ANSIBLE_PLAYBOOK_REL_PATH


# IMPORT HELPER FUNCTIONS
from HELPERS import getArgs
from HELPERS import get_project_details
from HELPERS import shortenFQDN
from HELPERS import create_ansible_playbook_dirs
from HELPERS import copy_jinja2_template
from HELPERS import create_ansbile_task
from HELPERS import create_collect_config_tasks
from HELPERS import create_ansible_inventory
from HELPERS import create_hostvars
from HELPERS import create_main_playbook
from HELPERS import run_ansible_playbook
from HELPERS import setupLogging


def main() -> None:

    logger = setupLogging(__name__, "ezConfig", INFO, DEBUG)
    args = getArgs()
    project_home = PROJECT_DIR.joinpath(args.project)

    print()
    print(f"Starting {args.project}")

    try:
        changes_to_make = get_project_details(project_home)
    except (FileNotFoundError, ValueError, NotADirectoryError) as err:
        logger.info(err)
        logger.info("Error found. exiting...")
        sys.exit()

    for change in changes_to_make:
        print(f"Preparing {change['description']}")
        change_dir = project_home.joinpath(change["name"].replace(" ", "_"))
        main_playbook_name = change["name"].replace(" ", "_") + ".yml"

        # Create Ansible Working Environment
        try:
            create_ansible_playbook_dirs(change_dir)
        except (OSError, ValueError) as err:
            print(err)
            print("exiting...")
            sys.exit()
        except Exception as e:
            print(e)

        # Copy Users jinja2 template into ansible playbook
        copy_jinja2_template(change["jinja2_template"], change_dir)
        logger.debug(f"Building Jinja2 templates complete")

        # Build Ansible Tasks
        create_collect_config_tasks(change_dir)
        task_name = create_ansbile_task(change["jinja2_template"], change_dir)
        logger.debug(f"Building task {task_name} complete")

        # Build Main playbook
        main_playbook = [
            {
                "hosts": "all",
                "name": "Implement defined automation tasks",
                "vars": {"run_other_playbook": True},
                "tasks": [
                    GATHER_CONFIG_BEFORE_TASK,
                    {
                        "name": change["description"],
                        "include_tasks": task_name,
                        "when": "run_other_playbook",
                    },
                    GATHER_CONFIG_AFTER_TASK,
                ],
            }
        ]

        # Build Ansible Inventory
        create_ansible_inventory(change["device_names"], change_dir)
        logger.debug(f"Building inventory file complete")

        # Build Host Vars File
        for device in change["device_names"]:
            short_hostname = shortenFQDN(device)
            if "variables" in change:
                create_hostvars(change["variables"], change_dir, short_hostname + ".yml")
        logger.debug(f"Building hostvars file complete")
        # Create Main playbook
        create_main_playbook(main_playbook, change_dir, main_playbook_name)

        path_to_main_playbook = change_dir.joinpath(ANSIBLE_PLAYBOOK_REL_PATH).joinpath(main_playbook_name)
        path_to_inventory = change_dir.joinpath(ANSIBLE_PLAYBOOK_REL_PATH).joinpath("inventory.yml")

        print(f"Applying {change['description']}")
        ansible_output, play_recap = run_ansible_playbook(
            args.username, args.password, str(path_to_main_playbook), path_to_inventory
        )

        print(play_recap)


if __name__ == "__main__":
    main()


"""
# Example usage
if __name__ == "__main__":
    base_directory_path = 'path/to/your/base_directory'
    directory_path = os.path.join(base_directory_path, 'new_directory')
    try:
        create_or_replace_directory(directory_path, base_directory_path)
        print(f"Directory {directory_path} has been created or replaced.")
    except ValueError as e:
        print(e)
"""
