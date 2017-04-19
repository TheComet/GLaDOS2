import glados

burns = [
    "OOOOOOOH YOU JUST GOT BURNED, SON",
    "BUUUUUUUUURNN",
    "APPLY LIQUID NITROGEN TO AREA OF BURN",
    "DO YOU NEED ICE? CAUSE' YOU JUST GOT BUUURNEED",
    "Is something burning? oh wait, it's you.",
    "#BURN #APPLYWATER #GOHOMESON",
    "NEIN CAN HEAR YOU CAUSE JEWS GOT BURNED"
]


class Burn(glados.Module):

    def __init__(self):
        super(Burn, self).__init__()
        self.counter = 0

    def get_help_list(self):
        return [
            glados.Help('burn', '<user>', 'Burn a user when you feel like he just got pwned')
        ]

    @glados.Module.commands("burn")
    def burn_user(self, message, content):
        global burns

        if content == "":
            yield from self.provide_help('burn', message)
            return

        user_being_burned = content.strip('@')
        user_burning = message.author.name

        burn = burns[self.counter]
        self.counter = (self.counter + 1) % len(burns)

        if not user_burning in self.get_memory()['burns']:
            self.get_memory()['burns'][user_burning] = dict()
        if not user_being_burned in self.get_memory()['burns'][user_burning]:
            self.get_memory()['burns'][user_burning] = {user_being_burned: 0}
        if not user_being_burned in self.get_memory()['burns']:
            self.get_memory()['burns'][user_being_burned] = {user_burning: 0}
        self.get_memory()['burns'][user_burning][user_being_burned] += 1

        response = "@{0} {1}\n{2}: {3}\n{4}: {5}".format(user_being_burned, burn,
                                                         user_burning, self.get_memory()['burns'][user_burning][user_being_burned],
                                                         user_being_burned, self.get_memory()['burns'][user_being_burned][user_burning])
        yield from self.client.send_message(message.channel, response)
