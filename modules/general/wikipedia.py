# coding=utf-8
# Copyright 2013 Elsie Powell - embolalia.com
# Licensed under the Eiffel Forum License 2.

import glados
import json
import re
import urllib.request

REDIRECT = re.compile(r'^REDIRECT (.*)')


class Wikipedia(glados.Module):
    def __init__(self):
        super(Wikipedia, self).__init__()
        self.__lang = 'en'

    def get_help_list(self):
        return [
            glados.Help('w', '<query>', 'Search wikipedia for a thing.')
        ]

    @glados.Module.commands('w', 'wiki', 'wik')
    def wikipedia(self, message, query):

        if query == '':
            await self.provide_help('w', message)
            return

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
    search_url = ('http://%s/w/api.php?format=json&action=query'
                  '&list=search&srlimit=%d&srprop=timestamp&srwhat=text'
                  '&srsearch=') % (server, num)
    search_url += query
    query = json.loads(urllib.request.urlopen(search_url).read().decode("utf-8"))
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
    snippet_url = ('https://' + server + '/w/api.php?format=json'
                   '&action=query&prop=extracts&exintro&explaintext'
                   '&exchars=300&redirects&titles=')
    snippet_url += query
    snippet = json.loads(urllib.request.urlopen(snippet_url).read().decode("utf-8"))
    snippet = snippet['query']['pages']

    # For some reason, the API gives the page *number* as the key, so we just
    # grab the first page number in the results.
    snippet = snippet[list(snippet.keys())[0]]

    return snippet['extract']


def say_snippet(client, message, server, query, show_url=True):
    page_name = query.replace('_', ' ')
    query = query.replace(' ', '_')
    snippet = mw_snippet(server, query)
    msg = '[WIKIPEDIA] {} | "{}"'.format(page_name, snippet)
    if show_url:
        msg = msg + ' | https://{}/wiki/{}'.format(server, query)
    await client.send_message(message.channel, msg)
