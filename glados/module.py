import re


class Module(object):

    def __init__(self, settings):
        pass

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
