import re


class Module(object):

    def __init__(self, settings):
        self.__command_prefix = settings['commands']['prefix']
        # this is set externally when the module is loaded. Contains a list of server names where this module should
        # be active. An empty list means it can be active on all servers.
        self.server_whitelist = list()
        # this is set externally when the module is loaded. It will be something like "test.foo.Hello".
        self.full_name = str()
        # set externally to the discord client object
        self.client = None
        self.settings = settings

    def setup(self):
        """
        Called right after the external module attributes were set.
        """
        pass

    def provide_help(self, command, message):
        """
        If the user has entered an invalid command, you can call this function to send help to the user.
        Example:
            if user_didnt_use_hello_command_correctly:
                yield from self.provide_help('hello', client, message)
        :param command: A string specifying the command the user tried to use. This string needs to exist in one of the
        glados.Help objects returned by get_help_list().
        :param client: The discord.client
        :param message: The discord.message object
        :return: Returns a generator, must be yielded (asyncio coroutine).
        """
        hlp = next(x for x in self.get_help_list() if x.command == command)
        yield from self.client.send_message(message.channel, self.__command_prefix + hlp.get())

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
                    yield from client.send_message(message.channel, 'Hi! {}'.format(message.author.name))

        In this case, sending either ".hello" or ".hi" will cause your function respond_to_hello() to be called.

        :param command_list: A list of strings of commands to react to when they are issued in Discord.
        """
        def add_attribute(func):
            if not hasattr(func, "commands"):
                func.commands = list()
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
                    yield from client.send_message(message.channel, 'So you like books, {}?'.format(message.author.name))

        In this case, if any message contains the phrase "I like books", then the function respond_to_books() will be
        called.

        :param rule_list: A list of strings of regular expression to match messages sent on Discord with.
        """
        def add_attribute(func):
            if not hasattr(func, "rules"):
                func.rules = list()
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
            if not hasattr(func, "bot_rules"):
                func.bot_rules = list()
            for rule in rule_list:
                func.bot_rules.append(re.compile(rule, re.IGNORECASE))
            return func
        return add_attribute
