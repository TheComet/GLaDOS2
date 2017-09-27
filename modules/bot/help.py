import glados


class Help(glados.Module):

    def __init__(self):
        super(Help, self).__init__()
        self.__command_prefix = None

    @glados.Module.command('help', '[search]', 'Get a list of all commands, or of a specific command')
    async def help(self, message, content):
        help_strings = (string for module in self.loaded_modules for string in module.get_casual_help_strings())

        # Filter relevant modules if the user is requesting a specific command
        if len(content) > 0:
            help_strings = filter(
                lambda hlp: any(True for search in content.split() if search in hlp), help_strings)

        await self.client.send_message(message.channel,
                'I\'m sending you a gigantic wall of direct message with a list of commands!')

        for msg in self.__concat_into_valid_message(sorted(help_strings)):
            await self.client.send_message(message.author, msg)

    @glados.Module.command('modhelp', '[search]', 'Get a list of privileged bot commands (for moderators/admins)')
    async def modhelp(self, message, content):
        help_strings = (string for module in self.loaded_modules for string in module.get_privileged_help_strings())

        # Filter relevant modules if the user is requesting a specific command
        if len(content) > 0:
            help_strings = filter(
                lambda hlp: any(True for search in content.split() if search in hlp), help_strings)

        await self.client.send_message(message.channel,
                                       'I\'m sending you a list of moderator commands.')

        for msg in self.__concat_into_valid_message(sorted(help_strings)):
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
                l = len(s)
                temp = list()
            temp.append(s)
        ret.append('\n'.join(temp))
        return ret
