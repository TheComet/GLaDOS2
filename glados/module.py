import re
import os


class Module(object):

    def __init__(self):
        self.__was_initialised = False

        # this is set externally when the module is loaded. Contains a list of server names where this module should
        # be active. An empty list means it can be active on all servers.
        self.server_whitelist = list()
        # set when the module is loaded. It will be something like "test.foo.Hello".
        self.__full_name = str()
        # the settings dictionary (settings.json)
        self.__settings = None
        self.__command_prefix = None
        self.__data_path = None
        self.__global_data_dir = None
        # reference to the bot object, required for getting the client object or a list of all loaded modules
        self.__bot = None
        # reference to permission module (or dummy, if not loaded)
        self.__permissions = None

        # Server isolation stuff
        self.__server_specific_data_dir = None
        self.__memories = dict()
        self.__current_memory = None
        self.__current_server = None

    def init_module(self, bot, full_name, settings, permissions):
        self.__bot = bot
        self.__full_name = full_name
        self.__settings = settings
        self.__permissions = permissions
        self.__command_prefix = settings['commands']['prefix']
        self.__data_path = settings['modules'].setdefault('data', 'data')
        self.__global_data_dir = os.path.join(self.__data_path, 'global_cache')

        if not os.path.isdir(self.__global_data_dir):
            os.mkdir(self.__global_data_dir)

    def set_current_server(self, server_id):
        self.__current_server = next((server for server in self.client.servers if server.id == server_id))
        if self.__current_server is None:
            raise RuntimeError('Failed to set current server to ID: {}'.format(server_id))

        self.__server_specific_data_dir = os.path.join(self.__data_path, server_id)
        if not os.path.isdir(self.__server_specific_data_dir):
            os.mkdir(self.__server_specific_data_dir)

        # lazy global init for modules
        if not self.__was_initialised:
            self.setup_global()  # calls derived
            self.__was_initialised = True

        # lazy memory init for modules
        self.__current_memory = self.__memories.get(self.__current_server.id, None)
        if self.__current_memory is None:
            self.__memories[self.__current_server.id] = dict()
            self.setup_memory()  # calls derived

    @property
    def settings(self):
        """
        :return: Reference to global settings.json file. You can write things back into it. Changes will be saved when
        the bot shuts down.
        """
        return self.__settings

    @property
    def full_name(self):
        """
        :return: The full name of this module. Typically it's something like path.filename.classname
        """
        return self.__full_name

    @property
    def command_prefix(self):
        """
        :return: Returns the configured command prefix character(s) for commands.
        """
        return self.__command_prefix

    @property
    def current_server(self):
        """
        :return: A reference to the currently active discord server object (from which the message originated).
        """
        return self.__current_server

    @property
    def client(self):
        """
        :return: A reference to the discord client object.
        """
        return self.__bot.client

    @property
    def loaded_modules(self):
        """
        :return: Generates a list of all of the loaded modules that are active on the current server.
        """
        return self.__bot.get_loaded_modules(self.__current_server.id)

    @property
    def global_data_dir(self):
        """
        :return: Returns the path to a directory where modules can store data that is common among all servers.
        If you want to store data only for specific servers, then use data_dir() instead.
        """
        return self.__global_data_dir

    @property
    def data_dir(self):
        """
        Returns the path in which modules can store their data. Modules **must** use this function and not retrieve it
        from the "settings" dict. It changes depending on which server a message originated from.
        """
        return self.__server_specific_data_dir

    @property
    def memory(self):
        """
        Returns the server specific memory. Modules can store whatever they want in here.
        :return: A dictionary. Store whatever you want
        """
        return self.__current_memory

    def setup_global(self):
        """
        Use this instead of __init__ if possible. This gets called once only, and it gets called on demand (that is, the
        first time your module is required).
        """
        pass

    def setup_memory(self):
        """
        Gets called once for every server on demand. This is useful when modules want to create the server specific
        directories and set up memory storage.
        """
        pass

    def shutdown(self):
        """
        Gets called once when the bot is about to terminate execution. You can do various cleanup
        stuff here like saving files.
        """
        pass

    def is_banned(self, member):
        """
        Checks if the specified member is banned or not.
        :param member: A discord member object.
        :return: True if banned, False if otherwise
        """
        return self.__permissions.is_banned(member)

    def is_blessed(self, member):
        """
        Checks if the specified member is blessed or not.
        :param member: A discord member object.
        :return: True if blessed, False if otherwise
        """
        return self.__permissions.is_blessed(member)

    def require_moderator(self, member):
        """
        Checks if the specified member has moderator privileges or higher.
        :param member: A discord member object.
        :return: True if so, False if otherwise.
        """
        return self.__permissions.require_moderator(member)

    def require_admin(self, member):
        """
        Checks if the specified member has administrator privileges or higher.
        :param member: A discord member object.
        :return: True if so, False if otherwise.
        """
        return self.__permissions.require_admin(member)

    def require_owner(self, member):
        """
        Checks if the specified member has owner privileges.
        :param member: A discord member object.
        :return: True if so, False if otherwise.
        """
        return self.__permissions.require_owner(member)

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
        for hlp in self.get_help_list():
            if hlp.command == command:
                await self.client.send_message(message.channel, self.__command_prefix + hlp.get())

    def get_help_list(self):
        """
        The inheriting modules should return a list of glados.Help objects describing what each command in the class
        does.

        For example:

            def get_help_list(self):
                return [
                    glados.Help('hello', '<name>', 'Says hello to the user with the specified name')
                ]

        :return: A list of glados.Help objects. If no help exists (because your module has no commands), you can also
        return an empty list.
        """
        raise RuntimeError('Module doesn\'t provide any command descriptions.')

    def parse_members_roles(self, message, content):
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
        if len(members) > 0 or len(roles) > 0:
            return members, roles, ''

        # fall back to text based names, in which case we need to look up the member object
        name = content.split()[0].strip('@').split('#')[0]
        for member in self.current_server.members:
            if member.nick == name or member.name == name:
                members.add(member)
            # There is currently no way to get a list of all roles, but we can compose one by taking the
            # roles from all of the members
            for role in member.roles:
                if role.name == name:
                    roles.add(role)

        if len(members) == 0 and len(roles) == 0:
            return (), (), 0, 'Error: No member or role found with the name "{}"'.format(name)
        if len(members) > 0 and len(roles) > 0:
            return (), (), 0, 'Error: One or more member(s) have a name identical to a role name "{}".' \
                              'Try again by mentioning the user/role'.format(name)
        if len(members) > 1 or len(roles) > 1:
            return (), (), 0, 'Error: Multiple members/roles share the name "{}".' \
                              'Try again by mentioning the user.'.format(name)

        return members, roles, ''

    @staticmethod
    def commands(*command_list):
        """
        This should be used as a decorator for your module member functions that handle commands. You can specify
        a list of commands you wish to react to.

        Example:

            class Hello(glados.Module):
                @glados.Mdoule.commands('hello', 'hi')
                def respond_to_hello(self, client, message, content):
                    await client.send_message(message.channel, 'Hi! {}'.format(message.author.name))

        In this case, sending either ".hello" or ".hi" will cause your function respond_to_hello() to be called.

        :param command_list: A list of strings of commands to react to when they are issued in Discord.
        """
        def add_attribute(func):
            func.__dict__.setdefault('commands', list())
            func.commands.extend(command_list)
            return func
        return add_attribute

    @staticmethod
    def rules(*rule_list):
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

        :param rule_list: A list of strings of regular expression to match messages sent on Discord with.
        """
        def add_attribute(func):
            func.__dict__.setdefault('rules', list())
            for rule in rule_list:
                func.rules.append(re.compile(rule, re.IGNORECASE))
            return func
        return add_attribute

    @staticmethod
    def bot_rules(*rule_list):
        """
        Same as rules(), except only messages that originate from bots (that aren't our own) are passed.
        :param rule_list: A list of strings of regular expression to match messages sent on Discord with.
        """
        def add_attribute(func):
            func.__dict__.setdefault('bot_rules', list())
            for rule in rule_list:
                func.bot_rules.append(re.compile(rule, re.IGNORECASE))
            return func
        return add_attribute
