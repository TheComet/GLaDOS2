# coding=utf-8
# Copyright 2010, Michael Yanovich (yanovich.net), and Morgan Goose
# Copyright 2012, Lior Ramati
# Copyright 2013, Elsie Powell (embolalia.com)
# Licensed under the Eiffel Forum License 2.
import glados
import discord
import urllib.request
import random
import re
import requests
import os


ignored_sites = [
    # For google searching
    'almamater.xkcd.com',
    'blog.xkcd.com',
    'blag.xkcd.com',
    'forums.xkcd.com',
    'fora.xkcd.com',
    'forums3.xkcd.com',
    'store.xkcd.com',
    'wiki.xkcd.com',
    'what-if.xkcd.com',
]
sites_query = ' site:xkcd.com -site:' + ' -site:'.join(ignored_sites)


def get_info(number=None):
    if number:
        url = 'http://xkcd.com/{}/info.0.json'.format(number)
    else:
        url = 'http://xkcd.com/info.0.json'
    data = requests.get(url).json()
    data['url'] = 'http://xkcd.com/' + str(data['num'])
    return data


r_duck = re.compile(r'nofollow" class="[^"]+" href="(?!https?:\/\/r\.search\.yahoo)(.*?)">')


def duck_search(query):
    query = query.replace('!', '')
    uri = 'http://duckduckgo.com/html/?q=%s&kl=uk-en' % query
    bytes = urllib.request.urlopen(uri).read().decode('utf-8')
    if 'web-result' in bytes:  # filter out the adds on top of the page
        bytes = bytes.split('web-result')[1]
    m = r_duck.search(bytes)
    if m:
        return m.group(1)


def google(query):
    url = duck_search(query + sites_query)
    if not url:
        return None
    match = re.match('(?:https?://)?xkcd.com/(\d+)/?', url)
    if match:
        return match.group(1)


class XKCD(glados.Module):
    def __init__(self):
        super(XKCD, self).__init__()
        self.__tmp_dir = None

    def setup(self):
        self.__tmp_dir = os.path.join(self.settings['modules']['config path'], 'xkcd')
        if not os.path.exists(self.__tmp_dir):
            os.makedirs(self.__tmp_dir)

    def get_help_list(self):
        return [
            glados.Help('xkcd', '[query]', 'Either return random comic or search for a comic. '
                                           'Query can also be a number')
        ]

    @glados.Module.commands('xkcd')
    def xkcd(self, message, query):
        """
        .xkcd - Finds an xkcd comic strip. Takes one of 3 inputs:
        If no input is provided it will return a random comic
        If numeric input is provided it will return that comic, or the nth-latest
        comic if the number is non-positive
        If non-numeric input is provided it will return the first google result for those keywords on the xkcd.com site
        """
        # get latest comic for rand function and numeric input
        latest = get_info()
        max_int = latest['num']

        # if no input is given (pre - lior's edits code)
        if query == '':  # get rand comic
            random.seed()
            requested = get_info(random.randint(1, max_int + 1))
        else:
            query = query.strip()

            numbered = re.match(r"^(#|\+|-)?(\d+)$", query)
            if numbered:
                query = int(numbered.group(2))
                if numbered.group(1) == "-":
                    query = -query
                if query > max_int:
                    yield from self.client.send_message(message.channel, ("Sorry, comic #{} hasn't been posted yet. "
                                                                     "The last comic was #{}").format(query, max_int))
                    return
                elif query <= -max_int:
                    yield from self.client.send_message(message.channel, ("Sorry, but there were only {} comics "
                                                                     "released yet so far").format(max_int))
                    return
                elif abs(query) == 0:
                    requested = latest
                elif query == 404 or max_int + query == 404:
                    yield from self.client.send_message(message.channel, "404 - Not Found")  # don't error on that one
                    return
                elif query > 0:
                    requested = get_info(query)
                else:
                    # Negative: go back that many from current
                    requested = get_info(max_int + query)
            else:
                # Non-number: google.
                if query.lower() == "latest" or query.lower() == "newest":
                    requested = latest
                else:
                    number = google(query)
                    if not number:
                        yield from self.client.send_message(message.channel, 'Could not find any comics for that query.')
                        return
                    requested = get_info(number)

        img_file = requested['img'].split('/')[-1]
        img_file = os.path.join(self.__tmp_dir, img_file)
        if not os.path.isfile(img_file):
            urllib.request.urlretrieve(requested['img'], img_file)

        response = '{} [{}]'.format(requested['url'], requested['title'])
        try:
            yield from self.client.send_file(message.channel, img_file)
        except discord.errors.Forbidden:
            pass
        yield from self.client.send_message(message.channel, response)
