"""
8ball.py - Ask the magic 8ball a question
Copyright 2013, Sander Brand http://brantje.com
Licensed under the Eiffel Forum License 2.
http://sopel.dfbta.net
"""

import glados
import random

messages = ["It is certain",
            "It is decidedly so",
            "Without a doubt",
            "Yes definitely",
            "You may rely on it",
            "As I see it yes",
            "Most likely",
            "Outlook good",
            "Yes",
            "Signs point to yes",
            "Don't count on it",
            "My reply is no",
            "God says no",
            "Very doubtful",
            "Outlook not so good",
            "r u srs?",
            "lol yeah right. In your dreams maybe",
            "No.",
            "Definitely not.",
            "Maybe in a future life"]


class EightBall(glados.Module):

    def get_help_list(self):
        return [
            glados.Help('8/8ball', '<question>', 'Ask the magical 8-ball a yes/no question')
        ]

    @glados.Module.commands('8', '8ball')
    def ball(self, message, content):
        if content == '':
            yield from self.provide_help('8', message)
            return

        yield from self.client.send_message(message.channel, random.choice(messages))
