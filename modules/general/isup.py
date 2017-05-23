# coding=utf-8
"""Simple website status check with isup.me"""
# Author: Elsie Powell http://embolalia.com

from __future__ import unicode_literals, absolute_import, print_function, division
import glados
import urllib.request


class IsUp(glados.Module):

    def get_help_list(self):
        return [
            glados.Help('isup', '<website>', 'Checks whether a website is up or not.')
        ]

    @glados.Module.commands('isup')
    def isup(self, message, site):
        """isup.me website status checker"""

        if not site:
            yield from self.provide_help('isup', message)
            return

        if site[:7] != 'http://' and site[:8] != 'https://':
            if '://' in site:
                protocol = site.split('://')[0] + '://'
                yield from self.client.send_message(message.channel, "Try it again without the {}".format(protocol))
                return
            else:
                site = 'https://' + site

        if not '.' in site:
            site += ".com"

        try:
            response = urllib.request.urlopen(site).read()
        except Exception:
            yield from self.client.send_message(message.channel, site + ' looks down from here.')
            return

        if response:
            yield from self.client.send_message(message.channel, site + ' looks fine to me.')
        else:
            yield from self.client.send_message(message.channel, site + ' is down from here.')

    @glados.Module.rules(r'(?i).*?(gdnet|gd.net|gamedev|gamedev.net).*?(down\??)')
    def is_gdnet_down(self, message, match):
        yield from self.isup(message, 'https://gamedev.net')
    
