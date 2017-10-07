from glados import Module

chill_out_counter = 0
chill_out = ["Woahhh, chill the fuck out bro", "Says the guy with two gay daddies", "That was uncalled for"]

diety_counter = 0
diety_dammit = ["Allah dammit!", "Buddha dammit!", "Vishnu dammit!", "Shiva dammit!"]


class DeltaInsults(Module):

    @Module.rule("^.*(what i thought).*$")
    async def what_i_thought(self, message, content):
        await self.client.send_message(message.channel, message.author.name + ": Oh yeah? Think again")

    @Module.rule("^.*(i figured).*$")
    async def i_figured(self, message, content):
            await self.client.send_message(message.channel, message.author.name + ": Oh yeah Einstein? Did Sherlock Holmes help you with that one?")

    @Module.rule("^.*(?=.*thought)(?=.*so).*$")
    async def thought_so(self, message, content):
            await self.client.send_message(message.channel, message.author.name + ": Oh yeah? Think again")

    @Module.rule("^.*(?=.*get)(?=.*book).*$")
    async def getting_a_book(self, message, content):
        await self.client.send_message(message.channel, "Another book? That's some expensive toilet paper.")

    @Module.rule("^.*(?=.*according)(?=.*book).*$")
    async def according_to_books(self, message, content):
        await self.client.send_message(message.channel, message.author.name + ": Just because you read lots of books doesn't mean mommy loves you")

    @Module.rule("^.*(?=.*fuck)(?=.*fag).*$")
    @Module.rule("^.*(?=.*fuck)(?=.*queer).*$")
    async def fucking_fag_defense(self, message, content):
        global chill_out
        global chill_out_counter
        await self.client.send_message(message.channel, message.author.name + ": " + chill_out[chill_out_counter])
        chill_out_counter = (chill_out_counter + 1) % len(chill_out)

    @Module.rule("^(((?=.*goddammit).*)|((?=.*goddamnit).*)|((?=.*goddangit).*)).*$")
    async def allah_dammit(self, message, content):
        global diety_counter
        global diety_dammit
        await self.client.send_message(message.channel, message.author.name + ": " + diety_dammit[diety_counter])
        diety_counter = (diety_counter + 1) % len(diety_dammit)
