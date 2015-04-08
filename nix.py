#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

DOCUMENTATION = """
---
module: nix
short_description: Manage packages with Nix

"""

EXAMPLES = """
# Install package foo
- nix: name=foo state=present
"""

class Nix(object):
    def __init__(self, ansible_module, nix_env="nix-env"):
        self.nix_env = nix_env
        self.ansible_module = ansible_module
        self.services = []

    def enable(self, *packages):
        self.services.extend(packages)

    def is_enabled(self, package):
        return False

    def install(self, *packages):
        newly_installed = []

        for package in packages:
            if self.is_installed(package=package):
                continue
            exit_status, _, _ = self.ansible_module.run_command(
                [self.nix_env, "-i", package],
            )
            newly_installed.append(package)

        return newly_installed

    def is_installed(self, package):
        exit_status, _, _ = self.ansible_module.run_command(
            [self.nix_env, "-q", package],
            check_rc=False,
        )
        return exit_status == 0


def main(ansible_module):
    params = ansible_module.params

    facts = ansible_facts(ansible_module)
    assert "services" not in facts

    nix = Nix(ansible_module=ansible_module)
    act_on, will_change = action_for(nix, params["state"])

    changed, packages = [], params["name"].split(",")
    for package in packages:
        package = package.strip()
        if not package or not will_change(package):
            continue

        act_on(package)
        changed.append(package)

    if changed:
        msg="installed " + ", ".join(changed)
    else:
        msg="package(s) already installed"

    ansible_module.exit_json(
        ansible_facts={"services" : nix.services},
        changed=bool(changed),
        msg=msg,
    )


def action_for(nix, state):
    if state == "enabled":
        return nix.enable, lambda package : not nix.is_enabled(package)
    elif state == "present":
        return nix.install, lambda package : not nix.is_installed(package)
    else:
        raise ValueError("Unknown state: %r" % (state,))


# Ansible is doing weird things, and cat's stuff into this module to
# replace the below things. So yes you need import *.
from ansible.module_utils.basic import *
from ansible.module_utils.facts import *


# More weird, the module has to literally be called module for this to work.
module = AnsibleModule(
    required_one_of=[["name"]],
    supports_check_mode=True,
    argument_spec=dict(
        name={},
        state={"default" : "enabled", "choices" : ["enabled", "present"]},
    ),
)
main(ansible_module=module)
