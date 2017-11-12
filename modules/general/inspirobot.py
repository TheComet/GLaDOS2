from glados import Module
import requests
import asyncio

URI = 'http://inspirobot.me/api?generate=true'


class InspiroBot(Module):
    @Module.command('inspire')
    async def inspire(self, message, content):
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, requests.get, URI)
        
