# Discord Bot framework

This is a bot for [Discord](https://discordapp.com/) that provides you with a framework to easily extend functionality.

## Running

To run the bot, you need [Python](https://www.python.org/) and [discord.py](https://github.com/Rapptz/discord.py).

Running the bot for the first time will produce the `settings.json` file. You should edit this, then run the bot again.

## Dependencies

From pip:
 + discord.py
 + python-dateutil
 + requests
 + pyenchant
 + beautifulsoup4
 + PySocks
 + lxml
 + nltk
 + matplotlib
 + jsonpickle

## Settings

### Login

The email and password used to login to the account. It is recommended that you create a separate account for running bots. Alternatively, you can provide an OAuth2 token, in which case the e-mail and password are not required.

### Modules

It is possible to add a list of paths, in which the bot modules will be searched for. 

### Writing modules

You can use this as a framework for your module.
```python
import glados

class MyModule(glados.Module):
    def __init__(self, settings):
        pass  # you can retrieve data from the settings.json file using settings

    def get_help_list(self):
        return [
            glados.Help('hello', '<name>', 'Says hello to the specified name')
        ]

    @glados.Module.commands('hello')
    def respond_to_hello(self, client, message, arg):
        
        # User forgot to supply the command with an argument
        if arg == '':
            yield from self.provide_help('hello', client, message)
            return

        yield from client.send_message(message.channel, 'Hello, {}!'.format(arg))

    @glados.Module.rules('^.*(hello).*$')
    @glados.Module.rules('^.*(hi).*$')
    def someone_said_hello_or_hi(self, client, message, match)
        yield from client.send_message(message.channel, 'Hello, {}!'.format(message.author.name))
```


There are two ways to register yourself to messages being received. Either you can provide a command to react to, for example:
```python
import glados

class MyModule(glados.Module):
    
    @glados.Module.command('test', 'foo')
    def message_received(self, client, message, content):
        yield from client.send_message(message.channel, "{0} wrote {1}".format(message.author.name, content))
```
In this example, sending ```.test hello``` or ```.foo hello``` will have the bot respond with "*<your name> wrote hello*".

Or you can use a regex to match incoming messages. If any messages matches the regex, then your method will be invoked. Examples:
```python
import glados

class MyModule(glados.Module):

    @glados.Module.rules('^.*(I like books).*$')
    def on_books_liked(self, client, message, match):
        yield from client.send_message(message.channel, "{} likes books! Burn him!".format(message.author.name))
```

You can additionally provide a constructor to receive a dictionary containing the settings from ```settings.json```:
```python
import glados

class MyModule(glados.Module):

    def __init__(self, settings):
        super(MyModule, self).__init__(settings)

        path_to_save_things = settings['modules']['config path']
```

In this example we retrieve the path to a folder in which the bot is allowed to write whatever files it needs to write. Perhaps you want to save information between sessions? Write things and read things from there.

