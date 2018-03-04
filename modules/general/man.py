import requests
import re
import time
from glados import Module
from bs4 import BeautifulSoup
from urllib.parse import urlencode

URI = "https://www.freebsd.org/cgi/man.cgi"


def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    # fix missing bracket in #include statements
    cleantext = '\n'.join(["#include <" + x.split("#include ")[-1] if "#include" in x else x for x in cleantext.splitlines()])
    return cleantext


def unindent(text):
    return '\n'.join(x.strip() for x in text.splitlines())


def remove_shitty_formatting(text):
    text = re.sub("\n{3,}", "\n\n", text)
    return re.sub("[^\S\n]+", " ", text)


class Man(Module):
    @Module.command('man', '<query>', 'Look up something in the BSD reference manual. Example: strtok, or strtok(3)')
    async def do_man(self, message, args):
        # See if user specified some section
        section = 0  # Means "all sections" on the bsd website
        match = re.compile("^.*\((\d)\).*$").match(args)
        if match:
            section = int(match.group(1))
            args = args.split("(")[0]

        # Do query
        params = {"query": args, "sektion": section}
        response_time = time.time()
        response = requests.get(URI, params=params, timeout=10)
        response_time = time.time() - response_time
        if not response.status_code == 200:
            return await self.client.send_message(message.channel, "{} returned status {}".format(URI, response.status_code))
        soup = BeautifulSoup(response.text, "lxml")
        if soup.body.findAll(text=re.compile("Sorry, no data found for")):
            return await self.client.send_message(message.channel, "Sorry, no data found for `{}`. Make sure syntax is correct, for example: .man printf(3)\nMaybe try searching on the website? https://www.freebsd.org/cgi/man.cgi".format(args))

        # Try to extract the synopsis or name from the received html
        msg = u""
        s_tag = soup.find("a", {"name": "SYNOPSIS"})
        if s_tag is None:
            # no synopsis, try NAME instead?
            s_tag = soup.find("a", {"name": "NAME"})
        if s_tag:
            for tag in s_tag.next_siblings:
                if tag.name == "a":
                    break
                msg += str(tag)
            msg = "\n".join([cleanhtml(x) for x in msg.splitlines()[1:]])
            lang = ""
            if "#include" in msg:
                lang = "cpp"
            msg = "```" + lang + "\n" + msg + "\n```"
            msg = unindent(msg)
            msg = remove_shitty_formatting(msg)
        msg += URI + "?" + urlencode(params) + " (responded in {:.1f}s".format(response_time) + ")"

        await self.client.send_message(message.channel, msg)
