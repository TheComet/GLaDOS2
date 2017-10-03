from glados import Module
from urllib.parse import urlencode, urljoin
from urllib.request import urlopen
from bs4 import BeautifulSoup

KYM_URL    = 'http://knowyourmeme.com'
KYM_SEARCH = 'http://knowyourmeme.com/search?'


class KYMException(Exception):
    def __init__(self, message):
        super(KYMException, self).__init__(message)


def get_meme_info(url):
    try:
        html = urlopen(url).read().decode('utf-8')
        soup = BeautifulSoup(html, 'lxml')
        about = accumulate_to(soup.find('h2', {'id': 'about'}), ['h2', 'h3', 'h4'])
        origin = accumulate_to(soup.find('h2', {'id': 'origin'}), ['h2', 'h3', 'h4'])
        return about, origin
    except Exception as e:
        raise KYMException(str(e))


def accumulate_to(navstr, strings):
    if navstr is None:
        return 'Unknown'
    ret = list()
    for x in navstr.next_siblings:
        try:
            if x.name in strings:
                break
        except AttributeError:
            pass

        try:
            ret.append(x.text)
        except:
            pass

    return '\n'.join(ret)


class KnowYourMeme(Module):

    @Module.command('kym', '<term>', 'Searches knowyourmeme.com for dank memes')
    @Module.command('meme', '', '')
    async def search(self, message, content):
        try:
            url = self.search_meme(content)
            about, origin = get_meme_info(url)
        except KYMException as e:
            return await self.client.send_message(message.channel, 'Error: {}'.format(e))

        if len(about) + len(origin) > 5000:
            return await self.client.send_message(message.channel, 'KnowYourMeme returned more than 5k characters...')

        for msg in self.pack_into_messages('**About**\n{}\n\n**Origin**\n{}'.format(about, origin).split(' '), delimiter=' '):
            await self.client.send_message(message.channel, msg)

    @staticmethod
    def search_meme(query):
        url = KYM_SEARCH + urlencode(dict(
            context='entries',
            sort='relevance',
            q=query
        ))
        html = urlopen(url).read().decode('utf-8')
        soup = BeautifulSoup(html, 'lxml')
        entries = soup.find('div', {'id': 'entries'})

        try:
            error = entries.find('h3', {'class': 'closed'}).text
            if error:
                raise KYMException(error)
        except AttributeError:
            pass

        a = entries.find('td', {'class': True}).h2.a
        url = urljoin(KYM_URL, a['href'])
        return url

