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
from os.path import isfile
comment_pattern = re.compile('`(.*?)`')


server_lock = asyncio.Lock()


class ServerInstance(object):
    def __init__(self, client, settings, server):
        self.client = client
        self.settings = settings
        self.server = server
        self.callbacks = list()
        self.permissions = None
        self.__cooldown = Cooldown()

        self.root_data_dir = self.settings.setdefault('modules', {}).setdefault('data', 'data')
        self.global_data_dir = os.path.join(self.root_data_dir, 'global_cache')
        self.local_data_dir = os.path.join(self.root_data_dir, self.server.id)

    def instantiate_modules(self, class_list, whitelist, blacklist):
        for full_name, class_ in sorted(class_list):
            if len(whitelist) > 0 and full_name not in whitelist:
                continue
            log('Instantiating module {} for server {}'.format(full_name, self.server.name))
            obj = class_(self, full_name)
            self.callbacks += [(obj, member) for name, member in inspect.getmembers(obj, predicate=inspect.ismethod)
                         if hasattr(member, 'commands') or hasattr(member, 'rules') or hasattr(member, 'bot_rules')]

            # Need access to the permissions module for managing things like admins/botmods
            if full_name == 'bot.permissions.Permissions':
                self.permissions = obj

        if self.permissions is None:
            self.permissions = Permissions(self, 'bot.dummy.DummyPermissions')

        if not os.path.isdir(self.global_data_dir):
            os.mkdir(self.global_data_dir)
        if not os.path.isdir(self.local_data_dir):
            os.mkdir(self.local_data_dir)

    @property
    def command_prefix(self):
        """
        :return: Returns the configured command prefix character(s) for commands.
        """
        prefix = self.settings['command prefix']
        try:
            return prefix[self.server.id]
        except KeyError:
            return prefix.setdefault(self.server.id, prefix['default'])

    @property
    def active_modules(self):
        return set(obj for obj, c in self.callbacks if not obj.is_blacklisted)

    @property
    def available_modules(self):
        return set(obj for obj, c in self.callbacks)

    @property
    def blacklisted_modules(self):
        return set(obj for obj, c in self.callbacks if obj.is_blacklisted)

    def __get_commands_that_could_be_executed(self, message, commands):
        ret = list()

        # Bots can't trigger commands
        if message.author.bot:
            return ret

        # check if any issued commands match anything in the loaded callbacks
        for obj, callback in self.callbacks:
            if obj.is_blacklisted:
                continue
            if hasattr(callback, 'commands'):
                callback_commands = list(zip(*callback.commands))[0]
                for command, content in commands:
                    if command in callback_commands:
                        ret.append((obj, callback, content))
        return ret

    def __get_matches_that_could_be_executed(self, message):
        ret = list()
        for obj, callback in self.callbacks:
            if obj.is_blacklisted:
                continue

            # process bot messages
            if message.author.bot and hasattr(callback, 'bot_rules'):
                for rule, ignorecommands in callback.bot_rules:
                    if ignorecommands and message.content.startswith(self.server.command_prefix):
                        continue
                    match = rule.match(message.content)
                    if match is None:
                        continue
                    ret.append((callback, match))

            # Bots can't trigger normal rules
            if message.author.bot:
                continue

            # process message responses
            if hasattr(callback, 'rules'):
                for rule, ignorecommands in callback.rules:
                    if ignorecommands and message.content.startswith(self.server.command_prefix):
                        continue
                    match = rule.match(message.content)
                    if match is None:
                        continue
                    ret.append((obj, callback, match))

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

    async def process_message(self, message):
        # Check if this bot has been authorized by the owner to be on this server (if enabled)
        if not self.permissions.is_server_authorized() \
            and not self.permissions.require_owner(message.author):
            return ()
        commands = self.extract_commands_from_message(message)
        commands_to_process = self.__get_commands_that_could_be_executed(message, commands)
        commands_to_process += self.__get_matches_that_could_be_executed(message)

        punish_checked = False
        user_is_punished = False
        for obj, callback, content in commands_to_process:
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
                    await obj.provide_help(callback.commands[-1][0], message)
                    continue

            await callback(message, content)


class Bot(object):
    def __init__(self):
        self.client = discord.Client()
        if isfile('settings.json'):
            self.settings = json.loads(open('settings.json').read())
        else:
            self.settings = dict()
        self.__original_settings = copy.deepcopy(self.settings)
        self.class_list = list()  # (fullname, class)
        self.server_instances = dict()
        self.whitelist = dict()
        self.blacklist = dict()

        self.settings.setdefault('command prefix', {}).setdefault('default', '.')
        self.settings.setdefault('auto join', {
            'note': 'This doesn\'t seem to work for bots, they don\'t have permission to just join servers. But this will work if the bot uses a normal user account instead.',
            'invite urls': []
        })

        self.load_classlist()

        @self.client.event
        async def on_message(message):
            # disallow direct messages
            if not message.server:
                return ()

            await self.server_instances[message.server.id].process_message(message)

            # Write settings dict to disc (and print a diff) if a command changed it in any way
            self.__check_if_settings_changed()

        @self.client.event
        async def on_ready():
            await self.__auto_join_channels()
            log('Running as {}'.format(self.client.user.name))

        @self.client.event
        async def on_server_available(server):
            log('Server {} became available'.format(server.name))
            s = ServerInstance(self.client, self.settings, server)
            s.instantiate_modules(self.class_list, self.whitelist, self.blacklist)
            self.server_instances[server.id] = s

        @self.client.event
        async def on_server_unavailable(server):
            log('Server {} became unavailable, cleaning up instances'.format(server.name))
            self.server_instances.pop(server.id)

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

    def __check_if_settings_changed(self):
        if self.settings == self.__original_settings:
            return

        a = self.__as_json(self.__original_settings).split('\n')
        b = self.__as_json(self.settings).split('\n')

        log('Settings diff:\n{}'.format('\n'.join(difflib.unified_diff(a, b))))
        log('settings.json has been modified, you probably want to go edit it now')
        self.__save_settings()
        self.__original_settings = copy.deepcopy(self.settings)

    def load_classlist(self):
        add_import_paths(self.settings.setdefault('modules', {}).setdefault('paths', [
            'modules'  # all default glados modules are in this folder
        ]))

        # Need whitelist and blacklist so we know which classes to load
        for server_id, modnames in self.settings['modules'].setdefault('whitelist', {}).items():
            for modname in modnames:
                self.whitelist.setdefault(modname, set()).add(server_id)
        for server_id, modnames in self.settings['modules'].setdefault('blacklist', {}).items():
            for modname in modnames:
                self.blacklist.setdefault(modname, set()).add(server_id)

        # compose a complete set of modules that need to be loaded. These are global modules + whitelisted modules
        modules_to_import = set(self.settings['modules'].setdefault('names', [
            'bot.del.Del',
            'bot.help.Help',
            'bot.modulemanager.ModuleManager',
            'bot.permissions.Permissions',
            'bot.ping.Ping',
            'bot.prefix.Prefix',
            'bot.say.Say',
            'bot.source.Source',
            'bot.uptime.UpTime',
        ])).union(self.whitelist)

        # time to load all modules
        for modfullname in sorted(modules_to_import):

            # get class name and namespace
            modnamespace = modfullname.split('.')
            classname = modnamespace[-1]
            modnamespace = '.'.join(modnamespace[:-1])

            # try importing the module
            try:
                m = __import__(modnamespace, fromlist=[classname])
                self.class_list.append((modfullname, getattr(m, classname)))
            except:
                log('Error: Failed to import class {0}\n{1}'.format(modfullname, traceback.print_exc()))
                continue
            log('Imported class {}'.format(modfullname))

    @staticmethod
    def __as_json(o):
        return json.dumps(o, indent=2, sort_keys=True)

    def __save_settings(self):
        open('settings.json', 'w').write(self.__as_json(self.settings))

    async def login(self):

        args = list()
        token = self.settings.setdefault('login', {}).setdefault('token', 'OAuth2 Token')
        email = self.settings['login'].setdefault('email', 'address')
        password = self.settings['login'].setdefault('password', 'secretpass')
        if self.settings['login'].setdefault('method', 'token') == 'token':
            args.append(token)
        else:
            args.append(email)
            args.append(password)

        # create settings.json and then let it be changed before actually logging in.
        if not isfile('settings.json'):
            self.__check_if_settings_changed()
            return ()
        self.__check_if_settings_changed()

        log('Connecting...')
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
