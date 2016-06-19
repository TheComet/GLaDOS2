from willie import module
from random import choice

colours = [
    'red',
    'green',
    'blue',
    'yellow',
    'white',
    'pink',
    'orange'
]

hot_colour = None
cut_wires = list()

@module.commands('plant')
def plant_bomb(bot, trigger):
    global hot_colour
    global cut_wires

    if hot_colour:
        bot.reply('The bomb is already planted!')
        return

    hot_colour = choice(colours)
    cut_wires = list()
    bot.say('{0} has planted the bomb! Attempt to diffuse with ".cut {1}"'.format(trigger.nick, '/'.join(colours)))

@module.commands('cut')
def cut(bot, trigger):
    global hot_colour
    global cut_wires

    if not hot_colour:
        bot.reply('You must plant the bomb first with ".plant"')
        return

    cutting = trigger.group(2)
    if not cutting:
        bot.reply("You need to cut a colour you idiot")
        return
    cutting = cutting.lower()
    if not cutting in colours:
        bot.reply("This bomb doesn't have any wires with the colour {}".format(cutting))
        return
    if cutting in cut_wires:
        bot.reply('The {} wire has already been cut!'.format(cutting))
        return

    cut_wires.append(cutting)
    bot.say('{0} cuts the {1} wire...'.format(trigger.nick, cutting))

    if cutting == hot_colour:
        bot.say('*BOOOOOM*')
        bot.say('{} looses!'.format(trigger.nick))
        hot_colour = None

