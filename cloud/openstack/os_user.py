#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

DOCUMENTATION = '''
---
module: os_user
version_added: "1.9"
short_description: Manage OpenStack users
extends_documentation_fragment: openstack
description:
   - Manage users for OpenStack.
options:
  state:
    description:
      - Should the resource be present or absent.
    choices: [present, absent]
    default: present
  name:
    description:
       - The name of the user that to be added/removed from OpenStack
    required: true
  password:
    description:
       - The password to be assigned to the user
    required: false
    default: None
  project:
    description:
       - The default project name or id for the user
    required: false
    default: None
  email:
    description:
       - An email address for the user
    required: false
    default: None
  enabled:
    description:
      - Should the user be enabled
    required: false
    default: 'yes'
    choices: ['yes', 'no']
requirements: ["shade"]
'''

EXAMPLES = '''
# Create a user
- os_user: user=john project=demo password=secrete
'''

def get_user_id(keystone, name):
    return get_user(keystone, name).id

def ensure_user_exists(cloud, name, password, email, project, enabled, check_mode):
    """Check if user exists.

       Return (True, user) if a new user was created, (False, user) user already
       exists
    """

    # Check if project already exists
    user = cloud.get_user(name)
    if user:
        if user['enabled'] == enabled && user['email'] == email:
            return (False, user)
        if check_mode:
            return (True, user)
        user = cloud.update_user(
            name_or_id=user['id'], email=email, enabled=enabled)
        return (True, user)

    # We now know we will have to create a new user
    if check_mode:
        return (True, None)

    user = cloud.create_user(
        name=name, password=password, email=email, project=project,
        enabled=enabled)
    return (True, user)


def ensure_user_absent(cloud, name_or_id, check_mode):
    """Ensure that a user does not exist

        Return True if the user was removed, False if it didn't exist
        in the first place
    """
    user = cloud.get_user(name_or_id)
    if not user:
        return False

    # We now know we will have to delete the project
    if check_mode:
        return True

    cloud.delete_project(user['id'])
    return True


def main():

    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        email=dict(required=False),
        project=dict(required=False),
        password=dict(required=False),
        enabled=dict(default='yes', type='bool'),
        state=dict(default='present', choices=['absent', 'present']),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    name = module.params['name']
    password = module.params['password']
    project = module.params['project']
    email = module.params['email']
    state = module.params['state']
    enabled = module.params['enabled']

    check_mode = module.check_mode

    try:
        cloud = shade.openstack_cloud(**module.params)

        if state == 'present':
            (changed, user_obj) = ensure_user_present(
                cloud, name, password, project, email, enabled, check_mode)
            module.exit_json(changed=changed, user=user_obj)
        else:
            changed = ensure_user_absent(cloud, name, check_mode)
            module.exit_json(changed=changed)
    except shade.OpenStackCloudException as e:
        if check_mode:
            # If we have a failure in check mode
            module.exit_json(changed=True,
                             msg=e.message, extra_data=e.extra_data)
        else:
            module.fail_json(msg=e.message, extra_dtata=e.extra_data)
    else:
        module.exit_json(**d)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
