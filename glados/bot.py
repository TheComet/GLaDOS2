import discord
import traceback
import json
import asyncio
import inspect
import re
import math
import copy
import difflib
from .Log import log
from .cooldown import Cooldown
from .tools.path import add_import_paths
from .Permissions import Permissions

comment_pattern = re.compile('`(.*?)`')


class Bot(object):
    def __init__(self):
        self.settings = json.loads(open('settings.json').read())
        self.original_settings = copy.deepcopy(self.settings)
        self.client = discord.Client()

        self.__command_prefix = self.settings.setdefault('commands', {}).setdefault('prefix', '.')
        self.__callback_tuples = list()  # list of tuples. (callback, module)
        self.__cooldown = Cooldown()
        self.load_modules()

        # The bot needs access to the permissions module for managing things like admins/botmods
        for cb, m in self.__callback_tuples:
            if m.full_name == 'bot.permissions.Permissions':
                self.permissions = m
                break
        else:
            self.permissions = Permissions()
            self.permissions.init_module(self, 'DummyPermissions', self.settings)

        @self.client.event
        async def on_message(message):

            # disallow direct messages
            if not message.server:
                return ()

            # required for permission server isolation
            self.permissions.set_current_server(message.server.id)

            # Check if this bot has been authorized by the owner to be on this server
            if not self.permissions.is_server_authorized() \
                    and not self.permissions.is_owner(message.author):
                return ()

            commands = self.extract_commands_from_message(message.clean_content)
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

                module.set_current_server(message.server.id)  # required for server isolation
                await callback(message, content)

            self.__check_if_settings_changed()

        @self.client.event
        async def on_ready():
            # TODO this doesn't seem to work, bots don't have permission to just join servers
            #await self.__auto_join_channels()
            log('Running as {}'.format(self.client.user.name))

    async def __auto_join_channels(self):
        invite_urls = [url for name, url in self.settings['auto join'].items()]
        for url in invite_urls:
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

    def __check_if_settings_changed(self):
        if self.settings == self.original_settings:
            return

        a = self.__as_json(self.original_settings).split('\n')
        b = self.__as_json(self.settings).split('\n')

        log('Settings diff:\n{}'.format('\n'.join(difflib.unified_diff(a, b))))
        log('settings.json has been modified, you probably want to go edit it now')
        self.__save_settings()
        self.original_settings = copy.deepcopy(self.settings)

    def __get_commands_that_could_be_executed(self, message, commands):
        ret = list()

        # Skip processing normal commands and rules if this message came from a bot
        if message.author.bot:
            return ret

        for callback, module in self.__callback_tuples:
            # Does the module have a server whitelist? If so, make sure this module is allowed.
            if len(module.server_whitelist) > 0:
                if message.server and not message.server.id in module.server_whitelist:
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
            # Does the module have a server whitelist? If so, make sure this module is allowed.
            if len(module.server_whitelist) > 0:
                if message.server and not message.server.id in module.server_whitelist:
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

    def extract_commands_from_message(self, msg):
        msg = str(msg)
        cmd_prefix = self.settings['commands']['prefix']

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

        # load global modules
        for modfullname in self.settings['modules'].setdefault('names', [
            'bot.permissions.Permissions',
            'bot.help.Help',
            'bot.ping.Ping',
            'bot.uptime.UpTime',
            'bot.say.Say'
        ]):
            result = self.__import_module(modfullname)
            if result is not None:
                delayed_errors.append(result)
            else:
                delayed_successes.append('Loaded global module {}'.format(modfullname))

        # load server whitelisted modules
        for server, modlist in self.settings['modules'].setdefault('server specific', {
            'server id': []
        }).items():
            for modfullname in modlist:
                result = self.__import_module(modfullname, server)
                if not result is None:
                    delayed_errors.append(result)
                else:
                    delayed_successes.append('Loaded whitelisted module {0} for server {1}'.format(modfullname, server))

        if delayed_successes:
            log('---------Loaded Modules----------\n' + '\n'.join(delayed_successes))
        if delayed_errors:
            log('---------FAILED Modules----------\n' + '\n'.join(delayed_errors))

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
            m = getattr(m, classname)()
        except ImportError:
            return 'Error: Failed to import module {0}\n{1}'.format(modfullname,
                                                                    traceback.print_exc())

        # set server whitelist
        if server is not None:
            m.server_whitelist.append(server)

        # set module properties
        m.init_module(self, modfullname, self.settings)

        # get a list of tuples containing (callback function, module) pairs.
        callback_tuples = self.__get_callback_tuples(m)
        if len(callback_tuples) > 0:
            self.__callback_tuples += callback_tuples

    def get_loaded_modules(self, server):
        return set(module for c, module in self.__callback_tuples
                        if len(module.server_whitelist) == 0
                        or server and server.name in module.server_whitelist)

    @staticmethod
    def __as_json(o):
        return json.dumps(o, indent=2, sort_keys=True)

    def __save_settings(self):
        open('settings.json', 'w').write(self.__as_json(self.settings))

    @staticmethod
    def __get_callback_tuples(m):
        return [(member, m) for name, member in inspect.getmembers(m, predicate=inspect.ismethod)
                if hasattr(member, 'commands') or hasattr(member, 'rules') or hasattr(member, 'bot_rules')]

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
