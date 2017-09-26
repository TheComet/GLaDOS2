import glados
import asyncio


class Announcements(glados.Module):
    def __init__(self):
        super(Announcements, self).__init__()
        self.channel_ids = None
        self.join_msg = None

    def setup_global(self):
        self.channel_ids = self.settings.setdefault('announcements', {}).setdefault('channels', [])
        self.join_msg = self.settings['announcements'].setdefault('join message', 'Welcome!')

        @self.client.event
        async def on_member_join(member):
            for channel in self.client.get_all_channels():
                if channel.id in self.channel_ids and member.server == channel.server:
                    await self.client.send_message(channel, "{} joined the server! {}".format(member.mention, self.join_msg))
            return list()

        @self.client.event
        async def on_member_remove(member):
            for channel in self.client.get_all_channels():
                if channel.id in self.channel_ids and member.server == channel.server:
                    await self.client.send_message(channel, "{} left the server!".format(member.name))
            return list()

    def get_help_list(self):
        return list()
