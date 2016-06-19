import willie.module

counter = 0
message_counter = 0
messages = ['Java sucks, shut the fuck up', 'All of this java... You people make me sick', 'Java is for queers', 'Oh I thought you guys were talking about java beans', "What's all of this talk about enterprise software", "Java? Are you gay or something?", "The java virtual machine is fatter than your mom"]

@willie.module.rule('^.*java*.$')
def java_counter(bot, trigger):
	global counter
	global message_counter
	global messages
	counter += 1
	if counter > 5:
		bot.say(messages[message_counter])
		message_counter = (message_counter + 1) % len(messages)
		counter = 0
