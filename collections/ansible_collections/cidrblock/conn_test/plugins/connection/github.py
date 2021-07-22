# (c) 2018 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function


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
  persistent_log_message_length_max:
    type: int
    description:
    - Specify the maximum length for an individual persistent log message.
    default: 1000
    ini:
    - section: persistent_connection
      key: log_message_length_max
    env:
    - name: ANSIBLE_PERSISTENT_LOG_MESSAGE_LENGTH_MAX
    vars:
    - name: ansible_persistent_log_message_length_max
  persistent_log_file_only:
    type: bool
    description:
    - Limit persistent log file messages to the log file specified by ansible_log_file
    - This disables persistent log messages being shown in stdout
    default: False
    ini:
    - section: persistent_connection
      key: log_file_only
    env:
    - name: ANSIBLE_PERSISTENT_LOG_FILE_ONLY
    vars:
    - name: ansible_persistent_log_file_only

"""
import logging
import os
import subprocess
from collections import namedtuple
from functools import wraps
from functools import partial

from ansible.module_utils._text import to_bytes
from ansible.module_utils.six import PY3
from ansible.module_utils.six.moves import cPickle
from ansible.errors import AnsibleConnectionFailure
from ansible.playbook.play_context import PlayContext
from ansible.plugins.connection import NetworkConnectionBase, ensure_connect
from ansible.module_utils.basic import missing_required_lib


try:
    from github import Github
    from github.GithubException import GithubException

    HAS_GITHUB = True
except ImportError:
    HAS_GITHUB = False

# Map ansible verbosity level to a python log level
# in the case surfacing dep python moduel logs is desired
ANSIBLE_VERBOSITY_TO_LOG_LEVEL = (0, 40, 30, 20, 10)


class PersistentConnection(NetworkConnectionBase):
    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(PersistentConnection, self).__init__(
            play_context, new_stdin, *args, **kwargs
        )
        self._play_context = play_context
        self._log_level = None
        self._set_up_logger()
 
    def log_with_pid(func):
        """decorator used to create a log message with PID and proc name"""

        @wraps(func)
        def wrapped(self, *args, **kwargs):
            msg = self._log_with_pid(
                msg="Called: {name}".format(name=func.__name__)
            )
            self._log_with_pid(
                msg="Called: {name}".format(name=func.__name__)
            )()
            return func(self, *args, **kwargs)

        return wrapped

    def _log_with_pid(self, msg):
        """Create a log message with the PID and process name while debugging

        :param msg: The message for the log entry
        :type msg: str
        :return: A partial that can be execed in the calling function for accutate log source
        :rtype: Callable
        """
        if self._log_level == logging.DEBUG:
            pid = os.getpid()
            name = subprocess.check_output(
                "ps -p {pid} -o cmd=".format(pid=pid), shell=True
            ).decode()
            msg = "({name}:{pid}) {msg}".format(msg=msg, name=name, pid=pid)
            return partial(self._logger.log, level=logging.DEBUG, msg=msg)
        return lambda *args: None

    def _set_up_logger(self):
        """Set up logging

        This allows the use of python style logging and logging levels
        and allow for logging from other python modules
        Log entries will be sent to the log file or log file and stdout
        based on the connection configuration
        """
        log_level = ANSIBLE_VERBOSITY_TO_LOG_LEVEL[
                    min(self._play_context.verbosity, 4)
                ]
        if log_level != self._log_level:
            self._log_level = log_level
            logging.getLogger().setLevel(self._log_level)
            # Set the log level for individual modules
            logging.getLogger("github").setLevel(self._log_level)

            # Or all imported modules
            self._logger = logging.getLogger(__name__)

            old_factory = logging.getLogRecordFactory()

            def log_bridge(*args, **kwargs):
                """Bridge python package logs to the persistent log output
                Using python log level to set the ansible verbosity
                """
                record = old_factory(*args, **kwargs)
                message = "{levelname} {name} {funcName} {message}".format(
                    **record.__dict__, message=record.getMessage()
                )
                if self.get_option("persistent_log_file_only"):
                    log_type = "log"
                else:
                    log_type = "v" * ANSIBLE_VERBOSITY_TO_LOG_LEVEL.index(
                        record.levelno
                    )
                self.queue_message(
                    log_type,
                    message[
                        0 : self.get_option("persistent_log_message_length_max")
                    ],
                )
                return record

            logging.setLogRecordFactory(log_bridge)
    
    @log_with_pid
    def set_options(self, task_keys=None, var_options=None, direct=None):
        """ Handle inbound options, it is sent each time the Connection
        is initialized, per task. The NetworkConnectionBase class handles set_options
        It is unlikely that the new options received across the socket
        need to be used here at all"""

        super().set_options(task_keys=task_keys, var_options=var_options, direct=direct)
    
    @log_with_pid
    def update_play_context(self, pc_data):
        """Handle the inbound play context, it is sent each time the Connection
        is initialized, per task

        Although it may not be possible to change ansible verbosity mid playbook
        this remains here as an example of how and why processing the updated
        playbook context may be necessary
        """
        pc_data = to_bytes(pc_data)
        if PY3:
            pc_data = cPickle.loads(pc_data, encoding="bytes")
        else:
            pc_data = cPickle.loads(pc_data)
        play_context = PlayContext()
        play_context.deserialize(pc_data)
        self._play_context = play_context
        self._set_up_logger()
      

class Connection(PersistentConnection):
    """A sample persistent connection usign the PyGithub package
    Although this Connection will be instantiated with every task
    the first instance is handed over to ansible-connection and will continue to run
    on the other side of the socket. Methods within this connection
    should be called as:

    <do this>

    from ansible.module_utils.connection import Connection

    connection_proxy = Connection(self._connection._socket_path)
    result = connection_proxy.xxx()

    If called directly, a new connection will be created for every task
    as no object persist across tasks

    <don't do this>

    result = self._connection..xxx()
    """

    # Required for identification as connection, the value is not used in this case
    # but customarily set to the connection path
    transport = "cidrblock.conn_test.github"

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(
            play_context, new_stdin, *args, **kwargs
        )
        self._github = None
        self._connected = False
        self._gh_access_token = None

    def ensure_current_token(func):
        """Wrapper to detect changes mid playbook of the GH access token
        when this occurs, set the self._connected state to false
        so the Gitub instance is reinitialized with the new access token
        """

        @wraps(func)
        def wrapped(self, *args, **kwargs):
            current = None
            try:
                current = self.get_option(option="gh_access_token")
            except KeyError:
                pass
            if current != self._gh_access_token:
                self._connected = False
                msg = "Gh access token changed, connection closed. Connection state = {state}".format(
                    state=self._connected
                )
                self._log_with_pid(msg=msg)()
            return func(self, *args, **kwargs)

        return wrapped

    @PersistentConnection.log_with_pid
    def _connect(self):
        """Although the Githu library doesn't establish a connection
        until requried, initalize the Github library with the access token
        """
        if not self._connected:
            super(Connection, self)._connect()
            self._gh_access_token = self.get_option(option="gh_access_token")
            if HAS_GITHUB:
                self._github = Github(self._gh_access_token)
            else:
                raise AnsibleConnectionFailure(
                    missing_required_lib("PyGithub").replace(
                        "module", "connection"
                    )
                )
            self._log_with_pid(msg="Github python library initialized")()
            self._connected = True

    @PersistentConnection.log_with_pid
    @ensure_current_token
    @ensure_connect
    def indirect_method(self, method, *args, **kwargs):
        """Call a method in the GH library directly by passing a string as the function name
        useful when:

        1) a 1:1 relationship exists between the action and the underlying library
        2) the library returns by default or can be instructued to return serializable data
        """
        msg = "Indirect method called: {method}".format(method=method)
        self._log_with_pid(msg=msg)()
        try:
            return getattr(self._github, method)(*args, **kwargs).raw_data
        except AttributeError as exc:
            error = "Unhandled exception in connection"
            self._logger.exception(msg=error)
            raise AnsibleConnectionFailure(message=error, orig_exc=exc)
        except GithubException as exc:
            raise AnsibleConnectionFailure(
                message="Connection error occured", orig_exc=exc
            )

    @PersistentConnection.log_with_pid
    @ensure_current_token
    @ensure_connect
    def direct_method(self, *args, **kwargs):
        """Call a method in this class by name
        useful when:

        1) Pre or post processing is required for the underlying library call
        2) Multiple library calls are necessary
        3) The library call response requires modification to be serialized
        """
        msg = "Direct method called"
        self._log_with_pid(msg=msg)()
        try:
            org = self._github.get_organization(kwargs["org"])
            return sorted(
                [
                    "{org}/{repo}".format(org=org.login, repo=repo.name)
                    for repo in org.get_repos()
                ]
            )
        except GithubException as exc:
            raise AnsibleConnectionFailure(
                message="Connection error occured", orig_exc=exc
            )
