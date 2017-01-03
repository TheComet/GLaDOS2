import glados


class BotModTools(glados.Module):
    def __init__(self, settings):
        super(BotModTools, self).__init__(settings)
        self.__settings = settings

    def get_help_list(self):
        return [
            glados.Help('modlist', '', 'Displays which users are bot moderators'),
            glados.Help('banlist', '', 'Displays which users are banned'),
            glados.Help('blesslist', '', 'Displays which users are blessed')
        ]

    @glados.Module.commands('modlist')
    def modlist(self, message, content):
        mod_list = list()
        admin_list = list()
        for member in self.client.get_all_members():
            if member.id in self.__settings['moderators']['IDs']:
                mod_list.append(member)
            if member.id in self.__settings['admins']['IDs']:
                admin_list.append(member)

        text = '**Moderators:**\n{}\n**Administrators:**\n{}'.format(
            '\n'.join(['  + ' + x.name for x in mod_list]),
            '\n'.join(['  + ' + x.name for x in admin_list])
        )

        yield from self.client.send_message(message.channel, text)

    @glados.Module.commands('banlist')
    def banlist(self, message, content):
        banned = list()
        for member in self.client.get_all_members():
            if member.id in self.__settings['banned']:
                banned.append(member)

        if len(banned) > 0:
            text = '**Banned Users**\n{}'.format('\n'.join(['  + ' + x.name for x in banned]))
        else:
            text = 'No one is banned.'
        yield from self.client.send_message(message.channel, text)

    @glados.Module.commands('blesslist')
    def blesslist(self, message, content):
        blessed = list()
        for member in self.client.get_all_members():
            if member.id in self.__settings['blessed']:
                blessed.append(member)

        if len(blessed) > 0:
            text = '**Blessed Users**\n{}'.format('\n'.join(['  + ' + x.name for x in blessed]))
        else:
            text = 'No one is blessed.'
        yield from self.client.send_message(message.channel, text)
