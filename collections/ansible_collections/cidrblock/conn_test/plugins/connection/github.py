# (c) 2018 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from functools import partial

__metaclass__ = type

DOCUMENTATION = """
author: Ansible Networking Team
connection: cidrblock.conn_test.github
short_description: Connect to github
description:
- This connection plugin provides a connection to remote devices over a HTTP(S)-based
  api.
version_added: 1.0.0
options:
  gh_access_token:
    type: str
    description:
    - The github access token
    required: True
    vars:
    - name: ansible_gh_access_token
    env:
    - name: ANSIBLE_GH_ACCESS_TOKEN
  persistent_connect_timeout:
    type: int
    description:
    - Configures, in seconds, the amount of time to wait when trying to initially
      establish a persistent connection.  If this value expires before the connection
      to the remote device is completed, the connection will fail.
    default: 30
    ini:
    - section: persistent_connection
      key: connect_timeout
    env:
    - name: ANSIBLE_PERSISTENT_CONNECT_TIMEOUT
    vars:
    - name: ansible_connect_timeout
  persistent_command_timeout:
    type: int
    description:
    - Configures, in seconds, the amount of time to wait for a command to return from
      the remote device.  If this timer is exceeded before the command returns, the
      connection plugin will raise an exception and close.
    default: 60
    ini:
    - section: persistent_connection
      key: command_timeout
    env:
    - name: ANSIBLE_PERSISTENT_COMMAND_TIMEOUT
    vars:
    - name: ansible_command_timeout
  persistent_log_messages:
    type: boolean
    description:
    - This flag will enable logging the command executed and response received from
      target device in the ansible log file. For this option to work 'log_path' ansible
      configuration option is required to be set to a file path with write access.
    - Be sure to fully understand the security implications of enabling this option
      as it could create a security vulnerability by logging sensitive information
      in log file.
    default: true
    ini:
    - section: persistent_connection
      key: log_messages
    env:
    - name: ANSIBLE_PERSISTENT_LOG_MESSAGES
    vars:
    - name: ansible_persistent_log_messages
"""
import json
from collections import namedtuple



from ansible.errors import AnsibleConnectionFailure, AnsibleError
from ansible.module_utils._text import to_bytes
from ansible.module_utils.six import PY3
from ansible.module_utils.urls import open_url
from ansible.playbook.play_context import PlayContext
from ansible.plugins.loader import httpapi_loader
from ansible.plugins.connection import NetworkConnectionBase, ensure_connect

from ansible.module_utils.basic import missing_required_lib


class Manager():
    def __init__(self, access_token):
        self._access_token = access_token
        self._errors = []
        self._messages = ["Github connection init"]
        self._result = {}

    @property
    def response(self):
        result = {"errors": self._errors, "messages": self._messages, "result": self._result}
        return result

    def initialize(self):
        try:
            from github import Github
            self._messages.append('Github python library imported successfully')
        except ImportError:
            self._errors.append(missing_required_lib('PyGithub').replace("module", "connection"))
            return self.response
        self._github = Github(self._access_token)
        return self.response
    
    def github(self, method, *args, **kwargs):
        self._errors = []
        self._messages = ["Github connection messages cleared"]
        self._result = {}
        self._messages.append("Calling {method} in github library".format(method=method))
        if hasattr(self, method):
            self._result = getattr(self, method)(*args, **kwargs)
        else:
            try:
                self._result = getattr(self._github, method)(*args, **kwargs).raw_data
            except AttributeError as exc:
                self._errors.append(str(exc))
                return self.response

        return self.response
    
    def org_repos(self, *args, **kwargs):
        org = self._github.get_organization(kwargs['org'])
        return sorted(["{org}/{repo}".format(org=org.login, repo=repo.name) for repo in org.get_repos()])
    

class Connection(NetworkConnectionBase):

    transport = "cidrblock.conn_test.github"
    has_pipelining = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(
            play_context, new_stdin, *args, **kwargs
        )
        self.manager = None
        self._connected = False

    def _connect(self):
        if not self._connected:
            super(Connection, self)._connect()
            self.manager = Manager(self.get_option('gh_access_token'))
            result = self.manager.initialize()
            if not result['errors']:
                self._connected = True
            return self.post_process_result(result)


    def close(self):
        if self._connected:
            self.queue_message("vvvv", "closing connection")
            self.logout()
        super(Connection, self).close()

    @ensure_connect
    def exec(self, method, *args, **kwargs):
        result = self.manager.github(method, *args, **kwargs)
        return self.post_process_result(result)
        
    def post_process_result(self, result):
        for message in result['messages']:
            self.queue_message("log", message)
        if result['errors']:
            raise AnsibleConnectionFailure(message=" ".join(result['errors']))
        return result['result']

        
