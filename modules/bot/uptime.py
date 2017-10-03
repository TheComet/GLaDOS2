# coding=utf-8
"""
uptime.py - Uptime module
Copyright 2014, Fabian Neundorf
Licensed under the Eiffel Forum License 2.
http://sopel.chat
"""
import glados
from datetime import datetime
from datetime import timedelta
import random


class UpTime(glados.Module):

    messages = (
        "I've been sitting here for {} and I keep going!",
        "I'm still sitting here. It's been {} and I try!",
        "It's been so long, I can't even tell you. I think {}",
        "Sitting is a thing humans do. I actually just exist. I've been existing for {}",
        "I am but an abstract description being used in an abstract way. Been so for {}"
    )

    def __init__(self, bot, full_name):
        super(UpTime, self).__init__(bot, full_name)
        self.__started = datetime.utcnow()

    @glados.Module.command('uptime', '', 'Returns the uptime of this bot.')
    async def uptime(self, message, arg):
        delta = timedelta(seconds=round((datetime.utcnow() - self.__started).total_seconds()))
        await self.client.send_message(message.channel, random.choice(self.messages).format(delta))
