#!/home/cometbot/discord/latex_bot/env2/bin/python

import discord
import urllib
import random
import os
import chanrestrict
import json
import shutil
import asyncio
import subprocess


HELP_MESSAGE = r"""
Hello! I'm the *LaTeX* math bot!

You can type mathematical *LaTeX* into the chat and I'll automatically render it!

Simply use the `!tex` command.

**Examples**

`!tex x = 7`

`!tex \sqrt{a^2 + b^2} = c`

`!tex \int_0^{2\pi} \sin{(4\theta)} \mathrm{d}\theta`

**Notes**

Using the `\begin` or `\end` in the *LaTeX* will probably result in something failing.

"""

LATEX_FRAMEWORK = r"""
\documentclass[varwidth=true]{standalone}
\usepackage{amsmath}
\usepackage{color}
\usepackage[usenames,dvipsnames,svgnames,table]{xcolor}
\usepackage{amsfonts}
\usepackage{amssymb}
\usepackage{esint}
\usepackage{listings}
\usepackage{mathtools}

\DeclarePairedDelimiter\ceil{\lceil}{\rceil}
\DeclarePairedDelimiter\floor{\lfloor}{\rfloor}

\begin{document}
{\color{orange}
\begin{align*}
__DATA__
\end{align*}}
\end{document}
"""

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

    def get_latex(msg):
        msg = [msg]
        for c in settings['commands']['render']:
            if not any(c in x for x in msg):
                continue
            msg = [x.strip() for item in msg for x in item.split("```" + c)]
            msg = [x.strip() for item in msg for x in item.split("`" + c)]
            msg = [x.strip() for item in msg for x in item.split(c)]
            msg = [x.strip() for item in msg for x in item.split("```")]
            msg = [x.strip() for item in msg for x in item.split("`")]
        # every second item is latex
        return msg[1::2]


    # Generate LaTeX locally. Is there such things as rogue LaTeX code?
    def generate_image(latex, message):
        num = str(random.randint(0, 2 ** 31))
        latex_file = 'tex/' + num + '.tex'
        dvi_file = 'tex/' + num + '.dvi'
        png_file = 'tex/' + num + '1.png'
        with open(latex_file, 'w') as tex:
            latex = LATEX_FRAMEWORK.replace('__DATA__', latex)
            tex.write(latex)
            tex.flush()
            tex.close()
        try:
            subprocess.check_output(['latex', '-no-shell-escape', '-interaction', 'nonstopmode', '-halt-on-error', '-file-line-error', '-output-directory=tex', latex_file])
        except subprocess.CalledProcessError as e:
            vprint('\n'.join(str(e.output).split('\\n')))
            errors = [x.strip() for x in str(e.output).split('\\n') if x.startswith('!') or '.tex:' in x]
            lines = [int(x) - 2 for error in errors for x in error.split(':') if x.isdigit()]
            latexlines = [x for n, x in enumerate(latex.split('\n')) if n in lines]
            errormsg = "Error: {0}\n{1}".format('\n'.join([x.strip() for x in str(e.output).split('\\n') if x.startswith('!') or '.tex:' in x]),
                                         '\n'.join(latexlines))
            return (False, errormsg)
        subprocess.call(['dvipng', '-q*', '-D', '200', '-T', 'tight', '-bg', 'Transparent', '-o', png_file, dvi_file])
        #subprocess.check_call(['dvipng', '-q*', '-D', '300', '-T', 'tight', dvi_file])

        return (True, png_file)

    # More unpredictable, but probably safer for my computer.
    def generate_image_online(latex, message):
        url = 'http://frog.isima.fr/cgi-bin/bruno/tex2png--10.cgi?'
        url += urllib.parse.quote(latex, safe='')
        fn = str(random.randint(0, 2 ** 31)) + '.png'
        urllib.request.urlretrieve(url, fn)
        return fn

    @client.event
    @asyncio.coroutine
    #@chanrestrict.apply
    def on_message(message):
        if message.author.bot:
            return

        msg = message.content
        if not any(x in msg for x in ("!tex", "!fortune", "!bofh")):
            return

        if any(x in msg for x in ("\\write18", "\\input", "\\include", "{align*}", "\\loop", "\\repeat", "\\csname", "\\endcsname")):
            yield from client.send_message(message.channel, "Error: Trying to be naughty, are we?")
            return

        # troll dsm
        #if message.author.name == "dsm":
        #    msg = "!tex \\color{pink} \\text {dsm loves dongers}"
       
        for latex in get_latex(msg):
            vprint('Latex:', latex)

            if settings['renderer'] == 'external':
                fn = generate_image_online(latex, message)
            if settings['renderer'] == 'local':
                fn = generate_image(latex, message)

            if fn[0] == False:
                yield from client.send_message(message.channel, fn[1])
                return

            if fn[0] == True and os.path.getsize(fn[1]) > 0:
                yield from client.send_file(message.channel, fn[1])
                vprint('Success!')
            else:
                vprint('Failure.')

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

