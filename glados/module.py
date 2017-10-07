import re
import inspect
import sys


class Module(object):

    def __init__(self, server_instance, full_name):
        # reference to the bot object, required for getting the client object or a list of all loaded modules
        self.__server_instance = server_instance
        # set when the module is loaded. It will be something like "test.foo.Hello".
        self.__full_name = full_name

    @property
    def settings(self):
        """
        :return: Reference to global settings.json file. You can write things back into it. Changes will be saved after
        your command returns.
        """
        return self.__server_instance.settings

    @property
    def server(self):
        return self.__server_instance.server

    @property
    def full_name(self):
        """
        :return: The full name of this module. Typically it's something like path.filename.classname
        """
        return self.__full_name

    @property
    def command_prefix(self):
        return self.__server_instance.command_prefix

    @property
    def client(self):
        """
        :return: A reference to the discord client object.
        """
        return self.__server_instance.client

    @property
    def active_modules(self):
        """
        :return: A set of all of the loaded modules that are active on the current server and are not
        blacklisted.
        """
        return self.__server_instance.active_modules

    @property
    def available_modules(self):
        """
        :return: A set of all of the available modules that could be activated on the current server.
        """
        return self.__server_instance.available_modules

    @property
    def blacklisted_modules(self):
        """
        :return: A set of the modules that were blacklisted for the current server.
        """
        return self.__server_instance.blacklisted_modules

    @property
    def global_data_dir(self):
        """
        :return: Returns the path to a directory where modules can store data that is common among all servers.
        If you want to store data only for specific servers, then use data_dir() instead.
        """
        return self.__server_instance.global_data_dir

    @property
    def local_data_dir(self):
        """
        Returns the path in which modules can store their data. Modules **must** use this function and not retrieve it
        from the "settings" dict. It changes depending on which server a message originated from.
        """
        return self.__server_instance.local_data_dir

    def is_banned(self, member):
        """
        Checks if the specified member is banned or not.
        :param member: A discord member object.
        :return: True if banned, False if otherwise
        """
        return self.__server_instance.permissions.is_banned(member)

    def is_blessed(self, member):
        """
        Checks if the specified member is blessed or not.
        :param member: A discord member object.
        :return: True if blessed, False if otherwise
        """
        return self.__server_instance.permissions.is_blessed(member)

    def require_moderator(self, member):
        """
        Checks if the specified member has moderator privileges or higher.
        :param member: A discord member object.
        :return: True if so, False if otherwise.
        """
        return self.__server_instance.permissions.require_moderator(member)

    def require_admin(self, member):
        """
        Checks if the specified member has administrator privileges or higher.
        :param member: A discord member object.
        :return: True if so, False if otherwise.
        """
        return self.__server_instance.permissions.require_admin(member)

    def require_owner(self, member):
        """
        Checks if the specified member has owner privileges.
        :param member: A discord member object.
        :return: True if so, False if otherwise.
        """
        return self.__server_instance.permissions.require_owner(member)

    async def provide_help(self, command, message):
        """
        If the user has entered an invalid command, you can call this function to send help to the user.
        Example:
            if user_didnt_use_hello_command_correctly:
                await self.provide_help('hello', client, message)
        :param command: A string specifying the command the user tried to use. This string needs to exist in one of the
        glados.Help objects returned by get_help_list().
        :param client: The discord.client
        :param message: The discord.message object
        :return: Returns a generator, must be yielded (asyncio coroutine).
        """
        command_list = list()
        for name, member in inspect.getmembers(self, predicate=inspect.ismethod):
            if not hasattr(member, 'commands') or not any(x[0] == command for x in member.commands):
                continue
            command_list += list(self.__help_string_from_member_func(member))
        await self.client.send_message(message.channel, '\n'.join(command_list))

    def get_casual_help_strings(self):
        for name, member in inspect.getmembers(self, predicate=inspect.ismethod):
            if not hasattr(member, 'commands') or any(hasattr(member, x) for x in ('moderator', 'admin', 'owner')):
                continue
            yield from self.__help_string_from_member_func(member)

    def get_privileged_help_strings(self, level):
        for name, member in inspect.getmembers(self, predicate=inspect.ismethod):
            if not hasattr(member, 'commands') or not hasattr(member, level):
                continue
            yield from self.__help_string_from_member_func(member)

    def __help_string_from_member_func(self, member_func):
        for command, argument_list_str, description in member_func.commands[::-1]:  # decorators are applied in reverse
            if not description:
                continue
            if argument_list_str:
                yield '{}{} **{}** -- *{}*'.format(self.command_prefix, command, argument_list_str, description)
            else:
                yield '{}{} -- *{}*'.format(self.command_prefix, command, description)

    def parse_members_roles(self, message, content, membercount=sys.maxsize, rolecount=sys.maxsize):
        """
        Can be used to extract a list of member names/mentions or role names from a sent message. Typically one would
        use it as follows:

            members, roles, error = self.get_members_roles(message, content)
            if error:
                await self.client.send_message(message.channel, error)
                return
            # At this point, you now have a list of mentioned members and roles

        :param message: The discord message object that was sent from the server
        :param content: The content of the message, minus command
        :param membercount: The maximum number of members you want returned.
        :param rolecount: The maximum number of roles you want returned.
        :return: If successful, this returns a tuple with a list of members, list of roles, and an empty string
        (indicating no error). If unsuccessful, the third item in the returned tuple will be a string containing the
        error message.
        """
        members = set()
        roles = set()

        # Use mentions instead of looking up the name if possible
        for member in message.mentions:
            members.add(member)
        for role in message.role_mentions:
            roles.add(role)

        # fall back to text based names, in which case we need to look up the member object
        if len(roles) == 0 and len(members) == 0:
            name = content.split()[0].strip('@').split('#')[0]
            for member in self.server.members:
                if member.nick == name or member.name == name:
                    members.add(member)
            for role in self.server.roles:
                if role.name == name:
                    roles.add(role)

            # These errors can only occur if the members/roles were not mentioned
            if len(members) > 0 and len(roles) > 0:
                return (), (), 'Error: One or more member(s) have a name identical to a role name "{}".' \
                               'Try again by mentioning the user/role'.format(name)
            if len(members) > 1 or len(roles) > 1:
                return (), (), 'Error: Multiple members/roles share the name "{}".' \
                               'Try again by mentioning the user.'.format(name)

        if len(members) == 0 and len(roles) == 0:
            return (), (), 'Error: No member or role found!'
        if len(members) >= membercount:
            return (), (), 'Error: More than {} member{} were specified!'.format(
                membercount, '' if membercount == 1 else 's')
        if len(roles) >= rolecount:
            return (), (), 'Error: More than {} role{} were specified!'.format(
                rolecount, '' if rolecount == 1 else 's')

        return members, roles, ''

    @staticmethod
    def pack_into_messages(list_of_strings, delimiter='\n'):
        """
        Takes a list of strings and joines them (with newlines by default) into a new list of strings such that none of
         the new strings exceed discord's message limit.
        :param list_of_strings: A list of strings you want to join.
        :param delimiter: The string to use for joining (default is newline).
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
                ret.append(delimiter.join(temp))
                l = len(s)
                temp = list()
            temp.append(s)
        ret.append(delimiter.join(temp))
        return ret

    @staticmethod
    def command(command, argument_list_str, description):
        """
        This should be used as a decorator for your module member functions that handle commands. You can specify
        a command, a string showing the arguments that need to be passed, and a description string (the last two
        arguments are used to generate help text).

        Example:

            class Hello(glados.Module):
                @glados.Mdoule.commands('hello', '[member]', 'Makes the bot say hello to someone')
                def respond_to_hello(self, client, message, content):
                    await client.send_message(message.channel, 'Hi! {}'.format(message.author.name))

        In this case, sending either ".hello" will cause your function respond_to_hello() to be called.

        :param command: A string for the command that triggers a callback to your method.
        :param argument_list_str: A string that shows the possible arguments that should be passed to your method (this
        is used to generate help)
        :param description: A string containing a description of what the command does (used for help).
        """
        def factory(func):
            func.__dict__.setdefault('commands', list())
            func.commands.append((command, argument_list_str, description))
            return func
        return factory

    @staticmethod
    def rule(rule, ignorecommands=True):
        """
        This should be used as a decorator for your module member functions that handle responding to specific patterns
        in messages. You can specify a list of regular expressions as arguments. If a message posted on Discord matches
        any of the regexes, then your method will be called.

        Example:

            class Hello(glados.Module):
                @glados.Mdoule.rules('^.*(I like books).*$')
                def respond_to_books(self, client, message, match):
                    await client.send_message(message.channel, 'So you like books, {}?'.format(message.author.name))

        In this case, if any message contains the phrase "I like books", then the function respond_to_books() will be
        called.

        :param rule: A regular expression to match messages sent on Discord with.
        """
        def factory(func):
            func.__dict__.setdefault('rules', list())
            func.rules.append((re.compile(rule, re.IGNORECASE), ignorecommands))
            return func
        return factory

    @staticmethod
    def bot_rule(rule, ignorecommands=True):
        """
        Same as rules(), except only messages that originate from bots (that aren't our own) are passed.
        :param rule: A regular expression to match messages sent on Discord with.
        """
        def factory(func):
            func.__dict__.setdefault('bot_rules', list())
            func.bot_rules.append((re.compile(rule, re.IGNORECASE), ignorecommands))
            return func
        return factory
