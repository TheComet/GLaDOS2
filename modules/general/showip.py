# this requires the showip command line tool
# https://github.com/TheComet93/showip

import glados
from subprocess import check_output


class ShowIP(glados.Module):
    @glados.Module.command('showip', '<URL>', 'Performs a DNS lookup and returns the IP address')
    async def showip(self, message, content):
        if content == '':
            await self.provide_help('showip', message)
            return

        ret = check_output(['/usr/local/bin/showip', content]).decode('utf-8')
        await self.client.send_message(message.channel, ret)
