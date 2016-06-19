from willie import module
from spellcheck import spellcheck

# spellcheck is performed on whatever word is returned from trigger.group(2).
# this class will replace that object and return the word we need
class FakeTrigger(object):
    def __init__(self, word):
        self.__word = word
    def group(self, index):
        return self.__word

@module.rule("^.*(\(spelling\?\)).*$")
def spelling_in_brackets(bot, trigger):
    # this abomination extracts the word before (spelling?) -- in this sentence said word would be "before"
    word = trigger.raw.split("(spelling?)")[0].strip().split(" ")[-1]
    fake_trigger = FakeTrigger(word)
    spellcheck(bot, fake_trigger)
