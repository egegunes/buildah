# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Inspired from: https://github.com/redhat-openstack/khaleesi/blob/master/plugins/callbacks/human_log.py
# Further improved support Ansible 2.0

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    from ansible.plugins.callback import CallbackBase
    BASECLASS = CallbackBase
except ImportError: # < ansible 2.1
    BASECLASS = DEFAULT_MODULE.CallbackModule

import os, sys
try:
    reload  # Python 2.7
except NameError:
    try:
        from importlib import reload  # Python 3.4+
    except ImportError:
        from imp import reload
reload(sys)

try:
    import simplejson as json
except ImportError:
    import json

# Fields to reformat output for
FIELDS = ['cmd', 'command', 'msg', 'stdout',
          'stderr', 'failed', 'reason']


class CallbackModule(CallbackBase):

    """
    Ansible callback plugin for human-readable result logging
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'human_log'
    CALLBACK_NEEDS_WHITELIST = False

    def __init__(self, *args, **kwargs):
        # pylint: disable=non-parent-init-called
        BASECLASS.__init__(self, *args, **kwargs)
        if os.getenv("TEST_ARTIFACTS") is not None:
            self.artifacts = os.getenv("TEST_ARTIFACTS")
        else:
            self.artifacts = './artifacts'
        self.result_file = os.path.join(self.artifacts, 'test.log')
        if not os.path.exists(self.artifacts):
            os.makedirs(self.artifacts)
        with open(self.result_file, 'w'): pass

    def human_log(self, data, taskname, status):
        if type(data) == dict:
            with open(self.result_file, 'a') as f:
                f.write("################################################################\n")
                f.write('The status is "%s" for task: %s.\n' % (status, taskname))
                f.write("Ansible outputs: \n\n")
                for field in FIELDS:
                    no_log = data.get('_ansible_no_log', False)
                    if field in data.keys() and data[field] and no_log != True:
                        output = self._format_output(data[field], field)
                        # The following two lines are a hack to make it work with UTF-8 characters
                        if type(output) != list:
                            output = output.encode('utf-8', 'replace')
                        if type(output) == bytes:
                            output = output.decode('utf-8')

                        f.write("{0}: {1}".format(field, output.replace("\\n","\n"))+"\n")


    def _format_output(self, output, field):
        # Strip unicode
        try:
            if type(output) == unicode:
                output = output.encode(sys.getdefaultencoding(), 'replace')
        except NameError:
            pass

        # If output is a dict
        if type(output) == dict:
            return json.dumps(output, indent=2, sort_keys=True)

        # If output is a list of dicts
        if type(output) == list and type(output[0]) == dict:
            # This gets a little complicated because it potentially means
            # nested results, usually because of with_items.
            real_output = list()
            for index, item in enumerate(output):
                copy = item
                if type(item) == dict:
                    for field in FIELDS:
                        if field in item.keys():
                            copy[field] = self._format_output(item[field], field)
                real_output.append(copy)
            return json.dumps(output, indent=2, sort_keys=True)

        # If output is a list of strings
        if type(output) == list and type(output[0]) != dict:
            if field == "cmd":
                return ' '.join(output)
            return '\n'.join(output)

        # Otherwise it's a string, (or an int, float, etc.) just return it
        return str(output)

    ####### V2 METHODS ######
    def v2_on_any(self, *args, **kwargs):
        pass

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.human_log(result._result, result._task.name, "FAIL")

    def v2_runner_on_ok(self, result):
        if result._task.name == "":
            return
        self.human_log(result._result, result._task.name, "PASS")

    def v2_runner_on_skipped(self, result):
        pass

    def v2_runner_on_unreachable(self, result):
        self.human_log(result._result, result._task.name, "UNREACHABLE")

    def v2_runner_on_no_hosts(self, task):
        pass

    def v2_runner_on_async_poll(self, result):
        self.human_log(result._result, result._task.name, "")

    def v2_runner_on_async_ok(self, host, result):
        self.human_log(result._result, result._task.name, "PASS")

    def v2_runner_on_async_failed(self, result):
        self.human_log(result._result, result._task.name, "FAIL")

    def v2_playbook_on_start(self, playbook):
        pass

    def v2_playbook_on_notify(self, result, handler):
        pass

    def v2_playbook_on_no_hosts_matched(self):
        pass

    def v2_playbook_on_no_hosts_remaining(self):
        pass

    def v2_playbook_on_task_start(self, task, is_conditional):
        pass

    def v2_playbook_on_vars_prompt(self, varname, private=True, prompt=None,
                                   encrypt=None, confirm=False, salt_size=None,
                                   salt=None, default=None):
        pass

    def v2_playbook_on_setup(self):
        pass

    def v2_playbook_on_import_for_host(self, result, imported_file):
        pass

    def v2_playbook_on_not_import_for_host(self, result, missing_file):
        pass

    def v2_playbook_on_play_start(self, play):
        pass

    def v2_playbook_on_stats(self, stats):
        pass

    def v2_on_file_diff(self, result):
        pass

    def v2_playbook_on_item_ok(self, result):
        pass

    def v2_playbook_on_item_failed(self, result):
        pass

    def v2_playbook_on_item_skipped(self, result):
        pass

    def v2_playbook_on_include(self, included_file):
        pass

    def v2_playbook_item_on_ok(self, result):
        pass

    def v2_playbook_item_on_failed(self, result):
        pass

    def v2_playbook_item_on_skipped(self, result):
        pass
