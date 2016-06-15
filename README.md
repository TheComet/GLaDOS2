# Discord Bot framework

This is a bot for [Discord](https://discordapp.com/) that provides you with a framework to easily extend functionality.

## Running

To run the bot, you need [Python](https://www.python.org/) and [discord.py](https://github.com/Rapptz/discord.py).

Running the bot for the first time will produce the `settings.json` file. You should edit this, then run the bot again.

## Settings

### Login

The email and password used to login to the account. It is recommended that you create a separate account for running bots. Alternatively, you can provide an OAuth2 token, in which case the e-mail and password are not required.

### Modules

It is possible to add a list of paths, in which the bot modules will be searched for. 

### Writing modules

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

