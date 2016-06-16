import glados
import re
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup


class Youtube(glados.Module):

    @glados.Module.commands('youtube', 'yt')
    def random_youtube(self, client, message, content):
        # no arguments
        if content == '':
            yield from client.send_message(message.channel, '.youtube <comment/video> selects a random comment/video\n'
                                                            '.youtube <search phrase> searches for a video on youtube.')
            return

        if content == 'comment':
            yield from client.send_message(message.channel, self.get_random_comment())
            return
        if content == 'video':
            yield from client.send_message(message.channel, self.get_random_video())
            return
        yield from client.send_message(message.channel, self.search_for_video(content))

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
        vid = soup.find(attrs={'class':'yt-uix-tile-link'})
        if vid:
            return 'https://www.youtube.com' + vid['href']
        else:
            return 'None found'
