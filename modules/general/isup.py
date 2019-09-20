# coding=utf-8
"""Simple website status check with isup.me"""
# Author: Elsie Powell http://embolalia.com

from __future__ import unicode_literals, absolute_import, print_function, division
import glados
import re
import socket
import urllib.request


class IsUp(glados.Module):
 
    # https://stackoverflow.com/questions/2532053/validate-a-hostname-string
    def is_valid_hostname(self, hostname):
        try:
            if len(hostname) > 255:
                return False
            if hostname[-1] == ".":
                hostname = hostname[:-1] # strip exactly one dot from the right, if present
            allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
            return all(allowed.match(x) for x in hostname.split("."))
        except Exception as exception:
            return False
    
    @glados.Module.command('isup', '<website>', 'Checks whether a website is up or not.')
    async def isup(self, message, site):
        """isup.me website status checker"""

        if not site:
            await self.provide_help('isup', message)
            return

        if site[:7] != 'http://' and site[:8] != 'https://':
            if '://' in site:
                protocol = site.split('://')[0] + '://'
                await self.client.send_message(message.channel, "Try it again without the {}".format(protocol))
                return
            else:
                site = 'https://' + site

        if not '.' in site:
            site += ".com"

        try:
            response = urllib.request.urlopen(site, timeout=5).getcode()
        except Exception as e:
            await self.client.send_message(message.channel, site + ' looks down from here. (Exception: {})'.format(str(e)))
            return

        site = site + f"looks fine to me (Return code {response})" if response >= 200 and response < 300 else site + f" returned code {response}"
        await self.client.send_message(message.channel, site)
    
    @glados.Module.command('isopen', '<host:port>', 'Checks if a port is open.')
    async def isopen(self, message, hostport):
        if not hostport or len(hostport.split(':')) != 2:
            await self.provide_help('isopen', message)
            return
        
        hostname, port = hostport.split(':')
        if not is_valid_hostname(hostname):
            await self.client.send_message(message.channel, f"{hostname} is not a valid hostname")
            return
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        
        res = f"Port {port} is open on {hostname}!" if sock.connect_ex((hostname, int(port))) == 0 else f"Port {port} is closed on {hostname}"
        await self.client.send_message(message.channel, res)
        
    
    @glados.Module.rule(r'(?i).*?(gdnet|gd.net|gamedev|gamedev.net).*?(down\??)')
    async def is_gdnet_down(self, message, match):
        await self.isup(message, 'https://gamedev.net')
