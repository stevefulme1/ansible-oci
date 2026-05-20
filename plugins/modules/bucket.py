#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Steve Fulmer (@stevefulme1)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: bucket
short_description: Manage OCI object_storage bucket
version_added: "1.0.0"
description:
  - Create, update, and delete bucket resources.
  - Supports check mode and diff mode for safe operations.
author:
  - "Steve Fulmer (@stevefulme1)"
options:
  state:
    description:
      - Desired state of the bucket resource.
    type: str
    choices: ['present', 'absent']
    default: present
  id:
    description:
      - >-
        The OCID of the bucket
    type: str
extends_documentation_fragment:
  - stevefulme1.oci.auth
"""

EXAMPLES = r"""
- name: Create a bucket
  stevefulme1.oci.bucket:
    state: present
  # API: POST /buckets
- name: Update a bucket
  stevefulme1.oci.bucket:
    id: "existing_id"
    state: present
  # API:
- name: Delete a bucket
  stevefulme1.oci.bucket:
    id: "existing_id"
    state: absent
  # API: DELETE /buckets
"""

RETURN = r"""
id:
  description: >-
    The OCID
  returned: success
  type: str
display_name:
  description: >-
    Display name
  returned: success
  type: str
lifecycle_state:
  description: >-
    Lifecycle state
  returned: success
  type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.oci.plugins.module_utils.api_client import (
    Client,
    ClientError,
    argument_spec as auth_argument_spec,
)


def get_current_state(client, module):
    """Retrieve the current state of the bucket via GET."""

    # No single-resource GET endpoint; fall back to list + filter
    identifier = module.params.get("id")

    name = module.params.get("display_name")
    search_key = "display_name"
    search_value = name if identifier is None else identifier

    if search_value is None:
        return None
    try:
        items = client.get("/buckets")
        if isinstance(items, dict):
            items = items.get("results", items.get("data", items.get("items", [])))
        for item in items:
            if str(item.get(search_key)) == str(search_value):
                return item
            if str(item.get("id")) == str(search_value):
                return item
        return None
    except ClientError:
        return None


def needs_update(current, desired):
    """Compare current state against desired params and return True if an update is needed."""
    if current is None:
        return True
    for key, value in desired.items():
        if value is None:
            continue
        current_value = current.get(key)
        if current_value != value:
            return True
    return False


def build_payload(module):
    """Build the API request payload from module params."""
    payload = {}

    if module.params.get("id") is not None:
        payload["id"] = module.params["id"]

    return payload


def main():
    spec = auth_argument_spec()
    spec.update(
        dict(
            state=dict(type="str", choices=["present", "absent"], default="present"),

            id=dict(
                type="str",







            ),

        )
    )

    module = AnsibleModule(
        argument_spec=spec,
        supports_check_mode=True,

    )

    state = module.params["state"]
    result = dict(changed=False, diff=dict(before={}, after={}))

    try:
        client = Client(module)
        current = get_current_state(client, module)

        if state == "present":
            desired = build_payload(module)

            if current is None:
                # Resource does not exist — create it
                result["changed"] = True
                result["diff"]["before"] = {}
                result["diff"]["after"] = desired

                if not module.check_mode:

                    response = client.POST(
                        "/buckets",
                        data=desired,
                    )
                    result.update(response if isinstance(response, dict) else {})

            elif needs_update(current, desired):
                # Resource exists but needs updating
                result["changed"] = True
                result["diff"]["before"] = current
                result["diff"]["after"] = dict(current, **{k: v for k, v in desired.items() if v is not None})

                if not module.check_mode:

                    identifier = current.get("id")
                    path = "".replace(
                        "{id}", str(identifier)
                    )
                    response = client.put(
                        path,
                        data=desired,
                    )
                    result.update(response if isinstance(response, dict) else {})

            else:
                # Resource exists and is up-to-date

                result["id"] = current.get("id")

                result["display_name"] = current.get("display_name")

                result["lifecycle_state"] = current.get("lifecycle_state")

                pass

        elif state == "absent":
            if current is not None:
                result["changed"] = True
                result["diff"]["before"] = current
                result["diff"]["after"] = {}

                if not module.check_mode:

                    identifier = current.get("id")
                    path = "/buckets".replace(
                        "{id}", str(identifier)
                    )
                    client.delete(path)

    except ClientError as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
