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

class UpTime(glados.Module):

    def __init__(self, settings):
        super().__init__(settings)
        self.__started = datetime.utcnow()

    def get_help_list(self):
        return [
            glados.Help('uptime', '', 'Returns the uptime of this bot.')
        ]

    @glados.Module.commands('uptime')
    def uptime(self, client, message, arg):
        delta = timedelta(seconds=round((datetime.utcnow() - self.__started).total_seconds()))
        yield from client.send_message(message.channel, "I've been sitting here for {} and I keep going!".format(delta))
