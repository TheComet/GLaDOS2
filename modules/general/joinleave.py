import glados
import json
from os.path import join, isfile


class JoinLeave(glados.Module):

    def setup_memory(self):
        self.memory['db file'] = join(self.data_dir, 'joinleave.json')
        self.__load_db()

        @self.client.event
        async def on_member_join(member):
            for channel in self.client.get_all_channels():
                if member.server.id == channel.server.id and channel.id in self.memory['db']['join messages']:
                    msg = self.memory['db']['join messages'][channel.id].replace('{}', member.mention)
                    await self.client.send_message(channel, msg)
            return ()

        @self.client.event
        async def on_member_remove(member):
            for channel in self.client.get_all_channels():
                if member.server.id == channel.server.id and channel.id in self.memory['db']['leave messages']:
                    msg = self.memory['db']['leave messages'][channel.id].replace('{}', member.name)
                    await self.client.send_message(channel, msg)
            return ()

    @glados.Permissions.admin
    @glados.Module.command('addjoin', '<channel> <msg>', 'Add a message to print when a user joins. You can use '
                           'python-like "{}" syntax to insert the user\'s name, e.g. "Welcome to my server {}! Have a '
                           'nice stay!')
    async def addjoin(self, message, content):
        channel, msg = self.__parse_args(message, content)
        if channel is None:
            await self.provide_help('addjoin', message)
            return
        self.memory['db']['join messages'][channel.id] = msg
        self.__save_db()
        await self.client.send_message(message.channel, 'Added join message to channel {}: {}'.format(
            channel.name, msg.replace('{}', '<user>')))

    @glados.Permissions.admin
    @glados.Module.command('rmjoin', '<channel>', 'Remove a join message from a channel. You can specify a channel ID '
                           '#name.')
    async def rmjoin(self, message, content):
        channel, msg = self.__parse_args(message, content + ' _')
        if channel is None:
            await self.provide_help('rmjoin', message)
            return
        if self.memory['db']['join messages'].pop(channel.id, None) is None:
            await self.client.send_message(message.channel, 'Channel {} has no join message'.format(channel.name))
        else:
            self.__save_db()
            await self.client.send_message(message.channel, 'Removed join message from channel {}'.format(channel.name))

    @glados.Permissions.admin
    @glados.Module.command('addleave', '<channel> <msg>', 'Add a message to print when a user leaves the server. You '
                           'can use python-like "{}" syntax to insert the user\'s name, e.g. "Sad to see you go, {}!')
    async def addleave(self, message, content):
        channel, msg = self.__parse_args(message, content)
        if channel is None:
            await self.provide_help('addleave', message)
            return
        self.memory['db']['leave messages'][channel.id] = msg
        self.__save_db()
        await self.client.send_message(message.channel, 'Added leave message to channel {}: {}'.format(
            channel.name, msg.replace('{}', '<user>')))

    @glados.Permissions.admin
    @glados.Module.command('rmleave', '<channel>', 'Remove a leave message from a channel')
    async def rmleave(self, message, content):
        channel, msg = self.__parse_args(message, content + ' _')
        if channel is None:
            await self.provide_help('rmleave', message)
            return
        if self.memory['db']['leave messages'].pop(channel.id, None) is None:
            await self.client.send_message(message.channel, 'Channel {} has no leave message'.format(channel.name))
        else:
            self.__save_db()
            await self.client.send_message(message.channel, 'Removed leave message from channel {}'.format(channel.name))

    def __parse_args(self, message, content):
        channel_name, msg = content.split(' ', 1)
        channel_name = channel_name.strip('#')
        for channel in self.client.get_all_channels():
            if channel.server.id == message.server.id and channel_name == channel.name:
                return channel, msg
        return None, msg

    def __load_db(self):
        if isfile(self.memory['db file']):
            self.memory['db'] = json.loads(open(self.memory['db file']).read())
        else:
            self.memory['db'] = dict()

        self.memory['db'].setdefault('join messages', {})
        self.memory['db'].setdefault('leave messages', {})

    def __save_db(self):
        with open(self.memory['db file'], 'w') as f:
            f.write(json.dumps(self.memory['db'], indent=2, sort_keys=True))
