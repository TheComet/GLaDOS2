from willie import module

@module.commands("approve")
def approve(bot, trigger):
    bot.say(trigger.nick + " approves. I don't")

