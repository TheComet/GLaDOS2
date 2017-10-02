import glados


class Help(glados.Module):

    def setup_memory(self):
        print('setup_memory')

    @glados.Module.command('test', '', 'The test')
    @glados.Module.command('test2', '', 'The test')
    async def test(self, message, content):
        await self.client.send_message(message.content, 'test')

    @glados.Module.command('help', '[search]', 'Get a list of all commands, or of a specific command')
    async def help(self, message, content):
        help_strings = (string for module in self.active_modules for string in module.get_casual_help_strings())

        # Filter relevant modules if the user is requesting a specific command
        if len(content) > 0:
            help_strings = filter(
                lambda hlp: any(True for search in content.split() if search in hlp), help_strings)

        await self.client.send_message(message.channel,
                'I\'m sending you a gigantic wall of direct message with a list of commands!')

        for msg in self.pack_into_messages(sorted(help_strings)):
            await self.client.send_message(message.author, msg)

    @glados.Module.command('modhelp', '[search]', 'Get a list of moderator bot commands')
    async def modhelp(self, message, content):
        await self.__privileged_help(message, content, 'moderator')

    @glados.Module.command('adminhelp', '[search]', 'Get a list of administrator bot commands')
    async def adminhelp(self, message, content):
        await self.__privileged_help(message, content, 'admin')

    @glados.Module.command('ownerhelp', '[search]', 'Get a list of owner bot commands')
    async def ownerhelp(self, message, content):
        await self.__privileged_help(message, content, 'owner')

    async def __privileged_help(self, message, content, level):
        help_strings = (string for module in self.active_modules
                        for string in module.get_privileged_help_strings(level))

        # Filter relevant modules if the user is requesting a specific command
        if len(content) > 0:
            help_strings = filter(
                lambda hlp: any(True for search in content.split() if search in hlp), help_strings)

        await self.client.send_message(message.channel,
                                       'I\'m sending you a list of {} commands.'.format(level))

        for msg in self.pack_into_messages(sorted(help_strings)):
            await self.client.send_message(message.author, msg)
