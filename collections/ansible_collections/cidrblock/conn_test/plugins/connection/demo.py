
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display

display = Display()

DOCUMENTATION = """
name: cidrblock.conn_action.demo
short_description: connect to something
description:
    - desc
author: '@cidrblock'
notes:
    - notes 
options:
    host:
        description: 
            - Hostname/ip to connect to.
        required: True
        vars:
            - name: inventory_hostname
            - name: ansible_host
            - name: delegated_vars['ansible_host']
    password:
        description: Authentication password
        required: True
        vars:
            - name: ansible_password
    port:
        default: 443
        description: 
            - Remote port to connect to.
        type: int
        ini:
            - section: defaults
              key: remote_port
        env:
            - name: ANSIBLE_REMOTE_PORT
        vars:
            - name: ansible_port
    user:
        description:
            - User name with which to login to the remote server
        required: True
        ini:
            - section: defaults
              key: remote_user
        env:
            - name: ANSIBLE_REMOTE_USER
        vars:
            - name: ansible_user
        cli:
            - name: user    
"""

    

class Connection(ConnectionBase):
    ''' Connection credential shim '''

    transport = 'cidrblock.conn_action.demo'
   
    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)
        self._host = None
        self._port = None
        self._user = None
        self._password = None
      
    @property
    def connection_details(self):
        self._host = self.get_option('host')
        self._port = self.get_option('port')
        self._user = self.get_option('user')
        self._password = self.get_option('password')
        return {"host": self._host, "port": self._port, "user": self._user, "password": self._password}

    def _connect(self):
        pass
  
    def exec_command(self, cmd, in_data=None, sudoable=True):
        pass
   
    def put_file(self, in_path, out_path):
        pass

    def fetch_file(self, in_path, out_path):
        pass
 
    def close(self):
        pass

  