import discord
import traceback
import json
import asyncio
import inspect
import re
from datetime import datetime, timedelta
from .Log import log
from .cooldown import Cooldown
from .tools.path import add_import_paths

comment_pattern = re.compile('`(.*?)`')


class Bot(object):
    def __init__(self):
        self.settings = json.loads(open('settings.json').read())
        self.client = discord.Client()

        self.__command_prefix = self.settings['commands']['prefix']
        self.__callback_tuples = list()  # list of tuples. (module, command_callback)
        self.__cooldown = Cooldown()
        self.load_modules()

        @self.client.event
        @asyncio.coroutine
        def on_message(message):

            # disallow direct messages
            if not message.server:
                return ()

            commands = self.extract_commands_from_message(message.clean_content)
            commands_to_process = self.__get_commands_that_will_be_executed(message, commands)
            matches_to_process = self.__get_matches_that_will_be_executed(message)

            # Ignore banned users
            if message.author.id in self.settings['banned']:
                # See if any of the modules are blessed. If not, punish
                if not all('.'.join((x[1].full_name, x[0].__name__)) in self.settings['modules']['blessed'] for x in commands_to_process) or \
                   not all('.'.join((x[1].full_name, x[0].__name__)) in self.settings['modules']['blessed'] for x in matches_to_process):
                    if not self.__try_unban_user(message.author):
                        expiry = self.settings['banned'][message.author.id]
                        yield from self.client.send_message(message.author,
                                'You have been banned from using the bot. Your ban expires: {}'.format(expiry))
                        return
            else:
                for command, content in commands:
                    yield from self.__process_core_commands(message, command, content)

            if len(commands_to_process) == 0 and len(matches_to_process) == 0:
                return ()

            if not message.author.id in self.settings['blessed'] \
                    and not message.author.id in self.settings['moderators']['IDs'] \
                    and not message.author.id in self.settings['admins']['IDs']:
                # See if any of the modules are blessed. If not, punish
                if not all('.'.join((x[1].full_name, x[0].__name__)) in self.settings['modules']['blessed'] for x in commands_to_process) or \
                   not all('.'.join((x[1].full_name, x[0].__name__)) in self.settings['modules']['blessed'] for x in matches_to_process):
                    cooldown = self.__apply_cooldown(message)
                    if cooldown:
                        yield from self.client.send_message(message.author, cooldown)
                        return

            for callback, module, content in commands_to_process:
                yield from callback(message, content)

            for callback, module, match in matches_to_process:
                yield from callback(message, match)

        @self.client.event
        @asyncio.coroutine
        def on_ready():
            log('Running as {}'.format(self.client.user.name))

    def __get_commands_that_will_be_executed(self, message, commands):
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

    def __get_matches_that_will_be_executed(self, message):
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
        if not self.__cooldown.punish(author):
            return ('You are on cooldown.\nYour cooldown will expire in {} seconds.\n'
                    'You have reached punishment level {}.\n'
                    'Your punishment level decreases by 1 every 180 seconds.'). \
                format(self.__cooldown.expires_in(author), self.__cooldown.punishment(author))
        return False

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

        # set module properties
        m.full_name = modfullname
        m.client = self.client

        # get a list of tuples containing (callback function, module) pairs.
        callback_tuples = self.__get_callback_tuples(m)
        if len(callback_tuples) == 0:
            return 'Error: Module {0} has no callbacks'.format(modfullname)

        self.__callback_tuples += callback_tuples

    def __process_core_commands(self, message, command, content):
        # Ignore bots
        if message.author.bot:
            return

        if command == self.settings['commands']['help']:
            yield from self.__process_help_command(message, content)
        elif command == self.settings['commands']['modhelp']:
            yield from self.__process_modhelp_command(message, content)
        elif command == self.settings['commands']['optout']:
            yield from self.__process_optout_command(message, content)
        elif command == self.settings['commands']['optin']:
            yield from self.__process_optin_command(message, content)

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
            self.settings['commands']['reload']: self.__process_reload_command
        }

        # commands that require moderator privileges
        if command in mod_commands:
            if not is_mod and not is_admin:
                yield from self.client.send_message(message.author, 'You must be a moderator to use this command')
                return
        if command == self.settings['commands']['ban']:
            yield from self.__process_ban_command(message, content)
        elif command == self.settings['commands']['unban']:
            yield from self.__process_unban_command(message, content)
        elif command == self.settings['commands']['bless']:
            yield from self.__process_bless_command(message, content)
        elif command == self.settings['commands']['unbless']:
            yield from self.__process_unbless_command(message, content)

        # Remaining commands require admin privileges
        if command in admin_commands:
            if not is_admin:
                yield from self.client.send_message(message.author, 'You must be an administrator to use this command')
                return
        if command == self.settings['commands']['mod']:
            yield from self.__process_mod_command(message, content)
        elif command == self.settings['commands']['unmod']:
            yield from self.__process_unmod_command(message, content)
        elif command == self.settings['commands']['reload']:
            yield from self.__process_reload_command(message, content)
        else:
            return None

    def __process_help_command(self, message, content):
        # creates a list of relevant modules
        relevant_modules = set(module for c, module in self.__callback_tuples
                               if len(module.server_whitelist) == 0
                               or message.server and message.server.name in module.server_whitelist)
        # generates a list of help strings from the modules
        relevant_help = sorted([self.__command_prefix + hlp.get()
                                for mod in relevant_modules
                                for hlp in mod.get_help_list()
                                if content == hlp.command or content == ''])

        # If sending all help, PM it to the user
        if content == '':
            relevant_help = ['==== Loaded modules ===='] + relevant_help

            # If the user was banned, don't announce the help sending
            if not message.author.id in self.settings['banned']:
                yield from self.client.send_message(message.channel,
                                                    'I\'m sending you a direct message with a list of commands!')
            for msg in self.__concat_into_valid_message(relevant_help):
                yield from self.client.send_message(message.author, msg)
        # If sending help for a single command, send it to the channel
        else:
            if len(relevant_help) > 0:
                yield from self.client.send_message(message.channel, relevant_help[0])
            else:
                yield from self.client.send_message(message.channel, 'Unknown command {}'.format(content))

    def __process_modhelp_command(self, message, content):
        # If the user was banned, don't announce the help sending
        if not message.author.id in self.settings['banned']:
            yield from self.client.send_message(message.channel, "I just PM'd you the help list!")
        yield from self.client.send_message(message.author,
                "{0}{1} **<user> [hours]** -- Blacklist the specified user from using the bot for the "
                "specified number of hours. The default number of hours is 24. Specifying a value"
                " of 0 will cause the user to be perma-banned. The ban is based on user ID.\n"
                "{0}{2} **<user>** -- Allow a banned user to use the bot again.\n"
                "{0}{3} **<user>** -- Allow the specified user to evade the punishment system. "
                "This allows the user to excessively use the bot without consequences.\n"
                "{0}{4} **<user>** -- Prevents spam from this user by putting him through the punishment system.\n".format(
                    self.__command_prefix,
                    self.settings['commands']['ban'],
                    self.settings['commands']['unban'],
                    self.settings['commands']['bless'],
                    self.settings['commands']['unbless'])
        )

    def __process_optout_command(self, message, content):
        if message.author.id in self.settings['optout']:
            yield from self.client.send_message(message.channel, 'User "{}" is already opted out.'.format(message.author.name))
            return

        self.settings['optout'].append(message.author.id)
        self.__save_settings()

        yield from self.client.send_message(message.channel,
                        'User "{}" has opted out. The bot will no longer log any of your activity. '
                        'This also means you won\'t be able to use any of the statistic commands, such '
                        'as `.quote` or `.zipf`. If you want your existing data to be deleted, ask the '
                        'bot owner.'.format(message.author.name))

    def __process_optin_command(self, message, content):
        if not message.author.id in self.settings['optout']:
            yield from self.client.send_message(message.channel, 'User "{}" is already opted in.'.format(message.author.name))
            return

        self.settings['optout'].remove(message.author.id)
        self.__save_settings()

        yield from self.client.send_message(message.channel, 'User "{}" has opted in. The bot will collect logs on you '
                        'for commands such as `.quote` or `.zipf` to function correctly.'.format(message.author.name))

    def __process_ban_command(self, message, content):
        if content == '':
            yield from self.client.send_message(message.channel, 'Invalid syntax. Type `.modhelp` if you need help.')
            return

        args = content.split()
        author = args[0]

        # If result is a string, then it is an error message.
        results = self.__get_members_from_string(message, author)
        if isinstance(results, str):
            yield from self.client.send_message(message.channel, results)
            return

        # If you are a moderator, then you can't ban admins
        is_mod = message.author.id in self.settings['moderators']['IDs'] or \
                 len(set(x.name for x in message.author.roles).intersection(set(self.settings['moderators']['roles']))) > 0
        if is_mod:
            for member in results:
                is_admin = member.id in self.settings['admins']['IDs']
                if is_admin:
                    yield from self.client.send_message(message.channel, 'Moderators can\'t ban admins')
                    return

        # Default ban length is 24 hours
        if len(args) < 2:
            hours = 24
        else:
            try:
                hours = float(args[-1])
            except ValueError:
                hours = 24

        if hours > 0:
            expiry_date = datetime.now() + timedelta(hours / 24.0)
            for member in results:
                self.settings['banned'][member.id] = expiry_date.isoformat()
        else:
            for member in results:
                self.settings['banned'][member.id] = 'never'
            expiry_date = 'forever'
        self.__save_settings()

        users_banned = ', '.join([x.name for x in results])
        yield from self.client.send_message(message.channel, 'User(s) "{}" is banned from using this bot until {}'.format(users_banned, expiry_date))

    def __process_unban_command(self, message, content):
        if content == '':
            yield from self.client.send_message(message.channel, 'Invalid syntax. Type `.modhelp` if you need help.')
            return

        # If result is a string, then it is an error message.
        author = content.split()[0]
        results = self.__get_members_from_string(message, author)
        if isinstance(results, str):
            yield from self.client.send_message(message.channel, results)
            return

        for member in results:
            if not member.id in self.settings['banned']:
                yield from self.client.send_message(message.channel, 'User "{}" isn\'t banned'.format(member))
            else:
                self.__unban_user(member)
                yield from self.client.send_message(message.channel, 'Unbanned user "{}"'.format(member))

    def __try_unban_user(self, member):
        if not member.id in self.settings['banned']:
            return True

        expiry_date = self.settings['banned'][member.id]
        if expiry_date == 'never':
            return False
        if datetime.now().isoformat() > expiry_date:
            self.__unban_user(member)
            return True

        return False

    def __unban_user(self, member):
        del self.settings['banned'][member.id]
        self.__save_settings()

    def __process_bless_command(self, message, content):
        if content == '':
            yield from self.client.send_message(message.channel, 'Invalid syntax. Type `.modhelp` if you need help.')
            return

        args = content.split(' ', 1)
        author = args[0]

        # If result is a string, then it is an error message.
        results = self.__get_members_from_string(message, author)
        if isinstance(results, str):
            yield from self.client.send_message(message.channel, results)
            return

        for member in results:
            if member.id in self.settings['blessed']:
                yield from self.client.send_message(message.channel, 'User "{}" is already blessed'.format(member))
            else:
                self.settings['blessed'].append(member.id)
                yield from self.client.send_message(message.channel, 'User "{}" has been blessed.'.format(member))
        self.__save_settings()

    def __process_unbless_command(self, message, content):
        if content == '':
            yield from self.client.send_message(message.channel, 'Invalid syntax. Type `.modhelp` if you need help.')
            return

        # If result is a string, then it is an error message.
        author = content.split()[0]
        results = self.__get_members_from_string(message, author)
        if isinstance(results, str):
            yield from self.client.send_message(message.channel, results)
            return

        for member in results:
            if not member.id in self.settings['blessed']:
                yield from self.client.send_message(message.channel, 'User "{}" isn\'t blessed'.format(member))
            else:
                self.settings['blessed'].remove(member.id)
                yield from self.client.send_message(message.channel, 'User "{}" has been unblessed'.format(member))
        self.__save_settings()

    def __process_mod_command(self, message, content):
        if content == '':
            yield from self.client.send_message(message.channel, 'Invalid syntax. Type `.modhelp` if you need help.')
            return

        args = content.split(' ', 1)
        author = args[0]

        # If result is a string, then it is an error message.
        results = self.__get_members_from_string(message, author)
        if isinstance(results, str):
            yield from self.client.send_message(message.channel, results)
            return

        for member in results:
            if member.id in self.settings['moderators']['IDs']:
                yield from self.client.send_message(message.channel, 'User "{}" is already a moderator'.format(member))
            else:
                self.settings['moderators']['IDs'].append(member.id)
                yield from self.client.send_message(message.channel, 'User "{}" is now a bot moderator. Type `.modhelp` to learn about your new powers!'.format(member))
        self.__save_settings()

    def __process_unmod_command(self, message, content):
        if content == '':
            yield from self.client.send_message(message.channel, 'Invalid syntax. Type `.modhelp` if you need help.')
            return

        # If result is a string, then it is an error message.
        author = content.split()[0]
        results = self.__get_members_from_string(message, author)
        if isinstance(results, str):
            yield from self.client.send_message(message.channel, results)
            return

        for member in results:
            if not member.id in self.settings['moderators']['IDs']:
                yield from self.client.send_message(message.channel, 'User "{}" isn\'t a moderator!'.format(member))
            else:
                self.settings['moderators']['IDs'].remove(member.id)
                yield from self.client.send_message(message.channel, 'User "{}" is no longer a moderator'.format(member))
        self.__save_settings()

    def __process_reload_command(self, message, content):
        self.settings = json.loads(open('settings.json').read())
        yield from self.client.send_message(message.channel, 'Reloaded settings')

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
        for s in list_of_strings:
            l += len(s)
            if l >= max_length:
                ret.append('\n'.join(temp))
                l = 0
                temp = list()
            temp.append(s)
        ret.append('\n'.join(temp))
        return ret

    @staticmethod
    def __get_callback_tuples(m):
        return [(member, m) for name, member in inspect.getmembers(m, predicate=inspect.ismethod)
                if hasattr(member, 'commands') or hasattr(member, 'rules') or hasattr(member, 'bot_rules')]

    @asyncio.coroutine
    def login(self):
        log('Connecting...')
        if self.settings['login']['method'] == 'token':
            yield from self.client.login(self.settings['login']['token'])
        else:
            yield from self.client.login(self.settings['login']['email'], self.settings['login']['password'])
        yield from self.client.connect()

    def run(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.login())
        except:
            loop.run_until_complete(self.client.logout())
            raise
        finally:
            loop.close()
