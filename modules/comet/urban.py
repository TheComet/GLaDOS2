import json
import glados
import urllib.request

UD_URL = 'http://api.urbandictionary.com/v0/define?term='


class Urban(glados.Module):

    @staticmethod
    def get_def(word):
        url = UD_URL + word
        resp = json.loads(urllib.request.urlopen(url).read())
        if resp['result_type'] == 'no_results':
            definition = 'Definition %s not found!' % (word)
        else:
            try:
                item = resp['list'][0]['definition'].encode('utf8')
                thumbsup = resp['list'][0]['thumbs_up']
                thumbsdown = resp['list'][0]['thumbs_down']
                points = str(int(thumbsup) - int(thumbsdown))
                total_nom = len(resp['list'])
                definition = 'Definition: ' + str(item) + " >> Number: " + str(nom) + '/' + str(total_nom) + ' >> Points: ' + points + ' (03' + str(thumbsup) + '|05' + str(thumbsdown) + ')'
            except IndexError:
                definition = ('Definition entry %s does'
                              'not exist for \'%s\'.' % (1, word))
        return definition


    @commands('urban', 'ud')
    def urban(self, bot, trigger):
        if not trigger.group(2):
                bot.reply('.urban [defnum] <term>')
                return
        args = trigger.group(2).replace(', ', ',').split(',')
        defnum = 0
        word = ' '.join(args)
        if len(args) > 1:
            try:
                defnum = int(args[0])
                defnum = defnum - 1
                word = ' '.join(args[1:])
            except ValueError:
                pass
        definition = get_def(word, defnum).replace('\r', ' / ')
        bot.say(definition, max_messages=5)
