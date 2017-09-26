import discord
import traceback
import json
import asyncio
import inspect
import re
import math
from .Log import log
from .cooldown import Cooldown
from .tools.path import add_import_paths
from .Permissions import Permissions

comment_pattern = re.compile('`(.*?)`')


class Bot(object):
    def __init__(self):
        self.settings = json.loads(open('settings.json').read())
        self.client = discord.Client()

        self.__command_prefix = self.settings.setdefault('commands', {}).setdefault('prefix', '.')
        self.__callback_tuples = list()  # list of tuples. (callback, module)
        self.__cooldown = Cooldown()
        self.load_modules()

        # The bot needs access to the permissions module for managing things like admins/botmods
        self.__permissions = Permissions()
        self.__permissions.set_settings(self.settings)
        for cb, m in self.__callback_tuples:
            if m.full_name == 'bot.permissions.Permissions':
                self.__permissions = m
                break

        @self.client.event
        async def on_message(message):

            # disallow direct messages
            if not message.server:
                return ()

            commands = self.extract_commands_from_message(message.clean_content)
            commands_to_process = self.__get_commands_that_could_be_executed(message, commands)
            commands_to_process += self.__get_matches_that_could_be_executed(message)

            # required for permission server isolation
            self.__permissions.set_current_server(message.server.id)

            punish_checked = False
            user_is_punished = False
            for callback, module, content in commands_to_process:
                code = self.__permissions.check_permissions(message.author, callback)
                if code < 0:
                    cooldown = self.__apply_cooldown(message)
                    if cooldown:
                        await self.client.send_message(message.author, cooldown)
                    else:
                        await self.__permissions.inform_about_failure(message, code)
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

                module.set_current_server(message.server.id)  # required for server isolation
                await callback(message, content)

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
                for command, content in commands:
                    if command in callback.commands:
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
            'bot.ping.Ping',
            'bot.uptime.UpTime',
            'bot.permissions.Permissions'
        ]):
            result = self.__import_module(modfullname)
            if not result is None:
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

        # get the module's help list for the global .help command
        try:
            modhelp = [self.__command_prefix + x.get() for x in m.get_help_list()]
        except RuntimeError:
            return 'Error: Module {0} doesn\'t provide any help.'.format(modfullname)

        # set server whitelist
        if not server is None:
            m.server_whitelist.append(server)

        # set module properties
        m.full_name = modfullname
        m.client = self.client
        m.set_settings(self.settings)
        m.setup_global()

        # get a list of tuples containing (callback function, module) pairs.
        callback_tuples = self.__get_callback_tuples(m)
        if len(callback_tuples) > 0:
            self.__callback_tuples += callback_tuples

    async def __process_core_commands(self, message, command, content):
        # Ignore bots
        if message.author.bot:
            return

        if command == self.settings['commands'].setdefault('help', 'help'):
            await self.__process_help_command(message, content)
        elif command == self.settings['commands'].setdefault('modhelp', 'modhelp'):
            await self.__process_modhelp_command(message, content)
        elif command == self.settings['commands'].setdefault('optout', 'optout'):
            await self.__process_optout_command(message, content)
        elif command == self.settings['commands'].setdefault('optin', 'optin'):
            await self.__process_optin_command(message, content)

        # TODO remove
        return ()

        is_mod = message.author.id in self.settings['moderators']['IDs'] or \
                 len(set(x.name for x in message.author.roles).intersection(set(self.settings['moderators']['roles']))) > 0
        is_admin = message.author.id in self.settings['admins']['IDs']

        mod_commands = {
            self.settings['commands']['ban']: self.__process_ban_command,
            self.settings['commands']['unban']: self.__process_unban_command,
            self.settings['commands']['bless']: self.__process_bless_command,
            self.settings['commands']['unbless']: self.__process_unbless_command,
        }

        admin_commands = {
            self.settings['commands']['mod']: self.__process_mod_command,
            self.settings['commands']['unmod']: self.__process_unmod_command,
            self.settings['commands']['reload']: self.__process_reload_command,
            self.settings['commands']['say']: self.__process_say_command
        }

        # commands that require moderator privileges
        if command in mod_commands:
            if not is_mod and not is_admin:
                await self.client.send_message(message.author, 'You must be a moderator to use this command')
                return
        if command == self.settings['commands']['ban']:
            await self.__process_ban_command(message, content)
        elif command == self.settings['commands']['unban']:
            await self.__process_unban_command(message, content)
        elif command == self.settings['commands']['bless']:
            await self.__process_bless_command(message, content)
        elif command == self.settings['commands']['unbless']:
            await self.__process_unbless_command(message, content)

        # Remaining commands require admin privileges
        if command in admin_commands:
            if not is_admin:
                await self.client.send_message(message.author, 'You must be an administrator to use this command')
                return
        if command == self.settings['commands']['mod']:
            await self.__process_mod_command(message, content)
        elif command == self.settings['commands']['unmod']:
            await self.__process_unmod_command(message, content)
        elif command == self.settings['commands']['reload']:
            await self.__process_reload_command(message, content)
        elif command == self.settings['commands']['say']:
            await admin_commands[command](message, content)
        else:
            return None

    async def __process_help_command(self, message, content):
        # creates a list of relevant modules
        relevant_modules = set(module for c, module in self.__callback_tuples
                               if len(module.server_whitelist) == 0
                               or message.server and message.server.name in module.server_whitelist)
        # Filter relevant modules if the user is requesting a specific command
        if len(content) > 0:
            relevant_modules = set(module for module in relevant_modules
                                   if any(True for x in content.split()
                                          if any(True for hlp in module.get_help_list()
                                                 if x.lower() in hlp.command)))
        # generates a list of help strings from the modules
        relevant_help = sorted([self.__command_prefix + hlp.get()
                                for mod in relevant_modules
                                for hlp in mod.get_help_list()])

        # If the user was banned, don't announce the help sending, but send the help anyway
        do_announce = False
        for msg in self.__concat_into_valid_message(relevant_help):
            do_announce = True
            await self.client.send_message(message.author, msg)
        if do_announce:
            if not message.author.id in self.settings['banned']:
                await self.client.send_message(message.channel,
                                                    'I\'m sending you a gigantic wall of direct message with a list of commands!')

    async def __process_optout_command(self, message, content):
        if message.author.id in self.settings['optout']:
            await self.client.send_message(message.channel, 'User "{}" is already opted out.'.format(message.author.name))
            return

        self.settings['optout'].append(message.author.id)
        self.__save_settings()

        await self.client.send_message(message.channel,
                        'User "{}" has opted out. The bot will no longer log any of your activity. '
                        'This also means you won\'t be able to use any of the statistic commands, such '
                        'as `.quote` or `.zipf`. If you want your existing data to be deleted, ask the '
                        'bot owner.'.format(message.author.name))

    async def __process_optin_command(self, message, content):
        if not message.author.id in self.settings['optout']:
            await self.client.send_message(message.channel, 'User "{}" is already opted in.'.format(message.author.name))
            return

        self.settings['optout'].remove(message.author.id)
        self.__save_settings()

        await self.client.send_message(message.channel, 'User "{}" has opted in. The bot will collect logs on you '
                        'for commands such as `.quote` or `.zipf` to function correctly.'.format(message.author.name))

    async def __process_bless_command(self, message, content):
        if content == '':
            await self.client.send_message(message.channel, 'Invalid syntax. Type `.modhelp` if you need help.')
            return

        args = content.split(' ', 1)
        author = args[0]

        # If result is a string, then it is an error message.
        results = self.__get_members_from_string(message, author)
        if isinstance(results, str):
            await self.client.send_message(message.channel, results)
            return

        for member in results:
            if member.id in self.settings['blessed']:
                await self.client.send_message(message.channel, 'User "{}" is already blessed'.format(member))
            else:
                self.settings['blessed'].append(member.id)
                await self.client.send_message(message.channel, 'User "{}" has been blessed.'.format(member))
        self.__save_settings()

    async def __process_unbless_command(self, message, content):
        if content == '':
            await self.client.send_message(message.channel, 'Invalid syntax. Type `.modhelp` if you need help.')
            return

        # If result is a string, then it is an error message.
        author = content.split()[0]
        results = self.__get_members_from_string(message, author)
        if isinstance(results, str):
            await self.client.send_message(message.channel, results)
            return

        for member in results:
            if not member.id in self.settings['blessed']:
                await self.client.send_message(message.channel, 'User "{}" isn\'t blessed'.format(member))
            else:
                self.settings['blessed'].remove(member.id)
                await self.client.send_message(message.channel, 'User "{}" has been unblessed'.format(member))
        self.__save_settings()

    async def __process_mod_command(self, message, content):
        if content == '':
            await self.client.send_message(message.channel, 'Invalid syntax. Type `.modhelp` if you need help.')
            return

        args = content.split(' ', 1)
        author = args[0]

        # If result is a string, then it is an error message.
        results = self.__get_members_from_string(message, author)
        if isinstance(results, str):
            await self.client.send_message(message.channel, results)
            return

        for member in results:
            if member.id in self.settings['moderators']['IDs']:
                await self.client.send_message(message.channel, 'User "{}" is already a moderator'.format(member))
            else:
                self.settings['moderators']['IDs'].append(member.id)
                await self.client.send_message(message.channel, 'User "{}" is now a bot moderator. Type `.modhelp` to learn about your new powers!'.format(member))
        self.__save_settings()

    async def __process_unmod_command(self, message, content):
        if content == '':
            await self.client.send_message(message.channel, 'Invalid syntax. Type `.modhelp` if you need help.')
            return

        # If result is a string, then it is an error message.
        author = content.split()[0]
        results = self.__get_members_from_string(message, author)
        if isinstance(results, str):
            await self.client.send_message(message.channel, results)
            return

        for member in results:
            if not member.id in self.settings['moderators']['IDs']:
                await self.client.send_message(message.channel, 'User "{}" isn\'t a moderator!'.format(member))
            else:
                self.settings['moderators']['IDs'].remove(member.id)
                await self.client.send_message(message.channel, 'User "{}" is no longer a moderator'.format(member))
        self.__save_settings()

    async def __process_reload_command(self, message, content):
        self.settings = json.loads(open('settings.json').read())
        await self.client.send_message(message.channel, 'Reloaded settings')

    async def __process_say_command(self, message, content):
        parts = content.split(' ', 2)
        if len(parts) < 3:
            await self.client.send_message(message.channel, 'Error: Specify server name or ID, then channel name or ID. Example: ``.say <server> <channel> <message>``')
            return

        # find relevant channel
        for channel in self.client.get_all_channels():
            if channel.server.id == parts[0] or channel.server.name == parts[0]:
                if channel.id == parts[1] or channel.name.strip('#') == parts[1].strip('#'):
                    await self.client.send_message(channel, parts[2])
                    return
        return tuple()

    def __save_settings(self):
        open('settings.json', 'w').write(json.dumps(self.settings, indent=2, sort_keys=True))

    def __get_members_from_string(self, message, user_name):
        # Use mentions instead of looking up the name if possible
        if len(message.mentions) > 0:
            return message.mentions

        user_name = user_name.strip('@').split('#')[0]
        members = list()
        for member in self.client.get_all_members():
            if member.nick == user_name or member.name == user_name:
                members.append(member)
        if len(members) == 0:
            return 'Error: No member found with the name "{}"'.format(user_name)
        if len(members) > 1:
            return 'Error: Multiple members share the name "{}". Try again by mentioning the user.'.format(user_name)
        return members

    @staticmethod
    def __concat_into_valid_message(list_of_strings):
        """
        Takes a list of strings and cats them such that the maximum discord limit is not exceeded. Strings are joined
        with a newline.
        :param list_of_strings:
        :return: Returns a list of strings. Each string will be small enough to be sent in a discord message.
        """
        ret = list()
        temp = list()
        l = 0
        max_length = 1000

        if len(list_of_strings) == 0:
            return ret

        for s in list_of_strings:
            l += len(s)
            if l >= max_length:
                ret.append('\n'.join(temp))
                l = len(s)
                temp = list()
            temp.append(s)
        ret.append('\n'.join(temp))
        return ret

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

        await self.client.login(*args)
        await self.client.connect()

    def run(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.login())
        except:
            loop.run_until_complete(self.client.logout())
            raise
        finally:
            loop.close()
            print(json.dumps(self.settings, indent=2, sort_keys=True))
            #self.__save_settings()
            for cb, m in self.__callback_tuples:
                m.shutdown()
