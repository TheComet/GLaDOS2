import glados
import re
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup


class Youtube(glados.Module):
    @glados.Module.command('youtube', '<search term|comment|video>', 'Look for a youtube video and return its URL, Look'
                           ' for a random youtube command and post it, or look for a random youtube video')
    @glados.Module.command('yt', '', '')
    async def random_youtube(self, message, content):
        # no arguments
        if content == '':
            await self.provide_help('youtube', message)
            return

        if content == 'comment':
            await self.client.send_message(message.channel, self.get_random_comment())
            return
        if content == 'video':
            await self.client.send_message(message.channel, self.get_random_video())
            return
        await self.client.send_message(message.channel, self.search_for_video(content))

    @staticmethod
    def get_random_comment():
        page = urllib.request.urlopen('http://www.randomyoutubecomment.com/').read().decode('utf-8')
        re_mark = re.compile('text-decoration: none; color: black;">(.*)</span>')
        comment = re_mark.findall(page)
        re_mark = re.compile('<p style="font-style:italic; font-size: 24pt;">(.*)</p>')
        author = re_mark.findall(page)
        if not author: author = ['(unknown)']
        if comment:
            return '{0}\n --{1}'.format(comment[0], author[0])
        else:
            return 'Error: No results :('

    @staticmethod
    def get_random_video():
        page = urllib.request.urlopen('http://randomyoutube.net/watch').read().decode('utf-8')
        re_mark = re.compile('<a href="http://www\.youtube\.com/watch\?v=(.*)" target="_blank">.*</p>')
        results = re_mark.findall(page)
        if results:
            return 'www.youtube.com/watch?v={}'.format(results[0])
        else:
            return 'Error: No results :('

    @staticmethod
    def search_for_video(text_to_search):
        query = urllib.parse.quote(text_to_search)
        url = 'https://www.youtube.com/results?search_query={}'.format(query)
        html = urllib.request.urlopen(url).read().decode('utf-8')
        soup = BeautifulSoup(html, 'lxml')
        for vid in soup.findAll(attrs={'class': 'yt-uix-tile-link'}):
            # See issue #5 - remove advertisement links
            href = vid['href']
            if "https://googleads.g.doubleclick.net" in href:
                continue
            return 'https://www.youtube.com' + href
        else:
            return 'None found'
