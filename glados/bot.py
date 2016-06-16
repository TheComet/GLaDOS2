import discord
import sys
import traceback
import json
import asyncio
import inspect
import re

import_paths_were_added = False
comment_pattern = re.compile('`(.*?)`')


def add_import_paths(paths):
    global import_paths_were_added
    if not import_paths_were_added:
        for path in paths:
            sys.path.append(path)
        import_paths_were_added = True


class Bot(object):
    def __init__(self):
        self.settings = json.loads(open('settings.json').read())
        self.client = discord.Client()

        self.__command_prefix = self.settings['commands']['prefix']
        self.__callback_tuples = list()  # list of tuples. (module, command_callback)
        self.load_modules()

        @self.client.event
        @asyncio.coroutine
        def on_message(message):
            if message.author.bot:
                return

            core_commands_response = self.__get_core_commands_response(message)
            if core_commands_response:
                yield from self.client.send_message(message.channel,
                                                    'I\'m sending you a direct message with a list of commands!')
                yield from self.client.send_message(message.author, core_commands_response)
                return

            for callback, module in self.__callback_tuples:

                # Does the module have a server whitelist? If so, make sure this module is allowed.
                if len(module.server_whitelist) > 0:
                    if not message.server.name in module.server_whitelist:
                        continue

                if hasattr(callback, 'commands'):
                    for command, content in self.extract_commands_from_message(message.clean_content):
                        if command in callback.commands:
                            yield from callback(self.client, message, content)
                if hasattr(callback, 'rules'):
                    for rule in callback.rules:
                        match = rule.match(message.content)
                        if match is None:
                            continue
                        yield from callback(self.client, message, match)

        @self.client.event
        @asyncio.coroutine
        def on_ready():
            print('Running as', self.client.user.name)

    def extract_commands_from_message(self, msg):
        msg = str(msg)
        cmd_prefix = self.settings['commands']['prefix']

        if msg.startswith(cmd_prefix):
            return [(msg[len(cmd_prefix):].split(' ', 1) + [''])[:2]]

        return [(x[len(cmd_prefix):].split(' ', 1) + [''])[:2] for x in comment_pattern.findall(msg) if
                x.startswith(cmd_prefix)]

    def load_modules(self):
        add_import_paths(self.settings['modules']['paths'])
        delayed_successes = list()
        delayed_errors = list()

        # load global modules
        for modfullname in self.settings['modules']['names']:
            result = self.__import_module(modfullname)
            if not result is None:
                delayed_errors.append(result)
            else:
                delayed_successes.append('Loaded global module {}'.format(modfullname))

        # load server whitelisted modules
        for server, modlist in self.settings['modules']['server specific'].items():
            for modfullname in modlist:
                result = self.__import_module(modfullname, server)
                if not result is None:
                    delayed_errors.append(result)
                else:
                    delayed_successes.append('Loaded whitelisted module {0} for server {1}'.format(modfullname, server))

        if delayed_successes:
            print('---------Loaded Modules----------\n' + '\n'.join(delayed_successes))
        if delayed_errors:
            print('---------FAILED Modules----------\n' + '\n'.join(delayed_errors))

    def __import_module(self, modfullname, server=None):
        # was this module name already loaded? This checks if "modfullname" is in any of the loaded modules
        # mod.namespace attribute.
        if len(self.__callback_tuples) > 0:
            existing_module = [m for callback, m in self.__callback_tuples if m.full_name == modfullname]
            if existing_module:
                # No need to load again. However, maybe the server has changed?
                if not server is None:
                    if not server in existing_module[0].server_whitelist:
                        existing_module[0].server_whitelist.append(server)
                return

        # get class name and namespace
        modnamespace = modfullname.split('.')
        classname = modnamespace[-1]
        modnamespace = '.'.join(modnamespace[:-1])

        # try importing the module
        try:
            m = __import__(modnamespace, fromlist=[classname])
            m = getattr(m, classname)(self.settings)
        except ImportError:
            return 'Error: Failed to import module {0}\n{1}'.format(modfullname,
                                                                    traceback.print_exc())

        # get the module's help list for the global .help command
        try:
            modhelp = [self.__command_prefix + x.get() for x in m.get_help_list()]
        except RuntimeError:
            return 'Error: Module {0} doesn\'t provide any help.'.format(modfullname)

        # set server whitelist
        if not server is None:
            m.server_whitelist.append(server)

        # set full name
        m.full_name = modfullname

        # get a list of tuples containing (callback function, module) pairs.
        callback_tuples = self.__get_callback_tuples(m)
        if len(callback_tuples) == 0:
            return 'Error: Module {0} has no callbacks'.format(modfullname)

        self.__callback_tuples += callback_tuples

    def __get_core_commands_response(self, message):
        if message.content.startswith(self.__command_prefix + self.settings['commands']['help']):
            # creates a list of relevant modules
            relevant_modules = set(module for c, module in self.__callback_tuples
                                   if len(module.server_whitelist) == 0
                                   or message.server.name in module.server_whitelist)
            # generates a list of help strings from the modules
            relevant_help = [self.__command_prefix + hlp.get() for mod in relevant_modules for hlp in mod.get_help_list()]
            return '==== Loaded modules ====\n' + '\n'.join(sorted(relevant_help))

        return False

    @staticmethod
    def __get_callback_tuples(m):
        return [(member, m) for name, member in inspect.getmembers(m, predicate=inspect.ismethod)
                if hasattr(member, 'commands') or hasattr(member, 'rules')]

    @asyncio.coroutine
    def main_task(self):
        yield from self.client.login(self.settings['login']['token'])
        yield from self.client.connect()

    def run(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.main_task())
        except:
            loop.run_until_complete(self.client.logout())
            raise
        finally:
            loop.close()
