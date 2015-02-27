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
module: os_project
version_added: "1.9"
short_description: Manage OpenStack Identity (keystone) projects
extends_documentation_fragment: openstack
description:
   - Manage project in OpenStack.
options:
  state:
    description:
      - Should the resource be present or absent.
    choices: [present, absent]
    default: present
  project:
    description:
      - The project name or id that has to be added/removed
    required: true
  description:
    description:
      - A description for the project
    required: false
    default: None
  enabled:
    description:
      - Should the project be enabled
    required: false
    default: 'yes'
    choices: ['yes', 'no']
requirements: ["shade"]
'''

EXAMPLES = '''
# Create a project
- os_project: name=demo description="Default Tenant"
'''


def get_project(keystone, name_or_id):
    """Retrieve a project by name or id."""
    projects = [x for x in keystone.projects.list()
                if x.id = name_or_id or x.name == name_or_id]
    if projects:
        return projects[0]
    return None


def ensure_project_exists(
        cloud, name, description, enabled, check_mode):
    """Ensure that a project exists.

       Return (True, id) if a new project was created, (False, None) if it
       already existed.
    """

    # Check if project already exists
    changed = False
    project = cloud.get_project(name)
    if project:
        if (project['description'] != description
                or project['enabled'] != enabled):
            changed = True
            # We need to update the project description
            if not check_mode:
                project = cloud.update_project(
                    project['id'], description=description, enabled=enabled)
        return (changed, project)
        
    # We now know we will have to create a new project
    changed = True
    if check_mode:
        return (changed, None)

    ks_project = cloud.create_project(
        name=name, description=description, enabled=enabled)
    return (changed, ks_project)


def ensure_project_absent(cloud, name, check_mode):
    """Ensure that a project does not exist

        Return True if the project was removed, False if it didn't exist
        in the first place
    """
    project = cloud.get_project(project_name)
    if not project:
        return False

    # We now know we will have to delete the project
    if check_mode:
        return True

    cloud.delete_project(project['id'])
    return True


def main():

    argument_spec = openstack_full_argument_spec(
        project=dict(required=True),
        description=dict(required=False),
        state=dict(default='present', choices=['absent', 'present']),
        enabled=dict(default='yes', type='bool'),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    project = module.params['project']
    description = module.params['description']
    state = module.params['state']
    enabled = module.params['enabled']

    check_mode = module.check_mode

    try:
        cloud = shade.openstack_cloud(**module.params)

        if state == "present":
            changed, project_obj = ensure_project_exists(
                cloud, project, description, enabled, check_mode)
            module.exit_json(changed=changed, project=project_obj)
        elif state == "absent":
            changed = ensure_project_absent(cloud, project, check_mode)
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
