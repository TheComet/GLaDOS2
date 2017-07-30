# coding=utf-8

import random
import glados


class Hello(glados.Module):

    def get_help_list(self): return []

    @glados.Module.rules(r'(?i)(hi|hello|hey|greetings),? glados.*$')
    def respond_hello(self, message, match):
        greeting = random.choice(('Hi ', 'Hey ', 'Hello '))
        greeting += message.author.name + random.choice(('', '!'))
        greeting += random.choice((' No one ever says hi to me... Are you a bot?',
                                   ' I\'m flattered you think I\'m human',
                                   ' Do you always say hi to robots or are you just lonely?'))
        yield from self.client.send_message(message.channel, greeting)

    @glados.Module.rules('^(hi|hello|hey|greetings)$')
    def hello(self, message, match):
        greeting = random.choice(('Hi', 'Hey', 'Hello'))
        punctuation = random.choice(('', '!'))
        yield from self.client.send_message(message.channel, greeting + ' ' + message.author.name + punctuation)


class Morgen(glados.Module):
    
    def get_help_list(self): return []

    @glados.Module.rules('^.*(morgen|abend|abendgruss).*$')
    def morgen(self, message, match):
        greeting = random.choice(('Heil', 'Tach'))
        punctuation = random.choice(('', '!'))
        yield from self.client.send_message(message.channel, greeting + ' ' + message.author.name + punctuation)


class Swiss(glados.Module):
    def get_help_list(self): return list()

    @glados.Module.rules(r'.*(grüetzi|grützi|grüessech|grüessich).*')
    def hii(self, message, match):
        greeting = random.choice(('Hoi büebli!', 'Sali!', 'Grüessech wohl', 'Grüessgott', 'S Wätter esch net schlächt hüt, äs chutet e chli'))
        yield from self.client.send_message(message.channel, greeting)


class Insult(glados.Module):

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

    def get_help_list(self): return []

    def respond(self, message):
        yield from self.client.send_message(message.channel, self.phrases[self.counter].format(message.author.name))
        self.counter = (self.counter + 1) % len(self.phrases)

    @glados.Module.rules("^.*(?=.*shut)(?=.*up)(?=.*glados).*$")
    def shut_up(self, message, match):
        yield from self.respond(message)

    @glados.Module.rules("^.*(?=.*fuck)(?=.*glados).*$")
    def fuck_you(self, message, match):
        yield from self.respond(message)

    @glados.Module.rules("^.*(?=.*glados)(?=.*cunt).*$")
    def you_cunt(self, message, match):
        yield from self.respond(message)


class Hmkay(glados.Module):
    def get_help_list(self): return []

    @glados.Module.rules("^.*(?=.*hmkay).*$")
    def hmkay(self, message, match):
        yield from self.client.send_message(message.channel, "HHHMMMMKAAAYYY. DRUGS ARE BAD HHMKAY")
