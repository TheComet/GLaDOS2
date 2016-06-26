import glados
import random


class Goto(glados.Module):
    def get_help_list(self): return list()

    responses = (
        '{}, wtf? Don\'t ever use goto it sucks.',
        '{}, if you have the option of using goto or punching yourself in the face I recommend you go with the latter.',
        'WRONG. {}, you\'re not getting it. Using goto in any situation is WRONG',
        '{}, stop spouting garbage about goto',
        'Ugh, goto is disgusting',
        'Don\'t try to use goto because you think you are "clever", {}. You\'re only making things worse.',
        'Ugh. No. Goto is too disgusting for words.',
        'Anybody who uses goto is just terminally confused.',
        'Quite frankly, if you use goto, you should be shot.',
        '{}, your use of goto just shows how stupid you really are.'
    )

    @glados.Module.rules('^.*goto.*$')
    def goto(self, message, match):
        yield from self.client.send_message(message.channel, random.choice(self.responses).format(message.author.name))


class Singleton(glados.Module):
    def get_help_list(self): return list()

    responses = (
        'Singleton? That\'s just disgusting crazy talk. Christ, {}, get a grip on yourself.',
        'Yeah, singletons are a hack, and they\'re wrong, and we should figure out how to do it right',
        'Oh, please, singletons are a British-level understatement. It\'s like calling WWII "a small bother". That\'s too ugly to live.',
        '{}, please don\'t use this idiotic singleton. It is wrong... Anybody who argues anything else is wrong, or confused, or confusing.',
        '{}, it\'s things like singletons that make me want to dig my eyes out with a spoon',
        'Singletons. It\'s stupid. It\'s wrong. It\'s *bad*.',
        '{}, really? Singletons? This is just another example of why people like you should be given extensive education about birth control and how not to procreate.',
        'Singletons are pure and utter *BS*.',
        'Actually, {}, the real fix to singletons would be to not be stupid.',
        '{}: WHAT? NONE OF WHAT YOU SAY MAKES ANY SENSE.'
    )

    @glados.Module.rules('^.*singleton.*$')
    def singletons(self, message, match):
        yield from self.client.send_message(message.channel, random.choice(self.responses).format(message.author.name))
