from willie import module
import codecs
import os

burns = [
    "OOOOOOOH YOU JUST GOT BURNED, SON",
    "BUUUUUUUUURNN",
    "APPLY LIQUID NITROGEN TO AREA OF BURN",
    "DO YOU NEED ICE? CAUSE' YOU JUST GOT BUUURNEED",
    "Is something burning? oh wait, it's you. YOU GOT BURNNNEED",
    "#BURN #APPLYWATER #GOHOMESON",
    "NEIN CAN HEAR YOU CAUSE JEWS GOT BURNED"
]
counter = 0

def configure(config):
    if config.option("Configure burns", False):
        config.interactive_add("burns", "burns_data_path", "Path to where you'd like to store the burn counts between users")

def setup(willie):
    global burns_dict
    global burns_data_file
    burns_data_file = os.path.join(willie.config.burns.burns_data_path, "burns.txt")
    
    burns_dict = dict()
    if os.path.isfile(burns_data_file):
        for line in codecs.open(burns_data_file, 'r', encoding='utf-8'):
            nick = line.split(": ")[0]
            count = int(line.split(": ")[1])
            burns_dict[nick] = count

def shutdown(willie):
    global burns_dict
    global burns_data_file

    with codecs.open(burns_data_file, 'a', encoding='utf-8') as f:
        for nick, count in burns_dict.iteritems():
            f.write(nick + ": " + count + "\n")

@module.commands("burn")
def burn_user(bot, trigger):
    global burns
    global counter
    global burns_dict

    if not trigger.group(2):
        bot.reply(".burn <user>")
        return

    user_being_burned = trigger.group(2)
    user_burning = trigger.nick

    burn = burns[counter]
    counter = (counter + 1) % len(burns)

    if not user_being_burned in burns_dict:
        burns_dict[user_being_burned] = 0
    if not user_burning in burns_dict:
        burns_dict[user_burning] = 0
    burns_dict[user_burning] += 1

    bot.say(user_being_burned + ": " + burn)
    bot.say(user_burning + ": " + str(burns_dict[user_burning]))
    bot.say(user_being_burned + ": " + str(burns_dict[user_being_burned]))
