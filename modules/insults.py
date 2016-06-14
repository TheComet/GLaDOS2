from willie import module

@module.rule("^.*(?=.*damn)(?=.*straight).*$")
def damn_straight(bot, trigger):
    bot.say(trigger.nick + ": Straighter than the pole your mom dances on?")

