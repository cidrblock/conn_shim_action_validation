from __future__ import absolute_import, division, print_function
import json 


__metaclass__ = type
from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError
from ansible_collections.cidrblock.conn_test.plugins.module_utils.argspec_validate import AnsibleArgSpecValidator
from ansible_collections.cidrblock.conn_test.plugins.modules.add import (
    DOCUMENTATION,
)

ARGSPEC_CONDITIONALS = {
    "required_together": [["third", "fourth"]],
}


class ActionModule(ActionBase):
    """ action module
    """

    def __init__(self, *args, **kwargs):
        super(ActionModule, self).__init__(*args, **kwargs)
        self._result = None
    
    def _check_argspec(self):
        aav = AnsibleArgSpecValidator(
            data=self._task.args,
            schema=DOCUMENTATION,
            schema_conditionals=ARGSPEC_CONDITIONALS,
            schema_format="doc",
            name=self._task.action,
        )
        valid, errors, self._task.args = aav.validate()
        self._result["failed"] = not valid
        self._result["msg"] = errors
      
    def run(self, tmp=None, task_vars=None):        
        self._result = super(ActionModule, self).run(tmp, task_vars)
        self._check_argspec()
        self._result['connection_details'] = self._connection.connection_details
        if self._result["failed"] is not True:
            self._result['sum'] = 0
            for entry in ['first', "second", "third", "fourth"]:
                if self._task.args[entry] is not None:
                    self._result['sum'] += self._task.args[entry]
    
        return self._result
     
