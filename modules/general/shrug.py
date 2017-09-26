import glados
import discord
import random

shrugs = [
    '¯\_(ツ)_/¯',
    'I Dunno LOL ¯\(°_o)/¯',
    'http://replygif.net/thumbnail/855.gif',
    'http://www.reactiongifs.com/r/dnno1.gif',
    'http://i1.kym-cdn.com/entries/icons/original/000/006/039/shrugging-pinkie-pie.png',
    'http://www.reactiongifs.com/r/well.gif',
    'http://www.reactiongifs.com/r/dunno1.gif',
    'http://www.reactiongifs.com/wp-content/uploads/2013/11/shrug-house.gif',
    'http://i0.kym-cdn.com/photos/images/original/000/003/308/xjobz5hofa.jpg',
    'http://i1.kym-cdn.com/photos/images/newsfeed/000/991/996/a7c.jpg',
    'https://uboachan.net/warc/src/1340433133397.jpeg',
    'http://i.imgur.com/VQ9Cdad.png',
    'http://i.imgur.com/l4KQj8w.png',
    'http://i.imgur.com/p4YJfO2.png',
    'http://i.imgur.com/XUsxfpG.png'
]


class Shrug(glados.Module):
    @glados.Module.command('shrug', '', 'Shrug')
    async def shrug(self, message, args):
        shrug = random.choice(shrugs)
        await self.client.send_message(message.channel, shrug)

