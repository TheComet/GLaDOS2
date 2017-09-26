import glados


class Help(glados.Module):

    def __init__(self):
        super(Help, self).__init__()
        self.__command_prefix = None

    def setup_global(self):
        self.__command_prefix = self.settings['commands']['prefix']

    def get_help_list(self):
        return [glados.Help('help', '[search]', 'Get a list of all commands, or of a specific command')]

    @glados.Module.commands('help')
    async def help(self, message, content):
        # creates a list of relevant modules
        relevant_modules = self.bot.get_loaded_modules(message.server)

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

        await self.client.send_message(message.channel,
                'I\'m sending you a gigantic wall of direct message with a list of commands!')

        for msg in self.__concat_into_valid_message(relevant_help):
            await self.client.send_message(message.author, msg)

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
                l = 0
                temp = list()
            temp.append(s)
        ret.append('\n'.join(temp))
        return ret
