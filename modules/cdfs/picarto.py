import glados
import asyncio
import json
import websockets
import http.client
import urllib.parse
import time
from modules.cdfs.proto import chat_pb2
from google.protobuf.message import Message


# /channel/name/{channel name}
# -> retrieve user_id -> this might be the channel ID?
# TheComet: 193355
# Leyanor: 187669

API_URL = 'api.picarto.tv'
API_V = '/v1'
CHAT_ENDPOINT = 'wss://nd2.picarto.tv/socket?token={}'


class PicartoClient(object):
    def __init__(self, discord_client, discord_channel_id, websocket):
        self.discord_client = discord_client
        self.websocket = websocket
        self.discord_channel_id = discord_channel_id

    async def listen(self):
        await self.discord_client.wait_until_ready()

        discord_channel = None
        for channel in self.discord_client.get_all_channels():
            if channel.id == self.discord_channel_id:
                discord_channel = channel
                break
        if discord_channel is None:
            glados.log('Failed to get discord channel with ID {}'.format(self.discord_channel_id))
            await self.websocket.close()
            return

        while True:
            time_started = time.time()
            data = await self.websocket.recv()
            message_type_id = data[0]
            data = data[1:]
            try:
                print(message_type_id)
                success = True
                if message_type_id == 2:  # ID for user message
                    message = chat_pb2.ChatMessage()
                    message.ParseFromString(data)
                    content = message.message
                    author = message.display_name
                    if message.time_stamp < time_started:
                        success = False
                else:
                    success = False

                if success:
                    await self.discord_client.send_message(discord_channel, '<{}> {}'.format(author, content))
            except:
                pass


class Picarto(glados.Module):

    def __init__(self):
        super(Picarto, self).__init__()
        self.picarto_clients = list()

    def get_help_list(self):
        return tuple()

    def setup_global(self):
        for bridge in self.settings['picarto']['bridges']:
            client = self.__connect(bridge)
            if client is None:
                continue
            self.picarto_clients.append(client)
            asyncio.ensure_future(client.listen())

    def __connect(self, bridge):
        conn = http.client.HTTPSConnection(API_URL)

        # Look up user_id, which apparently is also the channel_id
        user_name = bridge['user name']
        conn.request('GET', API_V + '/channel/name/{}'.format(user_name))
        response = conn.getresponse()
        if response.status != 200:
            glados.log('Failed to retrieve channel_id from /channel/name/{}\n{} {}\n{}'.format(
                user_name, response.status, response.reason, response.read()))
            return None
        channel_id = json.loads(response.read().decode('utf-8'))['user_id']

        # With channel_id, generate JWT key
        params = {'channel_id': channel_id, 'bot': True}
        headers = {'Authorization': 'Bearer {}'.format(self.settings['picarto']['persistent token'])}
        conn.request('GET', API_V + '/user/jwtkey?{}'.format(urllib.parse.urlencode(params)), headers=headers)
        response = conn.getresponse()
        if response.status != 200:
            glados.log('Failed to generate JWT key\n{} {}\n{}'.format(
                response.status, response.reason, response.read()))
            return None
        jwt_key = response.read().decode('utf-8')

        conn.close()

        url = CHAT_ENDPOINT.format(jwt_key)
        websocket = asyncio.get_event_loop().run_until_complete(websockets.connect(url))
        client = PicartoClient(self.client, bridge['discord channel id'], websocket)
        return client

    @glados.Module.rule('^.*$')
    async def on_message(self, message, match):
        for picarto_client in self.picarto_clients:
            picarto_message = chat_pb2.NewMessage()
            picarto_message.message = message.clean_content
            data = picarto_message.SerializeToString()
            data = b'\x00' + data
            await picarto_client.websocket.send(data)
