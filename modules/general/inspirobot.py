import requests
import asyncio
from glados import Module
from os.path import join, isdir
from os import mkdir

URI = 'http://inspirobot.me/api?generate=true'


def download_file(url, file_name):
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(file_name, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)


class InspiroBot(Module):

    def __init__(self, server_instance, full_name):
        super(InspiroBot, self).__init__(server_instance, full_name)

        # Create cache directory, where the inspire images are downloaded to
        self.__cache_dir = join(self.global_data_dir, 'inspirobot')
        if not isdir(self.__cache_dir):
            mkdir(self.__cache_dir)

    @Module.command('inspire', '', 'Generate an inspiring quote using inspirobot.me')
    async def inspire(self, message, content):
        # Request image URL
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, requests.get, URI)

        # Download image file into cache
        url = response.text
        file_name = join(self.__cache_dir, url.split('/')[-1])
        await loop.run_in_executor(None, download_file, url, file_name)

        await self.client.send_file(message.channel, file_name)
