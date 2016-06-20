# coding=utf-8
"""
spellcheck.py - Sopel spell check Module
Copyright © 2012, Elad Alfassa, <elad@fedoraproject.org>
Copyright © 2012, Lior Ramati
Licensed under the Eiffel Forum License 2.
http://sopel.chat
This module relies on pyenchant, on Fedora and Red Hat based system, it can be found in the package python-enchant
"""
import enchant
import glados


class SpellCheck(glados.Module):

    def get_help_list(self):
        return [
            glados.Help('spell', '<word>', 'Says whether the given word is spelled correctly, '
                                           'and gives suggestions if it\'s not')
        ]

    @glados.Module.commands('spellcheck', 'spell')
    def spellcheck(self, client, message, word):
        """
        Says whether the given word is spelled correctly, and gives suggestions if
        it's not.
        """
        if word == '':
            yield from self.provide_help('spell', client, message)
            return

        word = word.split(' ', 1)[0]
        dictionary = enchant.Dict("en_US")
        dictionary_uk = enchant.Dict("en_GB")

        # I don't want to make anyone angry, so I check both American and British English.
        if dictionary_uk.check(word):
            if dictionary.check(word):
                yield from client.send_message(message.channel, word + " is spelled correctly")
            else:
                yield from client.send_message(message.channel, word + " is spelled correctly (British)")
        elif dictionary.check(word):
            yield from client.send_message(message.channel, word + " is spelled correctly (American)")
        else:
            msg = word + " is not spelled correctly. Maybe you want one of these spellings:"
            sugWords = []
            for suggested_word in dictionary.suggest(word):
                    sugWords.append(suggested_word)
            for suggested_word in dictionary_uk.suggest(word):
                    sugWords.append(suggested_word)
            for suggested_word in sorted(set(sugWords)):  # removes duplicates
                msg = msg + " '" + suggested_word + "',"
            yield from client.send_message(message.channel, msg)

    @glados.Module.rules("^.*(\(spelling\?\)).*$")
    @glados.Module.rules("^.*(\(spell\?\)).*$")
    def spelling_in_brackets(self, client, message, match):
        # this abomination extracts the word before (spelling?) -- in this sentence said word would be "before"
        word = message.clean_content.split('(spelling?)')[0].strip().split()[-1]
        yield from self.spellcheck(client, message, word)
