import glados
import requests
import discord
import re
import os
import urllib
import difflib
from bs4 import BeautifulSoup


LATEST_URI = "http://xkcd.com/info.0.json"
NUMBER_URI = "http://xkcd.com/{}/info.0.json"
ARCHIVE_URI = "http://xkcd.com/archive"


class XKCD(glados.Module):
    def __init__(self, server_instance, full_name):
        super(XKCD, self).__init__(server_instance, full_name)

        self.__tmp_dir = os.path.join(self.local_data_dir, "xkcd")
        if not os.path.exists(self.__tmp_dir):
            os.makedirs(self.__tmp_dir)

    @glados.Module.command("xkcd", "[query/number]", "Return the active comic or search for a comic. Query can also be the comic index")
    async def xkcd(self, message, query):
        match = re.match(r"^#?(\d+)$", query)

        # simplest case: Get latest comic
        if query == "":
            data = requests.get(LATEST_URI)
            if not data.ok:
                return await self.client.send_message(message.channel, f"Error: {LATEST_URI} returned {data.status_code}")
            return await self.process_json(message, data.json())
        elif match:
            number = int(match.group(1))
            # special case because xkcd likes to be funny ha ha
            if number == 404:
                return await self.client.send_message(message.channel, "404 -- Not found")
            data = requests.get(NUMBER_URI.format(number))
            if not data.ok:
               return await self.client.send_message(message.channel, f"Error: {NUMBER_URI} returned {data.status_code}")
            return await self.process_json(message, data.json())
        else:
            return await self.search_archives(message, query)

    async def process_json(self, message, data):
        img_filename = data["img"].split("/")[-1]
        img_filename = os.path.join(self.__tmp_dir, img_filename)
        if not os.path.isfile(img_filename):
            urllib.request.urlretrieve(data["img"], img_filename)
        
        try:
            await self.client.send_file(message.channel, img_filename)
        except discord.errors.Forbidden:
            # hope discord embeds images...
            await self.client.send_message(message.channel, data["img"])
        await self.client.send_message(message.channel, f"<http://xkcd.com/{data['num']}> [{data['title']}]")

    async def search_archives(self, message, query):
        archives = await self.fetch_archives(message)
        closest_match = difflib.get_close_matches(query, archives, 1)
        if len(closest_match) == 0:
            return await self.client.send_message(message.channel, f"Couldn't find any entries matching `{query}`")
        index = int(archives[closest_match[0]])
        data = requests.get(NUMBER_URI.format(index))
        if not data.ok:
            return await self.client.send_message(message.channel, f"Error: {NUMBER_URI} returned {data.status_code}")
        return await self.process_json(message, data.json())
    
    async def fetch_archives(self, message):
        data = requests.get(ARCHIVE_URI)
        if not data.ok:
            return await self.client.send_message(message.channel, f"Error: {ARCHIVE_URI} returned {data.status_code}")
        soup = BeautifulSoup(data.content.decode("utf-8"), "lxml")
        links = soup.find_all("a", href=re.compile(r"/\d+/"))
        return {link.get_text(): link.get_attribute_list("href")[0].strip("/") for link in links}

