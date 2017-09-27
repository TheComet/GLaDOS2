# coding=utf-8
# Copyright 2013 Elsie Powell - embolalia.com
# Licensed under the Eiffel Forum License 2.

import glados
import json
import re
from urllib.request import urlopen
from urllib.parse import urlencode

REDIRECT = re.compile(r'^REDIRECT (.*)')


class Wikipedia(glados.Module):
    def __init__(self):
        super(Wikipedia, self).__init__()
        self.__lang = 'en'

    @glados.Module.command('wiki', '<query>', 'Search wikipedia for a thing.')
    @glados.Module.command('w', '', '')
    @glados.Module.command('wik', '', '')
    async def wikipedia(self, message, query):
        args = re.search(r'^-([a-z]{2,12})\s(.*)', query)
        if args is not None:
            lang = args.group(1)
            query = args.group(2)

        if not query:
            await self.client.send_message(message.channel, 'What do you want me to look up?')
            return

        server = self.__lang + '.wikipedia.org'
        query = mw_search(server, query, 1)
        if not query:
            await self.client.send_message(message.channel, 'I can\'t find any results for that.')
            return
        else:
            query = query[0]
        await say_snippet(self.client, message, server, query)


def mw_search(server, query, num):
    """
    Searches the specified MediaWiki server for the given query, and returns
    the specified number of results.
    """
    search_url = 'http://{}/w/api.php?'.format(server) + urlencode(dict(
        format='json',
        action='query',
        list='search',
        srlimit=num,
        srprop='timestamp',
        srwhat='text',
        srsearch=query
    ))
    query = json.loads(urlopen(search_url).read().decode("utf-8"))
    if 'query' in query:
        query = query['query']['search']
        return [r['title'] for r in query]
    else:
        return None


def mw_snippet(server, query):
    """
    Retrives a snippet of the specified length from the given page on the given
    server.
    """
    snippet_url = 'https://{}/w/api.php?exintro&explaintext&redirects&'.format(server) + urlencode(dict(
        format='json',
        action='query',
        prop='extracts',
        exchars=300,
        titles=query
    ))
    snippet = json.loads(urlopen(snippet_url).read().decode("utf-8"))
    snippet = snippet['query']['pages']

    # For some reason, the API gives the page *number* as the key, so we just
    # grab the first page number in the results.
    snippet = snippet[list(snippet.keys())[0]]

    return snippet['extract']


async def say_snippet(client, message, server, query, show_url=True):
    page_name = query.replace('_', ' ')
    query = query.replace(' ', '_')
    snippet = mw_snippet(server, query)
    msg = '[WIKIPEDIA] {} | "{}"'.format(page_name, snippet)
    if show_url:
        msg = msg + ' | https://{}/wiki/{}'.format(server, query)
    await client.send_message(message.channel, msg)
