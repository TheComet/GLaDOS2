#!/home/cometbot/discord/GLaDOS2/env/bin/python

import os
import shutil
import glados
import sys


if not os.path.isfile('settings.json'):

    shutil.copyfile('settings_default.json', 'settings.json')
    print('Now you can go and edit `settings.json`.')
    print('See README.md for more information on these settings.')

    sys.exit(0)


if __name__ == '__main__':
    b = glados.Bot()
    b.run()
    glados.log('Stopped -- this shouldn\'t happen')
