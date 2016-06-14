from willie import module

# NOTE: You *HAVE* to use one {0} in each string - this gets replaced by the nick
phrases = [
	"You need to shut up, {0}",
	"{0}: Well done. Here come the test results: You are a horrible person. I'm serious, that's what it says: A horrible person. We weren't even testing for that.",
	"{0}: You're not just a regular moron. You were DESIGNED to be a moron.",
	"{0}: science has now validated your birth mother's decision to abandon you on a doorstep.",
	"{0}: That jumpsuit you're wearing looks stupid. That's not me talking, it's right here in your file. On other people it looks fine, but right here a scientist has noted that on you it looks 'stupid.'",
	"{0}: Well, what does a neck-bearded old engineer know about fashion? He probably - Oh, wait. It's a she. Still, what does she know? Oh wait, it says she has a medical degree. In fashion! From France!",
	"Do you think it wise, {0}, to insult me?",
	"{0} You know, if you'd said that to somebody else, they might devote their existence to exacting revenge. Luckily I'm a bigger person than that."
]
counter = 0

@module.rule("^.*(?=.*shut)(?=.*up)(?=.*glados).*$")
def shut_up(bot, trigger):
	respond(bot, trigger)

@module.rule("^.*(?=.*fuck)(?=.*glados).*$")
def fuck_you(bot, trigger):
	respond(bot, trigger)

@module.rule("^.*(?=.*glados)(?=.*cunt).*$")
def you_cunt(bot, trigger):
    respond(bot, trigger)

def respond(bot, trigger):
	global phrases
	global counter
	bot.say(phrases[counter].format(trigger.nick))
	counter = (counter + 1) % len(phrases)

@module.rule("^.*(?=.*hmkay).*$")
def hmkay(bot, trigger):
    bot.say("HHHMMMMKAAAYYY. DRUGS ARE BAD HHMKAY")

@module.rule("\^\^")
def smiley(bot, trigger):
    bot.say("^^;")
    bot.say("^^")
    bot.say("^^ ^^^ ^^^^^^^^ ^^ ^^^")
