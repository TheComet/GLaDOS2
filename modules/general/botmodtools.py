import glados
from datetime import datetime, timedelta
import dateutil.parser


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
                if not member in mod_list:
                    mod_list.append(member)
            if member.id in self.__settings['admins']['IDs']:
                if not member in admin_list:
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
                expiry_date = self.__settings['banned'][member.id]
                if not expiry_date == 'never':
                    expiry_date = dateutil.parser.parse(expiry_date)
                    time_to_expiry = expiry_date - datetime.now()
                    time_to_expiry = '{0:.1f} hour(s)'.format(time_to_expiry.seconds / 3600.0)
                else:
                    time_to_expiry = 'forever'
                banned.append((member, time_to_expiry))

        if len(banned) > 0:
            text = '**Banned Users**\n{}'.format('\n'.join(['  + ' + x[0].name + ' for {}'.format(x[1]) for x in banned]))
        else:
            text = 'No one is banned.'
        yield from self.client.send_message(message.channel, text)

    @glados.Module.commands('blesslist')
    def blesslist(self, message, content):
        blessed = list()
        for member in self.client.get_all_members():
            if member.id in self.__settings['blessed']:
                if not member in blessed:
                    blessed.append(member)

        if len(blessed) > 0:
            text = '**Blessed Users**\n{}'.format('\n'.join(['  + ' + x.name for x in blessed]))
        else:
            text = 'No one is blessed.'
        yield from self.client.send_message(message.channel, text)
