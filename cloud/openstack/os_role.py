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
module: os_role
version_added: "1.9"
short_description: Manage OpenStack Identity roles
extends_documentation_fragment: openstack
description:
   - Manage role assignments for OpenStack.
options:
  state:
    description:
      - Should the resource be present or absent.
    choices: [present, absent]
    default: present
  name:
    description:
       - The name of the role to be assigned
    required: true
  user:
    description:
       - The name of the user the role should be applied to
    required: true
  project:
    description:
       - The project name in which the role should be applied to the user
    required: true
  domain:
    description:
       - The domain to operate in
    required: false
    default: None
requirements: ["shade"]
'''

EXAMPLES = '''
# Apply the admin role to the john user in the demo project
- os_role: name=admin user=john project=demo
'''

def user_exists(keystone, user):
    """Return True if user already exists."""
    return user in [x.name for x in keystone.users.list()]


def get_user(keystone, name):
    """Retrieve a user by name."""
    users = [x for x in keystone.users.list() if x.name == name]
    count = len(users)
    if count == 0:
        raise KeyError("No keystone users with name %s" % name)
    elif count > 1:
        raise ValueError("%d users with name %s" % (count, name))
    else:
        return users[0]


def get_role(keystone, name):
    """Retrieve a role by name."""
    roles = [x for x in keystone.roles.list() if x.name == name]
    count = len(roles)
    if count == 0:
        raise KeyError("No keystone roles with name %s" % name)
    elif count > 1:
        raise ValueError("%d roles with name %s" % (count, name))
    else:
        return roles[0]


def get_project_id(keystone, name):
    return get_project(keystone, name).id


def get_user_id(keystone, name):
    return get_user(keystone, name).id


def ensure_user_exists(keystone, user_name, password, email, project_name,
                       check_mode):
    """Check if user exists.

       Return (True, id) if a new user was created, (False, id) user already
       exists
    """

    # Check if project already exists
    try:
        user = get_user(keystone, user_name)
    except KeyError:
        # Tenant doesn't exist yet
        pass
    else:
        # User does exist, we're done
        return (False, user.id)

    # We now know we will have to create a new user
    if check_mode:
        return (True, None)

    project = get_project(keystone, project_name)

    user = keystone.users.create(name=user_name, password=password,
                                 email=email, project_id=project.id)
    return (True, user.id)


def ensure_role_exists(keystone, user_name, project_name, role_name,
                       check_mode):
    """Check if role exists.

       Return (True, id) if a new role was created or if the role was newly
       assigned to the user for the project. (False, id) if the role already
       exists and was already assigned to the user ofr the project.

    """
    # Check if the user has the role in the project
    user = get_user(keystone, user_name)
    project = get_project(keystone, project_name)
    roles = [x for x in keystone.roles.roles_for_user(user, project)
             if x.name == role_name]
    count = len(roles)

    if count == 1:
        # If the role is in there, we are done
        role = roles[0]
        return (False, role.id)
    elif count > 1:
        # Too many roles with the same name, throw an error
        raise ValueError("%d roles with name %s" % (count, role_name))

    # At this point, we know we will need to make changes
    if check_mode:
        return (True, None)

    # Get the role if it exists
    try:
        role = get_role(keystone, role_name)
    except KeyError:
        # Role doesn't exist yet
        role = keystone.roles.create(role_name)

    # Associate the role with the user in the admin
    keystone.roles.add_user_role(user, role, project)
    return (True, role.id)


def ensure_user_absent(keystone, user, check_mode):
    raise NotImplementedError("Not yet implemented")


def ensure_role_absent(keystone, uesr, project, role, check_mode):
    raise NotImplementedError("Not yet implemented")


def dispatch(keystone, user=None, password=None, project=None,
             project_description=None, email=None, role=None,
             state="present", endpoint=None, token=None, login_user=None,
             login_password=None, check_mode=False):
    """Dispatch to the appropriate method.

       Returns a dict that will be passed to exit_json

       project  user  role   state
       -------  ----  ----  --------
         X                   present     ensure_project_exists
         X                   absent      ensure_project_absent
         X       X           present     ensure_user_exists
         X       X           absent      ensure_user_absent
         X       X     X     present     ensure_role_exists
         X       X     X     absent      ensure_role_absent


    """
    changed = False
    id = None
    if project and not user and not role and state == "present":
        changed, id = ensure_project_exists(
            keystone, project, project_description, check_mode)
    elif project and not user and not role and state == "absent":
        changed = ensure_project_absent(keystone, project, check_mode)
    elif project and user and not role and state == "present":
        changed, id = ensure_user_exists(
            keystone, user, password, email, project, check_mode)
    elif project and user and not role and state == "absent":
        changed = ensure_user_absent(keystone, user, check_mode)
    elif project and user and role and state == "present":
        changed, id = ensure_role_exists(
            keystone, user, project, role, check_mode)
    elif project and user and role and state == "absent":
        changed = ensure_role_absent(keystone, user, project, role, check_mode)
    else:
        # Should never reach here
        raise ValueError("Code should never reach here")

    return dict(changed=changed, id=id)


def main():

    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        user=dict(required=False),
        project=dict(required=False),
        domain=dict(required=False),
        state=dict(default='present', choices=['absent', 'present']),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    name = module.params['name']
    user = module.params['user']
    project = module.params['project']
    domain = module.params['domain']
    state = module.params['state']

    check_mode = module.check_mode

    try:
        cloud = shade.openstack_cloud(**module.params)

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
