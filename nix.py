#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: nix
short_description: Manage packages with Nix

'''

EXAMPLES = '''
# Install package foo
- nix: name=foo state=present
'''

import os


NIX_ENV_BIN = os.expanduser("~/.nix-profile/bin/nix-env")


def query_package(module, name, state="present"):
    if state == "present":
        rc, _, _ = module.run_command(
            [NIX_ENV_BIN, "-q", name],
            check_rc=False,
        )
        return rc == 0
    # XXX: Presumably there's stuff here?


def install_packages(module, packages):
    installed = []

    for package in packages:
        if query_package(module, package):
            continue

        cmd = "nix-env -i %s" % package
        rc, stdout, stderr = module.run_command(cmd, check_rc=False)

        if rc != 0:
            module.fail_json(msg="failed to install %s" % (package))

        installed.append(package)

    info = dict(changed=False, msg="package(s) already installed")
    if installed:
        info = dict(
            changed=True,
            msg="installed %s package(s)" % (len(installed),),
        )
    module.exit_json(**info)


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

    if not os.path.exists(NIX_ENV_BIN):
        module.fail_json(msg="cannot find nix-env, looking for %s" %
                         (NIX_ENV_BIN))

    p = module.params

    # normalize the state parameter
    if p['state'] in ['present', 'installed']:
        p['state'] = 'present'
    elif p['state'] in ['absent', 'removed']:
        p['state'] = 'absent'

    if p['name']:
        pkgs = p['name'].split(',')

        if p['state'] == 'present':
            install_packages(module, pkgs)


from ansible.module_utils.basic import *
main()
