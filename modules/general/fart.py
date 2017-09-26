import glados
from random import randint

fart_counter = 0
fart_sounds = [
    "toot",
    "pbtpbtpbt",
    "paarp",
    "prrrbbbbt",
    "has a small explosion between his or her legs",
    "lets loose a land-locked foghorn",
    "lets go an ass flapper",
    "broke wind",
    "launched a butt bazooka",
    "roared from the rear",
    "is insane in the methane",
    "gassed the room"]


class Fart(glados.Module):
    @glados.Module.command("fart")
    async def fart(self, message, content):
        global fart_counter
        global fart_sounds
        await self.client.send_message(message.author.nick + ": " + fart_sounds[fart_counter])
        fart_counter = randint(0, len(fart_sounds) - 1)
