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

    def __init__(self, bot, full_name):
        super(Burn, self).__init__(bot, full_name)

        self.counter = 0
        self.burns = dict()

    @glados.Module.command('burn', '<user>', 'Burn a user when you feel like he just got pwned')
    async def burn_user(self, message, content):
        global burns

        user_being_burned = content.strip('@')
        user_burning = message.author.name

        burn = burns[self.counter]
        self.counter = (self.counter + 1) % len(burns)

        if not user_burning in self.burns:
            self.burns[user_burning] = dict()
        if not user_being_burned in self.burns[user_burning]:
            self.burns[user_burning] = {user_being_burned: 0}
        if not user_being_burned in self.burns:
            self.burns[user_being_burned] = {user_burning: 0}
        self.burns[user_burning][user_being_burned] += 1

        response = "@{0} {1}\n{2}: {3}\n{4}: {5}".format(user_being_burned, burn,
                                                         user_burning, self.burns[user_burning][user_being_burned],
                                                         user_being_burned, self.burns[user_being_burned][user_burning])
        await self.client.send_message(message.channel, response)
