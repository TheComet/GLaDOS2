import gzip
import json
from urllib.parse import urlencode
import urllib.request

import glados


STACK_EXCHANGE_API = 'https://api.stackexchange.com/2.2/search/advanced?'

class StackOverflow(glados.Module):
    def get_help_list(self):
        return [
            glados.Help('so', '<search terms>', 'Searches stuff in stackoverflow')
        ]

    @glados.Module.commands('so')
    def search(self, message, content):
        query_string = urlencode({
            'order': 'desc',
            'sort': 'relevance',
            'site': 'stackoverflow',
            'pagesize': 1,
            'q': content
        })
        result = get_json_response(STACK_EXCHANGE_API + query_string)
        if (not result['items']):
            yield from self.client.send_message(message.channel, 'No questions found :(')
        else:
            yield from self.client.send_message(message.channel, result['items'][0]['link'])


def get_json_response(url):
    with urllib.request.urlopen(url) as response:
        result = gzip.decompress(response.read())
        return json.loads(result.decode('utf-8'))
