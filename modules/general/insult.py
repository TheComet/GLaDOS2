import glados
import random

# Take from http://lolsnaps.com/funny/147275/probably-my-favorite-insult-generator-you-twat-gobbling-douc
A = [
    'cunt',
    'shit'
    'turd',
    'fuck',
    'douche',
    'ball',
    'testicle',
    'cock',
    'dick',
    'nut',
    'sack',
    'pussy',
    'piss',
    'cum',
    'ass',
    'bitch',
    'twat',
    'tit',
    'whore',
    'fat',
    'dyke',
    'fag',
    'nazi',
    'queer',
    'queef',
    'slut',
    'asshole',
    'bastard',
    'anal'
]

B = [
    'licking',
    'eating',
    'loving',
    'sucking',
    'kissing',
    'worshipping',
    'guzzling',
    'gobbling',
    'chugging',
    'sniffing',
    'pounding',
    'riding',
    'grinding',
    'banging',
    'drinking',
    'inhaling',
    'rubbing',
    'busting',
    'squeezing',
    'peddling'
]

C = [
    'waffle',
    'egg',
    'juice',
    'butter',
    'froth',
    'foam',
    'fluff',
    'cheese',
    'dumpling',
    'noodle',
    'nugget',
    'tostada',
    'fritter',
    'cream',
    'salami',
    'taco',
    'jelly',
    'sausage',
    'meat',
    'jam',
    'pancake',
    'salad',
    'syrup',
    'broth',
    'sandwich',
    'pizza',
    'soup',
    'souffle',
    'twinkie',
    'bean',
    'tortilla',
    'brocolli',
    'bologna'
]


class Insult(glados.Module):
    @staticmethod
    def gen_insult():
        words = list()
        while True:
            words.append(random.choice(A))
            if random.randint(0, 1):
                break
            words.append(random.choice(B))
        words.append(random.choice(C))
        return ' '.join(words)

    @glados.Module.command('insult', '[user]', 'Generate a random insult and direct it at a user.')
    async def insult(self, message, content):
        if not content:
            await self.client.send_message(message.channel, 'You {}!'.format(self.gen_insult()), tts=True)
        else:
            await self.client.send_message(message.channel, '{0}: You {1}!'.format(content, self.gen_insult()), tts=True)

