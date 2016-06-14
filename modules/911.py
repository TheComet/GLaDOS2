from willie import module

@module.rule("^.*(9/11).*$")
def nine_eleven(bot, trigger):
    bot.say("RIP The 2976 American people who lost their lives on 9/11 and RIP the 48,644 Afghan and 1,690,903 Iraqi and 350,000 Pakistani people who paid the ultimate price for a crime they did not commit")

