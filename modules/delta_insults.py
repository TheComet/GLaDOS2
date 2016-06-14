from willie import module

chill_out_counter = 0
chill_out = ["Woahhh, chill the fuck out bro", "Says the guy with two gay daddies", "That was uncalled for"]

diety_counter = 0
diety_dammit = ["Allah dammit!", "Buddha dammit!", "Vishnu dammit!", "Shiva dammit!"]

@module.rule("^.*(what i thought).*$")
def what_i_thought(bot, trigger):
	bot.say(trigger.nick + ": Oh yeah? Think again")

@module.rule("^.*(i figured).*$")
def i_figured(bot, trigger):
        bot.say(trigger.nick + ": Oh yeah Einstein? Did Sherlock Holmes help you with that one?")

@module.rule("^.*(?=.*thought)(?=.*so).*$")
def thought_so(bot, trigger):
        bot.say(trigger.nick + ": Oh yeah? Think again")

@module.rule("^.*(?=.*get)(?=.*book).*$")
def getting_a_book(bot, trigger):
	bot.say("Another book? That's some expensive toilet paper.")

@module.rule("^.*(?=.*according)(?=.*book).*$")
def according_to_books(bot, trigger):
	bot.say(trigger.nick + ": Just because you read lots of books doesn't mean mommy loves you")

@module.rule("^.*(?=.*fuck)(?=.*queer).*$")
def fucking_queer_defense(bot, trigger):
        defend(bot, trigger)

@module.rule("^.*(?=.*fuck)(?=.*fag).*$")
def fucking_fag_defense(bot, trigger):
        defend(bot, trigger)

def defend(bot, trigger):
	global chill_out
	global chill_out_counter
	bot.say(trigger.nick + ": " + chill_out[chill_out_counter])
	chill_out_counter = (chill_out_counter + 1) % len(chill_out)

@module.rule("^(((?=.*goddammit).*)|((?=.*goddamnit).*)|((?=.*goddangit).*)).*$")
def allah_dammit(bot, trigger):
        global diety_counter
        global diety_dammit
        bot.say(trigger.nick + ": " + diety_dammit[diety_counter])
        diety_counter = (diety_counter + 1) % len(diety_dammit)
