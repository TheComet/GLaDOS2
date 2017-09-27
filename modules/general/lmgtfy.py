# coding=utf-8
"""
lmgtfy.py - Sopel Let me Google that for you module
Copyright 2013, Dimitri Molenaars http://tyrope.nl/
Licensed under the Eiffel Forum License 2.
http://sopel.chat/
"""
from __future__ import unicode_literals, absolute_import, print_function, division
import glados
import urllib.parse


class LMGTFY(glados.Module):
    @glados.Module.command('lmgtfy', '<search term>', 'Generates a "Let me google that for you" link')
    @glados.Module.command('lmgify', '', '')
    @glados.Module.command('gify', '', '')
    @glados.Module.command('gtfy', '', '')
    async def googleit(self, message, arg):
        arg = urllib.parse.quote(arg)
        await self.client.send_message(message.channel, 'http://lmgtfy.com/?q=' + arg)
