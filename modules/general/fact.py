import glados
import urllib.request
from bs4 import BeautifulSoup


class Fact(glados.Module):

    def get_help_list(self):
        return [
            glados.Help('fact', '', 'Look up a random fact')
        ]

    @glados.Module.commands('fact')
    def fact(self, message, args):
        response = urllib.request.urlopen('http://randomfactgenerator.net/').read().decode('utf-8')
        soup = BeautifulSoup(response, 'lxml')
        fact_div = soup.find('div', {'id': 'z'})
        if len(fact_div.contents) == 0:
            yield from self.client.send_message(message.channel, 'Something broke.')
        else:
            yield from self.client.send_message(message.channel, fact_div.contents[0])

