import requests
import re
from glados import Module
from bs4 import BeautifulSoup
from urllib.parse import urlencode


URI = "https://www.freebsd.org/cgi/man.cgi"

def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

class Man(Module):
    @Module.command('man', '<query>', 'Look up something in the BSD reference manual. Example: strtok, or strtok(3)')
    async def do_man(self, message, args):
        # See if user specified some section
        section = 0  # Means "all sections" on the bsd website
        match = re.compile("^.*\((\d)\).*$").match(args)
        if match:
            section = int(match.group(1))
            args = split("(")[0]
        params={"query": args, "sektion": section}
        response = requests.get(URI, params=params, timeout=10)
        if not response.status_code == 200:
            return await self.client.send_message(message.channel, "freebsd.org returned status {}".format(response.status_code))
        soup = BeautifulSoup(response.text, "lxml")
        if soup.body.findAll(text=re.compile("Sorry, no data found for")):
            return await self.client.send_message(message.channel, "Sorry, no data found for `{}`. Maybe try searching on the website?\nhttps://www.freebsd.org/cgi/man.cgi".format(args))

        synopsis = u""
        s_tag = soup.find("a", {"name": "SYNOPSIS"})
        for tag in s_tag.next_siblings:
            if tag.name == "a":
                break
            synopsis += str(tag)
        msg = "```\n" + "\n".join([cleanhtml(x) for x in synopsis.splitlines()[1:]]) + "\n```"
        msg += URI + "?" + urlencode(params)

        await self.client.send_message(message.channel, msg)

