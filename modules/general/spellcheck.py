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

    @glados.Module.command('spell', '<word>', 'Says whether the given word is spelled correctly, and gives suggestions '
                           'if it\'s not')
    async def spellcheck(self, message, word):
        """
        Says whether the given word is spelled correctly, and gives suggestions if
        it's not.
        """
        if word == '':
            await self.provide_help('spell', message)
            return

        word = word.split(' ', 1)[0]
        dictionary = enchant.Dict("en_US")
        dictionary_uk = enchant.Dict("en_GB")

        # I don't want to make anyone angry, so I check both American and British English.
        if dictionary_uk.check(word):
            if dictionary.check(word):
                await self.client.send_message(message.channel, word + " is spelled correctly")
            else:
                await self.client.send_message(message.channel, word + " is spelled correctly (British)")
        elif dictionary.check(word):
            await self.client.send_message(message.channel, word + " is spelled correctly (American)")
        else:
            msg = word + " is not spelled correctly. Maybe you want one of these spellings:"
            sugWords = []
            for suggested_word in dictionary.suggest(word):
                    sugWords.append(suggested_word)
            for suggested_word in dictionary_uk.suggest(word):
                    sugWords.append(suggested_word)
            for suggested_word in sorted(set(sugWords)):  # removes duplicates
                msg = msg + " '" + suggested_word + "',"
            await self.client.send_message(message.channel, msg)

    @glados.Module.rule("^.*?(\\S+)\\s+\((spelling|spell|sp|spellig|selipng)\??\).*$")
    async def spelling_in_brackets(self, message, match):
        # this abomination extracts the word before (spelling?) -- in this sentence said word would be "before"
        word = message.clean_content.split('(spelling?)')[0].strip().split()[-1]
        word = match.group(1)
        await self.spellcheck(message, word)


class AutoCorrect(glados.Module):
    @glados.Module.rule('^.*(?i)((sh|c|w)ould|might)\\s+of\\b.*$')
    async def shouldof(self, message, match):
        await self.client.send_message(message.channel, '{} have*'.format(match.group(1)))
