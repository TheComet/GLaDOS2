import glados
import asyncio
from glados.Log import log


class Announcements(glados.Module):
    def __init__(self, settings):
        super(Announcements, self).__init__(settings)

    def setup(self):
        channel_ids = self.settings['announcements']['channels']

        @self.client.event
        @asyncio.coroutine
        def on_member_join(member):
            for channel in self.client.get_all_channels():
                if channel.id in channel_ids:
                    yield from self.client.send_message(channel, "{} joined the server!".format(member.mention))
            return list()

        @self.client.event
        @asyncio.coroutine
        def on_member_remove(member):
            for channel in self.client.get_all_channels():
                if channel.id in channel_ids:
                    yield from self.client.send_message(channel, "{} left the server!".format(member.mention))
            return list()

    def get_help_list(self):
        return list()
