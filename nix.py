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


_DEFAULT_NIX_ENV_BIN = "nix-env"


class Nix(object):
    def __init__(self, ansible_module, nix_env=_DEFAULT_NIX_ENV_BIN):
        self._module = ansible_module
        self._nix_env = nix_env

    def is_installed(self, package):
        exit_status, _, _ = self._module.run_command(
            [self._nix_env, "-q", package],
            check_rc=False,
        )
        return exit_status == 0

    def install(self, *packages):
        newly_installed = []

        for package in packages:
            if self.is_installed(package=package):
                continue
            exit_status, _, _ = self._module.run_command(
                [self._nix_env, "-i", package],
            )
            newly_installed.append(package)

        return newly_installed


def main():
    module = AnsibleModule(
        required_one_of=[["name"]],
        supports_check_mode=True,
        argument_spec=dict(
            name=dict(aliases=["pkg"]),
            state=dict(
                default="present",
                choices=["present", "installed", "absent", "removed"],
            ),
        ),
    )

    nix = Nix(ansible_module=module)

    params = module.params

    # normalize the state parameter
    if params["state"] in ["present", "installed"]:
        params["state"] = "present"
    elif params["state"] in ["absent", "removed"]:
        params["state"] = "absent"

    name = params["name"]
    if not name:
        # XXX ?
        pass
    else:
        packages = name.split(",")

        if params["state"] == "present":
            newly_installed = nix.install(*packages)
            info = dict(changed=False, msg="package(s) already installed")
            if newly_installed:
                info = dict(
                    changed=True,
                    msg="installed %s package(s)" % (len(newly_installed),),
                )
            module.exit_json(**info)
        else:
            # XXX ?
            pass


from ansible.module_utils.basic import *
main()
