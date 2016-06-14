import discord
import os
import chanrestrict
import json
import shutil
import asyncio
import subprocess


if not os.path.isfile('settings.json'):

    shutil.copyfile('settings_default.json', 'settings.json')
    print('Now you can go and edit `settings.json`.')
    print('See README.md for more information on these settings.')

else:

    def vprint(*args, **kwargs):
        if settings.get('verbose', False):
            print(*args, **kwargs)

    settings = json.loads(open('settings.json').read())

    chanrestrict.setup(settings['channels']['whitelist'],
                       settings['channels']['blacklist'])

    client = discord.Client()



        if msg in settings['commands']['help']:
            vprint('Showing help')
            yield from client.send_message(message.author, HELP_MESSAGE)

        if any(msg.startswith(x) for x in settings['commands']['fortune']):
            vprint('generating fortune')
            fortune = subprocess.check_output(['/usr/games/fortune']).decode('UTF-8')
            yield from client.send_message(message.channel, fortune);
        if any(msg.startswith(x) for x in settings['commands']['bofh']):
            fortune = subprocess.check_output(['/usr/games/fortune', 'bofh-excuses']).decode('UTF-8')
            yield from client.send_message(message.channel, fortune)

    @client.event
    @asyncio.coroutine
    def on_ready():
        vprint('LaTeX Math Bot!')
        vprint('Running as', client.user.name)

@asyncio.coroutine
def main_task():
    yield from client.login(settings['login']['token'])
    yield from client.connect()

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(main_task())
except:
    loop.run_until_complete(client.logout())
    raise
finally:
    loop.close()

