#!/usr/bin/python

# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013, Benno Joy <benno@ansible.com>
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
module: os_router
short_description: Create or Delete routers from OpenStack
extends_documentation_fragment: openstack
description:
   - Create or Delete routers from OpenStack
options:
   state:
     description:
        - Indicate desired state of the resource
     choices: ['present', 'absent']
     default: present
   name:
     description:
        - Name to be give to the router
     required: true
   admin_state_up:
     description:
        - Desired admin state of the created router.
     required: false
     default: true
requirements: ["shade"]
'''

EXAMPLES = '''
# Creates a router for tenant admin
- os_router:
    state=present
    name=router1
    admin_state_up=True
'''


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        admin_state_up=dict(type='bool', default=True),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    name = module.params['name']
    admin_state_up = module.params['admin_state_up']
    state = module.params['state']

    try:
        cloud = shade.openstack_cloud(**module.params)
        router = cloud.get_router(name)

        if state == 'present':
            if not router:
                router = cloud.create_router(name, admin_state_up)
                module.exit_json(changed=True, result="Created",
                                 id=router['id'])
            else:
                module.exit_json(changed=False, result="Success",
                                 id=router['id'])

        elif state == 'absent':
            if not router:
                module.exit_json(changed=False, result="Success")
            else:
                cloud.delete_router(name)
                module.exit_json(changed=True, result="Deleted")

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
main()
