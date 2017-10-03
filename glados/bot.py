import discord
import traceback
import json
import asyncio
import inspect
import re
import math
import copy
import difflib
import os
from .Log import log
from .cooldown import Cooldown
from .tools.path import add_import_paths
from .Permissions import Permissions

comment_pattern = re.compile('`(.*?)`')


class Bot(object):
    def __init__(self):
        self.client = discord.Client()
        self.__settings = json.loads(open('settings.json').read())
        self.__original_settings = copy.deepcopy(self.__settings)
        self.__callback_tuples = list()  # list of tuples. (callback, module)
        self.__cooldown = Cooldown()

        self.__root_data_dir = self.__settings['modules'].setdefault('data', 'data')
        self.__global_data_dir = os.path.join(self.__root_data_dir, 'global_cache')
        self.__server_data_dir = None
        self.__current_server = None

        self.__settings.setdefault('command prefix', {}).setdefault('default', '.')
        self.settings.setdefault('auto join', {
            'note': 'This doesn\'t seem to work for bots, they don\'t have permission to just join servers. But this will work if the bot uses a normal user account instead.',
            'invite urls': []
        })

        self.load_modules()

        # The bot needs access to the permissions module for managing things like admins/botmods
        for cb, m in self.__callback_tuples:
            if m.full_name == 'bot.permissions.Permissions':
                self.permissions = m
                break
        else:
            self.permissions = Permissions(self, 'bot.dummy.DummyPermissions')

        @self.client.event
        async def on_message(message):

            # disallow direct messages
            if not message.server:
                return ()

            self.__set_current_server(message.server)

            # Check if this bot has been authorized by the owner to be on this server (if enabled)
            if not self.permissions.is_server_authorized() \
                    and not self.permissions.require_owner(message.author):
                return ()
            commands = self.extract_commands_from_message(message)
            commands_to_process = self.__get_commands_that_could_be_executed(message, commands)
            commands_to_process += self.__get_matches_that_could_be_executed(message)

            punish_checked = False
            user_is_punished = False
            for callback, module, content in commands_to_process:
                code = self.permissions.check_permissions(message.author, callback)
                if code < 0:
                    cooldown = self.__apply_cooldown(message)
                    if cooldown:
                        await self.client.send_message(message.author, cooldown)
                    else:
                        await self.permissions.inform_about_failure(message, code)
                    continue

                if code == Permissions.PUNISHABLE:
                    if not punish_checked and not hasattr(callback, 'spamalot'):
                        cooldown = self.__apply_cooldown(message)
                        if cooldown:
                            user_is_punished = True
                            await self.client.send_message(message.author, cooldown)
                        punish_checked = True
                    if user_is_punished:
                        continue

                # Convenient: If the help string of the command contains brackets, check that the user has supplied the
                # correct number of arguments. If not, provide help instead of executing the command.
                if hasattr(callback, 'commands'):
                    arg_string = callback.commands[-1][1]  # first command (if more than one), argument list string
                    required_arg_count = len(arg_string.split('<')) - 1
                    if len(content.split()) < required_arg_count:
                        await module.provide_help(callback.commands[-1][0], message)
                        continue

                await callback(message, content)

            # Write settings dict to disc (and print a diff) if a command changed it in any way
            self.__check_if_settings_changed()

        @self.client.event
        async def on_ready():
            await self.__auto_join_channels()
            log('Running as {}'.format(self.client.user.name))

        @self.client.event
        async def on_server_available(server):
            self.__set_current_server(server)
            self.permissions.lazy_memory_initializer()
            for m in self.get_available_modules_for(server):
                m.lazy_memory_initializer()

    async def __auto_join_channels(self):
        for url in self.settings['auto join']['invite urls']:
            log('Auto-joining {}'.format(url))
            try:
                await self.client.accept_invite(url)
            except discord.NotFound:
                log('Invite has expired')
            except discord.HTTPException as e:
                log('Got an HTTP exception: {}'.format(e))
            except discord.Forbidden:
                log('Forbidden')
        return tuple()

    @property
    def settings(self):
        return self.__settings

    @property
    def command_prefix(self):
        """
        :return: Returns the configured command prefix character(s) for commands.
        """
        prefix = self.settings['command prefix']
        try:
            return prefix[self.__current_server.id]
        except KeyError:
            return prefix.setdefault(self.__current_server.id, prefix['default'])

    @property
    def current_server(self):
        """
        :return: A reference to the currently active discord server object (from which the message originated).
        """
        return self.__current_server

    @property
    def global_data_dir(self):
        return self.__global_data_dir

    @property
    def data_dir(self):
        return self.__server_data_dir

    def __set_current_server(self, server):
        self.__current_server = server
        self.__server_data_dir = os.path.join(self.__root_data_dir, server.id)
        if not os.path.isdir(self.__server_data_dir):
            os.mkdir(self.__server_data_dir)

    def __check_if_settings_changed(self):
        if self.__settings == self.__original_settings:
            return

        a = self.__as_json(self.__original_settings).split('\n')
        b = self.__as_json(self.__settings).split('\n')

        log('Settings diff:\n{}'.format('\n'.join(difflib.unified_diff(a, b))))
        log('settings.json has been modified, you probably want to go edit it now')
        self.__save_settings()
        self.__original_settings = copy.deepcopy(self.__settings)

    def __get_commands_that_could_be_executed(self, message, commands):
        ret = list()

        # Skip processing normal commands and rules if this message came from a bot
        if message.author.bot:
            return ret

        for callback, module in self.__callback_tuples:
            if not module.is_active_for(message.server):
                continue

            # check if any issued commands match anything in the loaded callbacks
            if hasattr(callback, 'commands'):
                callback_commands = list(zip(*callback.commands))[0]
                for command, content in commands:
                    if command in callback_commands:
                        ret.append((callback, module, content))
        return ret

    def __get_matches_that_could_be_executed(self, message):
        ret = list()
        for callback, module in self.__callback_tuples:
            if not module.is_active_for(message.server):
                continue

            # process bot messages
            if message.author.bot and hasattr(callback, 'bot_rules'):
                for rule in callback.bot_rules:
                    match = rule.match(message.content)
                    if match is None:
                        continue
                    ret.append((callback, module, match))

            # Skip processing normal commands and rules if this message came from a bot
            if message.author.bot:
                continue

            # process message responses
            if hasattr(callback, 'rules'):
                for rule in callback.rules:
                    match = rule.match(message.content)
                    if match is None:
                        continue
                    ret.append((callback, module, match))

        return ret

    def __apply_cooldown(self, message):
        author = message.author.name
        if not self.__cooldown.check(author):
            margin, factor, rate = (math.ceil(x)  for x in self.__cooldown.detail_for(author))

            return (
                'You are on cooldown.  The cooldown will expire in {} seconds.\n'
                'You have reached punishment level {}.\n'
                'Your punishment level decreases by 1 every {} seconds.'
            ).format(margin, factor, rate)

        return False

    def extract_commands_from_message(self, message):
        msg = str(message.clean_content)
        cmd_prefix = self.command_prefix

        if msg.startswith(cmd_prefix):
            return [(msg[len(cmd_prefix):].split(' ', 1) + [''])[:2]]

        return [(x[len(cmd_prefix):].split(' ', 1) + [''])[:2] for x in comment_pattern.findall(msg) if
                x.startswith(cmd_prefix)]

    def load_modules(self):
        add_import_paths(self.settings.setdefault('modules', {}).setdefault('paths', [
            'modules'  # all default glados modules are in this folder
        ]))
        delayed_successes = list()
        delayed_errors = list()

        # Need whitelist and blacklist so we can assign them to modules
        whitelist = dict()
        blacklist = dict()
        for server_id, modnames in self.settings['modules'].setdefault('whitelist', {}).items():
            for modname in modnames:
                whitelist.setdefault(modname, set()).add(server_id)
        for server_id, modnames in self.settings['modules'].setdefault('blacklist', {}).items():
            for modname in modnames:
                blacklist.setdefault(modname, set()).add(server_id)

        # compose a complete set of modules that need to be loaded. These are global modules + whitelisted modules
        modules_to_load = set(self.settings['modules'].setdefault('names', [
            'bot.del.Del',
            'bot.help.Help',
            'bot.modulemanager.ModuleManager',
            'bot.permissions.Permissions',
            'bot.ping.Ping',
            'bot.prefix.Prefix',
            'bot.say.Say',
            'bot.source.Source',
            'bot.uptime.UpTime',
        ])).union(whitelist)

        # time to load all modules
        for modfullname in modules_to_load:
            m, error = self.__import_module(modfullname)
            if error:
                delayed_errors.append(error)
                continue
            delayed_successes.append('Loaded module {}'.format(modfullname))

            m.server_whitelist = whitelist.get(modfullname, set())
            m.server_blacklist = blacklist.get(modfullname, set())

        if delayed_successes:
            log('---------Loaded Modules----------\n' + '\n'.join(delayed_successes))
        if delayed_errors:
            log('---------FAILED Modules----------\n' + '\n'.join(delayed_errors))

    def __import_module(self, modfullname):
        # get class name and namespace
        modnamespace = modfullname.split('.')
        classname = modnamespace[-1]
        modnamespace = '.'.join(modnamespace[:-1])

        # try importing the module
        try:
            m = __import__(modnamespace, fromlist=[classname])
            m = getattr(m, classname)(self, modfullname)
        except:
            return None, 'Error: Failed to import module {0}\n{1}'.format(modfullname, traceback.print_exc())

        # get a list of tuples containing (callback function, module) pairs.
        callback_tuples = [(member, m) for name, member in inspect.getmembers(m, predicate=inspect.ismethod)
                           if hasattr(member, 'commands') or hasattr(member, 'rules') or hasattr(member, 'bot_rules')]
        if len(callback_tuples) > 0:
            self.__callback_tuples += callback_tuples

        return m, ''

    def get_active_modules_for(self, server):
        return set(module for c, module in self.__callback_tuples if module.is_active_for(server))

    def get_available_modules_for(self, server):
        return set(module for c, module in self.__callback_tuples if module.is_available_for(server))

    def get_blacklisted_modules_for(self, server):
        return set(module for c, module in self.__callback_tuples if module.is_blacklisted_for(server))

    @staticmethod
    def __as_json(o):
        return json.dumps(o, indent=2, sort_keys=True)

    def __save_settings(self):
        open('settings.json', 'w').write(self.__as_json(self.settings))

    async def login(self):
        log('Connecting...')
        args = list()
        token = self.settings.setdefault('login', {}).setdefault('token', 'OAuth2 Token')
        email = self.settings['login'].setdefault('email', 'address')
        password = self.settings['login'].setdefault('password', 'secretpass')
        if self.settings['login'].setdefault('method', 'token') == 'token':
            args.append(token)
        else:
            args.append(email)
            args.append(password)

        self.__check_if_settings_changed()
        await self.client.login(*args)
        await self.client.connect()

    def run(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.login())
        except:
            loop.run_until_complete(self.client.logout())
            traceback.print_exc()
        finally:
            loop.close()
            for cb, m in self.__callback_tuples:
                m.shutdown()
