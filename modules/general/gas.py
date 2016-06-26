import glados


class Gas(glados.Module):

    @glados.Module.commands("gas")
    def gas(self, message, user):
        if not user:
            self.client.send_message(message.channel, "Ab ins gas du Jude!")
        else:
            if not user.lower().find("texbot") == -1:
                self.client.send_message(message.channel, "Nice try. Get comfortable while I warm up the neurotoxin emitters.")
            else:
                self.client.send_message(user + ": Ab ins gas du Jude!")
