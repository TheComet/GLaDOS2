import glados
import asyncio
import json
import http.client
import urllib.parse
from autobahn.asyncio.websocket import WebSocketClientFactory, WebSocketClientProtocol

# /channel/name/{channel name}
# -> retrieve user_id -> this might be the channel ID?
# TheComet: 193355
# Leyanor: 187669

API_URL = 'api.picarto.tv'
API_V = '/v1'
CHAT_ENDPOINT = 'https://nd2.picarto.tv/socket?token={}'


class PicartoClient(WebSocketClientProtocol):

    def __init__(self):
        super(PicartoClient, self).__init__()
        self.discord_channel = None

    def onConnect(self, request):
        print('oh?')

    def onOpen(self):
        print('hell yeah')

    def onMessage(self, payload, is_binary):
        print('lol')

    def onClose(self, was_clean, code, reason):
        print('shit')


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
        jwt_key = response.read()

        conn.close()

        url = CHAT_ENDPOINT.format(jwt_key)
        factory = WebSocketClientFactory(url)
        factory.protocol = PicartoClient
        loop = asyncio.get_event_loop()
        coro = loop.create_connection(factory, url)
        asyncio.ensure_future(coro)

        return True
