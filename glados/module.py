import re
import os


class Module(object):

    def __init__(self):
        self.__command_prefix = None
        self.__data_path = None
        self.__server_specific_config_dir = None
        # this is set externally when the module is loaded. Contains a list of server names where this module should
        # be active. An empty list means it can be active on all servers.
        self.server_whitelist = list()
        # this is set externally when the module is loaded. It will be something like "test.foo.Hello".
        self.full_name = str()
        # set externally to the discord client object
        self.client = None
        self.settings = None

        self.__server_specific_name = None
        self.__memories = dict()

    def set_settings(self, settings):
        self.settings = settings
        self.__command_prefix = settings['commands']['prefix']
        self.__data_path = self.settings['modules'].setdefault('data', 'data')

    def set_current_server(self, server_id):
        self.__server_specific_name = self.full_name + server_id
        self.__server_specific_config_dir = os.path.join(self.__data_path, server_id)
        if not os.path.isdir(self.__server_specific_config_dir):
            os.mkdir(self.__server_specific_config_dir)
        self.__may_need_to_setup_memory()

    def setup_global(self):
        """
        Called right after the external module attributes were set. Gets called only once globally.
        """
        pass

    def setup_memory(self):
        """
        Gets called once during initialisation for every server. This is useful when modules want to create the server
        specific directories and set up memory storage.
        """
        pass

    def shutdown(self):
        """
        Gets called once when the bot is about to terminate execution. You can do various cleanup
        stuff here like saving files.
        """
        pass

    def get_config_dir(self):
        """
        Returns the path in which modules can store their data. Modules **must** use this function and not retrieve it
        from the "settings" dict. It changes depending on which server a message originated from.
        """
        return self.__server_specific_config_dir

    def get_memory(self):
        """
        Returns the server specific memory. Modules can store whatever they want in here.
        :return: A dictionary. Store whatever you want
        """
        return self.__memories[self.__server_specific_name]

    def __may_need_to_setup_memory(self):
        if not self.__server_specific_name in self.__memories:
            self.__memories[self.__server_specific_name] = dict()
            self.setup_memory()  # calls derived

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
