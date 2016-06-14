# this requires the showip command line tool
# https://github.com/TheComet93/showip

from willie import module
from subprocess import check_output

@module.commands('showip')
def showip(bot, trigger):
    hostname = trigger.group(2)
    ret = check_output(["/usr/local/bin/showip", hostname])
    bot.say(ret)

