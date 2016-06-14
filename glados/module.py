class Module(object):

    def __init__(self, settings):
        pass

    def on_message(self, client, message):
        pass

    @staticmethod
    def commands(*command_list):
        def add_attribute(func):
            if not hasattr(func, "commands"):
                func.commands = list()
            func.commands.extend(command_list)
            return func
        return add_attribute
