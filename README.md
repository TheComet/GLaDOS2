# Discord Bot Framework

This is a bot for [Discord](https://discordapp.com/) that provides you with a very easy way to write your own bot commands.

How easy? Check it out!

Here's a module that responds to people who say "hello" in chat:

```python
import random
from glados import Module

responses = [
    'Hello, {}!',
    'Hi, {}!',
    'What\'s up, {}?',
    'Welcome back {}!'
]

class RespondHello(Module):
    @Module.rule('^(?i)(hello|hey|hi|sup).*$')
    def respond_to_hello(self, message, match):
        yield from self.client.send_message(message.channel,
                random.choice(responses).format(message.author.name))
```

Here's a module that generates a random fact whenever someone types ```.fact``` into chat:

```python
import urllib.request
from glados import Module
from bs4 import BeautifulSoup

class Fact(glados.Module):
    @Module.command('fact', '', 'Look up a random fact')
    async def fact(self, message, args):
        response = urllib.request.urlopen('http://randomfactgenerator.net/').read().decode('utf-8')
        soup = BeautifulSoup(response, 'lxml')
        fact_div = soup.find('div', {'id': 'z'})
        if len(fact_div.contents) == 0:
            await self.client.send_message(message.channel, 'Something broke.')
        else:
            await self.client.send_message(message.channel, fact_div.contents[0])
```

## Installing and Running

To run the bot, you need [Python3.5](https://www.python.org/) or later (we're using the new async keywords, which were introduced in 3.5).

I recommend setting up a virtual environment. The complete process looks as follows:

```sh
$ git clone git://github.com/TheComet/GLaDOS2.git
$ cd GLaDOS2
$ virtualenv -p /usr/bin/python3.6 env
$ source env/bin/activate
$ pip install -r requirements.txt
$ python glados.py
```

Running the bot for the first time will produce the `settings.json` file. You should edit this, then run the bot again.

Refer to the wiki for more information on all of the things you can configure in ```settings.json```.

## Dependencies

The bot itself only depends on ```asyncio```. However, there are a lot of modules that pull in a lot of additional dependencies, some of which are almost impossible to install if you are on Windows (scipy, for example). There is currently no easy way to figure out which modules require which dependencies. The file `requirements.txt` will pull in ALL dependencies so you can load ALL modules.

## Experimental Dependencies

Here are a list of experimental dependencies, which are not loaded by default

### Picarto

The picarto module requires google's protobuf to be built from source.

```
$ git clone https://github.com/google/protobuf
$ cd protobuf
$ ./autogen.sh
$ ./configure --prefix=some/place
$ make
$ make check
$ make install
```

Additionally, the python bindings need to be built and installed
```
$ (source the virtualenv)
$ cd python/
$ python setup.py install
$ cp -r build/lib/google ../../env/lib/site-packages/
``` 

## Contributors

Avalander
 + findquote refactor

fastcall22
 + Fixed punishment system

slicer4ever [](https://github.com/slicer4ever)
 + Pony emotes module

