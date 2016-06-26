# coding=utf-8
"""
etymology.py - Sopel Etymology Module
Copyright 2007-9, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.
http://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import re
import glados
import urllib.request


class Etymology(glados.Module):

    etyuri = 'http://etymonline.com/?term=%s'
    etysearch = 'http://etymonline.com/?search=%s'

    r_definition = re.compile(r'(?ims)<dd[^>]*>.*?</dd>')
    r_tag = re.compile(r'<(?!!)[^>]+>')
    r_whitespace = re.compile(r'[\t\r\n ]+')

    abbrs = [
        'cf', 'lit', 'etc', 'Ger', 'Du', 'Skt', 'Rus', 'Eng', 'Amer.Eng', 'Sp',
        'Fr', 'N', 'E', 'S', 'W', 'L', 'Gen', 'J.C', 'dial', 'Gk',
        '19c', '18c', '17c', '16c', 'St', 'Capt', 'obs', 'Jan', 'Feb', 'Mar',
        'Apr', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'c', 'tr', 'e', 'g'
    ]
    t_sentence = r'^.*?(?<!%s)(?:\.(?= [A-Z0-9]|\Z)|\Z)'
    r_sentence = re.compile(t_sentence % ')(?<!'.join(abbrs))

    def __init__(self, settings):
            super().__init__(settings)

    def get_help_list(self):
        return [
            glados.Help('ety', '<word>', 'Looks up the etymology of a word.')
        ]

    def unescape(self, s):
        s = s.replace('&gt;', '>')
        s = s.replace('&lt;', '<')
        s = s.replace('&amp;', '&')
        return s

    def text(self, html):
        html = self.r_tag.sub('', html)
        html = self.r_whitespace.sub(' ', html)
        return self.unescape(html).strip()

    def etymology(self, word):
        # @@ <nsh> sbp, would it be possible to have a flag for .ety to get 2nd/etc
        # entries? - http://swhack.com/logs/2006-07-19#T15-05-29

        if len(word) > 25:
            raise ValueError("Word too long: %s[...]" % word[:10])
        word = {'axe': 'ax/axe'}.get(word, word)

        bytes = urllib.request.urlopen(self.etyuri % word).read().decode('utf-8')
        definitions = self.r_definition.findall(bytes)

        if not definitions:
            return None

        defn = self.text(definitions[0])
        m = self.r_sentence.match(defn)
        if not m:
            return None
        sentence = m.group(0)

        maxlength = 275
        if len(sentence) > maxlength:
            sentence = sentence[:maxlength]
            words = sentence[:-5].split(' ')
            words.pop()
            sentence = ' '.join(words) + ' [...]'

        sentence = '"' + sentence.replace('"', "'") + '"'
        return sentence + ' - ' + (self.etyuri % word)

    @glados.Module.commands('ety')
    def f_etymology(self, message, word):
        """Look up the etymology of a word"""

        if word == '':
            yield from self.provide_help('ety', message)
            return

        try:
            result = self.etymology(word)
        except IOError:
            msg = "Can't connect to etymonline.com (%s)" % (self.etyuri % word)
            yield from self.client.send_message(message.channel, msg)
            return
        except (AttributeError, TypeError):
            result = None

        if result is not None:
            yield from self.client.send_message(message.channel, result)
        else:
            uri = self.etysearch % word
            msg = 'Can\'t find the etymology for "%s". Try %s' % (word, uri)
            yield from self.client.send_message(message.channel, msg)
            return
