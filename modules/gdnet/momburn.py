import glados
import discord


BURN_EMOJI = "\N{FIRE}"
DOWN_EMOJI = "\N{THUMBS DOWN SIGN}"


class MomBurn(glados.Module):
    @glados.Module.rule(r"^.*(yo)?ur\s+(mom|mum|mother|momma|mama)\b.*$")
    async def on_message(self, message, match):
        try:
            await self.client.add_reaction(message, BURN_EMOJI)
            await self.client.add_reaction(message, DOWN_EMOJI)
        except:
            pass

    
