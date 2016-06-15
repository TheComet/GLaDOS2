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

    def __init__(self, settings):
        super(Burn, self).__init__(settings)
        self.counter = 0
        self.burns_dict = dict()

    @glados.Module.commands("burn")
    def burn_user(self, client, message, content):
        global burns

        if content == "":
            yield from client.send_message(message.channel, ".burn <user>")
            return

        user_being_burned = content.strip('@')
        user_burning = message.author.name

        burn = burns[self.counter]
        self.counter = (self.counter + 1) % len(burns)

        if not user_burning in self.burns_dict:
            self.burns_dict[user_burning] = dict()
        if not user_being_burned in self.burns_dict[user_burning]:
            self.burns_dict[user_burning] = {user_being_burned: 0}
        if not user_being_burned in self.burns_dict:
            self.burns_dict[user_being_burned] = {user_burning: 0}
        self.burns_dict[user_burning][user_being_burned] += 1

        response = "@{0} {1}\n{2}: {3}\n{4}: {5}".format(user_being_burned, burn,
                                                         user_burning, self.burns_dict[user_burning][user_being_burned],
                                                         user_being_burned, self.burns_dict[user_being_burned][user_burning])
        yield from client.send_message(message.channel, response)
