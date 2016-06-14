import json

from willie import web
from willie.module import commands

UD_URL = 'http://api.urbandictionary.com/v0/define?term='


def get_def(word, num=0):
    url = UD_URL + word
    try:
        resp = json.loads(web.get(url))
    except UnicodeError:
        definition = ('ENGLISH MOTHERFUCKER, DO YOU SPEAK IT?')
        return definition
    nom = num + 1
    if resp['result_type'] == 'no_results':
        definition = 'Definition %s not found!' % (word)
    else:
        try:
            item = resp['list'][num]['definition'].encode('utf8')
            thumbsup = resp['list'][num]['thumbs_up']
            thumbsdown = resp['list'][num]['thumbs_down']
            points = str(int(thumbsup) - int(thumbsdown))
            total_nom = len(resp['list'])
            definition = 'Definition: ' + str(item) + " >> Number: " + str(nom) + '/' + str(total_nom) + ' >> Points: ' + points + ' (03' + str(thumbsup) + '|05' + str(thumbsdown) + ')'
        except IndexError:
            definition = ('Definition entry %s does'
                          'not exist for \'%s\'.' % (nom, word))
    return definition


@commands('urban', 'ud')
def urban(bot, trigger):
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
