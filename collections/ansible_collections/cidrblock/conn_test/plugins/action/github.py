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
        connection_proxy = Connection(self._connection._socket_path)
        if self._task.args['get'] == "user":
            # Reuses an existing connection if available, connection will remain across tasks
            self._result['user'] = connection_proxy.indirect_method('get_user')
            # Creates a new connection with every task
            # self._result['user'] = self._connection.indirect_method('get_user')
        elif self._task.args['get'] == "org":
            self._result['repos'] = connection_proxy.direct_method('org_repos', org="ansible-network")
        return self._result
     
