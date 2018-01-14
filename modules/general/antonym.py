from urllib.parse import quote
from urllib.request import urlopen
from glados import Module
from bs4 import BeautifulSoup

URI = "http://www.antonymswords.com/"
MAX_RESULTS = 20

class Antonym(Module):
    @Module.command("antonym", "<word>", "Look up the antonym (opposite) of a word.")
    def lookup_antonym(self, message, content):
        first_word = content.split(num=2)[0]
        url = URI + quote(first_word)
        response = urlopen(url).read().decode("utf-8")
        soup = BeautifulSoup(response, 'lxml')
        results = soup.find("div", {"class": "boxResult"}).find_all("a")
        if results is None:
            return await self.client.send_message(message.channel, "No results found for `{}`".format(first_word))
        results_str = ", ".join([a.string for a in results[MAX_RESULTS:]])
        if len(results) > MAX_RESULTS:
            results_str += ", and more..."

        await self.client.send_message(message.channel, "Antonyms for \"{}\": ```{}```".format(first_word, results_str))
