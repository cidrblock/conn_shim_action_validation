from __future__ import absolute_import, division, print_function
import json 


__metaclass__ = type
from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError
from ansible.module_utils.connection import Connection


class ActionModule(ActionBase):
    """ action module
    """

    def __init__(self, *args, **kwargs):
        super(ActionModule, self).__init__(*args, **kwargs)
        self._result = None
       
    def run(self, tmp=None, task_vars=None): 
        self._result = super(ActionModule, self).run(tmp, task_vars)
        github = Connection(self._connection._socket_path)
        if self._task.args['get'] == "user":
            self._result['user'] = github.exec('get_user')
        elif self._task.args['get'] == "org":
            self._result['repos'] = github.exec('org_repos', org="ansible-network")
        return self._result
     
