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
        self.__on_message_callbacks = list()
        self.__help_list = list()
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

            for callbacks in self.__on_message_callbacks:
                for callback in callbacks:

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

        return [(x[len(cmd_prefix):].split(' ', 1) + [''])[:2] for x in comment_pattern.findall(msg) if x.startswith(cmd_prefix)]

    def load_modules(self):
        add_import_paths(self.settings['modules']['paths'])
        delayed_successes = list()
        delayed_errors = list()
        for modfullname in self.settings['modules']['names']:
            modnamespace = modfullname.split('.')
            classname = modnamespace[-1]
            modnamespace = '.'.join(modnamespace[:-1])

            try:
                m = __import__(modnamespace, fromlist=[classname])
                m = getattr(m, classname)(self.settings)
            except ImportError:
                delayed_errors.append('Error: Failed to import module {0}\n{1}'.format(modfullname,
                                                                                       traceback.print_exc()))
                continue

            try:
                modhelp = [self.__command_prefix + x.get() for x in m.get_help_list()]
            except RuntimeError:
                delayed_errors.append('Error: Module {0} doesn\'t provide any help.'.format(modfullname))
                continue

            callbacks = self.__get_module_message_callbacks(m)
            if len(callbacks) == 0:
                delayed_errors.append('Error: Module {0} has no callbacks'.format(modfullname))
                continue

            delayed_successes.append('Loaded module {}'.format(modfullname))
            self.__on_message_callbacks.append(callbacks)
            self.__help_list.append('\n'.join(modhelp))

        if delayed_successes:
            print('---------Loaded Modules----------\n' + '\n'.join(delayed_successes))
        if delayed_errors:
            print('---------FAILED Modules----------\n' + '\n'.join(delayed_errors))

    def __get_core_commands_response(self, message):
        if message.content.startswith(self.__command_prefix + 'help'):
            return '==== Loaded modules ====\n' + '\n'.join(self.__help_list)

        return False

    @staticmethod
    def __get_module_message_callbacks(m):
        return [member for name, member in inspect.getmembers(m, predicate=inspect.ismethod)
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
