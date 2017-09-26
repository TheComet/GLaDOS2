import glados
import random


class Flip(glados.Module):

    def get_help_list(self):
        return [
            glados.Help('flip', '[user]', 'Flip a coin... Or a user')
        ]

    @glados.Module.commands('flip')
    async def flip(self, message, user):
        """Flips a coin... or a user.
        Defaults to coin.
        """
        if user == '':
            await self.client.send_message(message.channel, "*flips a coin and... " + random.choice(["HEADS!*", "TAILS!*"]))
        else:
            msg = ""
            user = user.split('#', 1)[0].strip('@')
            if user.lower() == self.client.user.name.lower():
                user = message.author.name
                msg = "Nice try. You think this is funny? How about *this* instead:\n\n"
            char = "abcdefghijklmnopqrstuvwxyz"
            tran = "ɐqɔpǝɟƃɥᴉɾʞlɯuodbɹsʇnʌʍxʎz"
            table = str.maketrans(char, tran)
            name = user.translate(table)
            char = char.upper()
            tran = "∀qƆpƎℲפHIſʞ˥WNOԀQᴚS┴∩ΛMX⅄Z"
            table = str.maketrans(char, tran)
            name = name.translate(table)
            await self.client.send_message(message.channel, msg + "(╯°□°）╯︵ " + name[::-1])
