import json
import glados
import urllib.request
import urllib.parse
import random

UD_URL = 'http://api.urbandictionary.com/v0/define?term='


class Urban(glados.Module):
    @staticmethod
    def get_def(word):
        url = UD_URL + urllib.parse.quote(word)
        resp = json.loads(urllib.request.urlopen(url).read().decode("utf-8"))
        if len(resp['list']) == 0:
            definition = 'Definition {} not found!'.format(word)
        else:
            try:
                item = resp['list'][0]
                thumbsup = item['thumbs_up']
                thumbsdown = item['thumbs_down']
                points = str(int(thumbsup) - int(thumbsdown))
                definition = str(item['definition']).replace('[', '').replace(']', '').replace('\n', ' ').replace('\r', '')
                example = str(item['example']).replace('[', '').replace(']', '').replace('\n', ' ').replace('\r', '')
                points = '{} ({}{}|{}{})'.format(points, thumbsup, u'\U0001F44D', thumbsdown, u'\U0001F44E')
                definition = '**Definition:** {}\n**Example:** {}\n**Points:** {}'.format(
                    definition, example, points
                )
            except:
                definition = 'Something went wrong. API broke again?'
        return definition

    @glados.Module.command('urban', '<term>', 'Look up a term on urban dictionary.')
    @glados.Module.command('ud', '', '')
    async def urban(self, message, content):
        if message.author.id == '156788287820791808' and random.random() < 0.333:   # newt
            return await self.client.send_message(message.channel, "Shut the hell up, newt")
        definition = self.get_def(content)
        await self.client.send_message(message.channel, definition)
