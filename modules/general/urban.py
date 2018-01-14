import json
import glados
import urllib.request
import urllib.parse

UD_URL = 'http://api.urbandictionary.com/v0/define?term='


class Urban(glados.Module):
    @staticmethod
    def get_def(word):
        url = UD_URL + urllib.parse.quote(word)
        resp = json.loads(urllib.request.urlopen(url).read().decode("utf-8"))
        if resp['result_type'] == 'no_results':
            definition = 'Definition {} not found!'.format(word)
        else:
            try:
                item = resp['list'][0]['definition']
                thumbsup = resp['list'][0]['thumbs_up']
                thumbsdown = resp['list'][0]['thumbs_down']
                points = str(int(thumbsup) - int(thumbsdown))
                definition = 'Definition: ' + str(item) + ' >> Points: ' + points + ' (03' + str(thumbsup) + '|05' + str(thumbsdown) + ')'
            except IndexError:
                definition = ('Definition entry %s does'
                              'not exist for \'%s\'.' % (1, word))
        return definition

    @glados.Module.command('urban', '<term>', 'Look up a term on urban dictionary.')
    @glados.Module.command('ud', '', '')
    async def urban(self, message, content):
        #if message.author.id == '156788287820791808':   # newt
        #    return await self.client.send_message(message.channel, "Fuck off newt")
        definition = self.get_def(content)
        await self.client.send_message(message.channel, definition)
