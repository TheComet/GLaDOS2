# coding=utf-8
"""
wiktionary.py - Sopel Wiktionary Module
Copyright 2009, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.
http://sopel.chat
"""
import glados
import re
import urllib.request
import urllib.parse

uri = 'http://en.wiktionary.org/w/index.php?title={}&printable=yes'
r_tag = re.compile(r'<[^>]+>')
r_ul = re.compile(r'(?ims)<ul>.*?</ul>')


def text(html):
    text = r_tag.sub('', html).strip()
    text = text.replace('\n', ' ')
    text = text.replace('\r', '')
    text = text.replace('(intransitive', '(intr.')
    text = text.replace('(transitive', '(trans.')
    return text


def wikt(word):
    bytes = urllib.request.urlopen(uri.format(urllib.parse.quote(word))).read().decode('utf-8')
    bytes = r_ul.sub('', bytes)

    mode = None
    etymology = None
    definitions = {}
    for line in bytes.splitlines():
        if 'id="Etymology"' in line:
            mode = 'etymology'
        elif 'id="Noun"' in line:
            mode = 'noun'
        elif 'id="Verb"' in line:
            mode = 'verb'
        elif 'id="Adjective"' in line:
            mode = 'adjective'
        elif 'id="Adverb"' in line:
            mode = 'adverb'
        elif 'id="Interjection"' in line:
            mode = 'interjection'
        elif 'id="Particle"' in line:
            mode = 'particle'
        elif 'id="Preposition"' in line:
            mode = 'preposition'
        elif 'id="' in line:
            mode = None

        elif (mode == 'etmyology') and ('<p>' in line):
            etymology = text(line)
        elif (mode is not None) and ('<li>' in line):
            definitions.setdefault(mode, []).append(text(line))

        if '<hr' in line:
            break
    return etymology, definitions

parts = ('preposition', 'particle', 'noun', 'verb',
    'adjective', 'adverb', 'interjection')


def format(result, definitions, number=2):
    for part in parts:
        if part in definitions:
            defs = definitions[part][:number]
            result += u' — {}: '.format(part)
            n = ['%s. %s' % (i + 1, e.strip(' .')) for i, e in enumerate(defs)]
            result += ', '.join(n)
    return result.strip(' .,')


class Wiktionary(glados.Module):

    def get_help_list(self):
        return [
            glados.Help('define', '<word>', 'Look up a word on wiktionary')
        ]

    @glados.Module.commands('wt', 'define', 'dict')
    async def wiktionary(self, message, word):
        """Look up a word on Wiktionary."""
        if word == '':
            await self.provide_help('define', message)
            return

        _etymology, definitions = wikt(word)
        if not definitions:
            await self.client.send_message(message.channel, 'Couldn\'t get any definitions for {}.'.format(word))
            return

        result = format(word, definitions)
        if len(result) < 150:
            result = format(word, definitions, 3)
        if len(result) < 150:
            result = format(word, definitions, 5)

        if len(result) > 300:
            result = result[:295] + '[...]'
        await self.client.send_message(message.channel, result)
