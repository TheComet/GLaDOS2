import glados


class Announcements(glados.Module):
    def __init__(self):
        super(Announcements, self).__init__()
        self.join_msgs = None
        self.leave_msgs = None

    def setup_global(self):
        self.join_msgs = self.settings.setdefault('announcements', {}).setdefault('join messages', {
            'channel id': '{} joined the server!'
        })
        self.leave_msgs = self.settings['announcements'].setdefault('leave message', {
            'channel id': '{} left the server!'
        })

        @self.client.event
        async def on_member_join(member):
            for channel in self.client.get_all_channels():
                if member.server.id == channel.server.id and channel.id in self.join_msgs:
                    msg = self.join_msgs[channel.id].format(member.mention)
                    await self.client.send_message(channel, msg)
            return ()

        @self.client.event
        async def on_member_remove(member):
            for channel in self.client.get_all_channels():
                if member.server.id == channel.server.id and channel.id in self.leave_msgs:
                    msg = self.leave_msgs[channel.id].format(member.name)
                    await self.client.send_message(channel, msg)
            return ()
