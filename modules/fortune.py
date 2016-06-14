from willie import module

import commands

@module.commands('fortune')
def fortune(bot, trigger):
	fortune = commands.getoutput('/usr/games/fortune')
	for line in fortune.rsplit("\n"):
		bot.say(line)

@module.commands('bofh')
def bastard_operator_from_hell_quote(bot, trigger):
    excuse = commands.getoutput("/usr/games/fortune bofh-excuses | tr '\n' ' '")
    for line in excuse.rsplit("\n"):
        bot.say(line)
