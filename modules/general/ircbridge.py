import socket
import glados
import asyncio
import discord
import traceback
import sys
import copy


class IRCBridge(glados.Module):

    STATE_DISCONNECTED = 0
    STATE_TRY_JOIN = 1
    STATE_CONNECTED = 2

    def __init__(self, settings):
        super(IRCBridge, self).__init__(settings)
        self.settings = settings['irc']
        self.host = self.settings['host']
        self.port = self.settings['port']
        self.botnick = self.settings['nick']
        self.irc_channels = self.settings['irc channels']
        self.discord_channels = list()
        self.channels_to_join = list()
        self.socket = None
        self.irc_write_enable = False
        self.state = self.STATE_DISCONNECTED
        asyncio.async(self.run())

    def connect_to_server(self):
        self.channels_to_join = copy.deepcopy(self.irc_channels)
        glados.log('Connecting to: {}:{}'.format(self.host, self.port))
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.send_raw_message('USER {0} {0} {0} :Bridge between the IRC and Discord GDNet communities\n'.format(self.botnick))
            self.send_raw_message('NICK {}\n'.format(self.botnick))
            self.state = self.STATE_TRY_JOIN
        except Exception as e:
            glados.log('Exception caught: {}'.format(e))

    def join_remaining_channels(self):
        for channel in self.channels_to_join:
            glados.log('Joining channel {}'.format(channel))
            self.send_raw_message('JOIN {}\n'.format(channel))

    def send_raw_message(self, msg):
        if self.socket:
            glados.log('irc: {}'.format(msg.strip('\r\n')))
            self.socket.send(msg.encode())

    def send_to_all_channels(self, msg):
        for channel in self.irc_channels:
            self.send_raw_message('PRIVMSG {} :{}\n'.format(channel, msg))

    @asyncio.coroutine
    def run(self):
        while True:
            try:
                if self.state == self.STATE_DISCONNECTED:
                    self.connect_to_server()

                else:
                    loop = asyncio.get_event_loop()
                    msg = yield from loop.run_in_executor(None, self.socket.recv, 2048)
                    if not msg:
                        continue

                    msg = msg.decode().strip('\r\n')
                    glados.log('Received message: {}'.format(msg))

                    if msg[:4] == 'PING':
                        resp = 'PONG {}\n'.format(msg.split()[1])
                        self.send_raw_message(resp)

                    if self.state == self.STATE_TRY_JOIN:
                        glados.log('There are channels to be joined...')
                        self.channels_to_join = [x for x in self.channels_to_join if msg.find('JOIN {}'.format(x)) == -1]
                        self.join_remaining_channels()
                        if len(self.channels_to_join) == 0:
                            glados.log('All channels joined')
                            self.state = self.STATE_CONNECTED

                    if msg.find('PRIVMSG ') != -1:
                        if self.client:
                            self.discord_channels = self.get_discord_channels(self.settings['discord channels'])
                        for channel in self.discord_channels:
                            if msg.find('PRIVMSG #'.format(channel.name)) != -1:
                                resp = msg.split('{} :'.format(channel.name), 1)[1]
                                author = msg.split('!')[0].strip(':')
                                yield from self.client.send_message(channel, '[IRCBridge] <{}> {}'.format(author, resp))

            except Exception as e:
                glados.log('Exception caught: {}'.format(e))
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
            yield

    def get_discord_channels(self, channel_names):
        ret = list()
        for channel in self.client.get_all_channels():
            if '#{}'.format(channel.name) in channel_names:
                ret.append(channel)
        return ret

    def get_help_list(self):
        return list()

    @glados.Module.rules('^.*$')
    def on_discord_message(self, message, match):
        if isinstance(message.channel, discord.Object):
            return()
        if message.channel.is_private:
            return ()
        if not self.irc_write_enable:
            return ()
        author = message.author.name
        content = self.substitute_mentions(message)
        self.send_to_all_channels('<{}> {}'.format(author, content))
        return ()

    @glados.Module.commands('ircenable')
    def on_irc_enable(self, message, args):
        if message.author.id != '104330175243636736':
            return ()

        self.irc_write_enable = not self.irc_write_enable
        msg = 'IRC write enabled: All messages here will be relayed.' if self.irc_write_enable else 'IRC write disabled. You can only see messages from IRC but cannot respond.'
        yield from self.client.send_message(message.channel, msg)

    @staticmethod
    def substitute_mentions(message):
        content = message.content
        for mention in message.mentions:
            content = content.replace('<@{}>'.format(mention.id), mention.name)
            content = content.replace('<@!{}>'.format(mention.id), mention.name)
        return content