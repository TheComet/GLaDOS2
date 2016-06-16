import re


class Module(object):

    def __init__(self, settings):
        self.__command_prefix = settings['commands']['prefix']

    def provide_help(self, command, client, message):
        help = next(x for x in self.get_help_list() if x.command == command)
        yield from client.send_message(message.channel, self.__command_prefix + help.get())

    def get_help_list(self):
        """
        The inheriting modules should return a list of strings describing what each command does.
        :return:
        """
        raise RuntimeError('Module doesn\'t provide any command descriptions.')

    @staticmethod
    def commands(*command_list):
        def add_attribute(func):
            if not hasattr(func, "commands"):
                func.commands = list()
            func.commands.extend(command_list)
            return func
        return add_attribute

    @staticmethod
    def rules(*rule_list):
        def add_attribute(func):
            if not hasattr(func, "rules"):
                func.rules = list()
            for rule in rule_list:
                func.rules.append(re.compile(rule))
            return func
        return add_attribute
