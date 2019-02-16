import random
import asyncio
import pickle
import json
from urllib.parse import urlparse, parse_qs, urlencode
from glados import Module, Permissions
from os import path, makedirs


DEFAULT_CONFIG = {
    "text channel": None,
    "voice channel": None,
    "queue": list()
}


def ensure_path_exists(dir):
    if not path.exists(dir):
        makedirs(dir)
    return dir


def load_json_if_exists(filename, default):
    if path.isfile(filename):
        return json.loads(open(filename, "rb").read().decode("utf-8"))
    return default


class MusicPlayer(Module):
    def __init__(self, server_instance, full_name):
        super(MusicPlayer, self).__init__(server_instance, full_name)

        self.voice_channel = None
        self.is_playing = False
        self.player = None
        self.ffmpeg_ss = 0

        self.config_dir = ensure_path_exists(path.join(self.local_data_dir, 'musicplayer'))
        self.cache_dir = ensure_path_exists(path.join(self.config_dir, "cache"))
        self.config = load_json_if_exists(path.join(self.config_dir, "config.json"), DEFAULT_CONFIG)

        self.actions = {
            "pause": (self.action_pause, "pause track"),
            "resume": (self.action_resume, "resume track"),
            "skip": (self.action_skip, "skip track"),
            "shuffle": (self.action_shuffle, "shuffle playlist"),
            "jump": (self.action_jump, "#min from start"),
            "list": (self.action_list, "list queued urls, optional preview"),
            "cockblock": (self.action_cockblock, "Play the last song added"),
            "configure": (self.action_configure, "set up music bot"),
            "help": (self.action_help, "print this help"),
        }

        asyncio.ensure_future(self.player_task())

    def save_config(self):
        open(path.join(self.config_dir, "config.json"), "wb").write(json.dumps(self.config).encode("utf-8"))

    async def action_skip(self, message):
        if self.player:
            self.player.stop()
        return ()

    async def action_cockblock(self, message):
        if len(self.config["queue"]) > 1:
            self.config["queue"].insert(1, self.config["queue"][-1])
            self.config["queue"].pop(-1)
            self.save_config()
            if self.player:
                self.player.stop()
            await self.client.send_message(message.channel, "cockblocked")
        return ()

    async def action_pause(self, message):
        if self.player:
            self.player.pause()
        return ()

    async def action_resume(self, message):
        if self.player:
            self.player.resume()
        return ()

    async def action_jump(self, message):
        if len(self.config["queue"]) > 0 and self.player:
            self.ffmpeg_ss = float(message.content.split(" ")[1])*60
            await self.client.send_message(message.channel, "jumping to minute {}".format(self.ffmpeg_ss/60))
            self.config["queue"].insert(0, self.config["queue"][0])
            self.save_config()
            self.player.stop()
        return ()

    async def action_shuffle(self, message):
        if len(self.config["queue"]) > 1:
            first, *self.config["queue"] = self.config["queue"]
            random.shuffle(self.config["queue"])
            self.config["queue"].insert(0, first)
            self.save_config()
            await self.client.send_message(message.channel, "Playlist was shuffled.")
        return ()

    async def action_list(self, message):
        if len(self.config["queue"]) > 0:
            for msg in self.pack_into_messages([f"<{x}>" for x in self.config["queue"]]):
                await self.client.send_message(message.channel, msg)
        else:
            await self.client.send_message(message.channel, "No music in queue")

    async def action_configure(self, message):
        if not self.require_admin(message.author):
            return await self.client.send_message(message.channel, "Only admins can configure the music bot")

        async def disconnect_vc():
            if self.voice_channel:
                await self.voice_channel.disconnect()
                self.voice_channel = None

        try:
            if len(message.content.split(" ")) < 3:
                await disconnect_vc()
                self.config["voice channel"] = None
                self.config["text channel"] = None
                self.save_config()
                return await self.client.send_message(message.channel, "Removed bot from music channel")
            voice_channel_id = message.content.split(" ")[2]
        except:
            return await self.client.send_message(message.channel, f"Voice channel ID not found.")

        self.config["voice channel"] = str(voice_channel_id)
        self.config["text channel"] = str(message.channel.id)
        self.save_config()

        if self.player:
            self.player.stop()
        await disconnect_vc()

        try:
            await self.try_joining_voice_channel()
            await self.client.send_message(message.channel, "Successfully joined voice channel")
        except TimeoutError:
            await disconnect_vc()
            await self.client.send_message(message.channel, "Failed to join voice channel: Timed out")
        except Exception as e:
            await disconnect_vc()
            await self.client.send_message(message.channel, f"Failed to join voice channel: {e}")

    async def action_help(self, message):
        await self.client.send_message(message.channel,
                                       "```Command list:\n" +
                                       "\n".join(
                                           [k.ljust(4+max(map(len, self.actions.keys()))) +
                                            self.actions[k][1]
                                            for k in self.actions.keys()])
                                       + "```")

    async def try_joining_voice_channel(self):
        vc = self.client.get_channel(self.config["voice channel"])
        tc = self.client.get_channel(self.config["text channel"])
        self.voice_channel = await self.client.join_voice_channel(vc)

    @Module.command("music", "", "Access to music queue controls")
    @Module.command("m", "", "Access to music queue controls")
    async def on_music(self, message, content):
        if "configure" not in content:
            tc = self.client.get_channel(self.config["text channel"])
            if tc is None:
                return await self.client.send_message(message.channel, "The music text channel wasn't found or wasn't configured. Please type .music configure <voice channel name> in a dedicated text channel. The text channel will become the only channel that accepts music commands.")
            if not tc == message.channel:
                return await self.client.send_message(message.channel, f"The {self.command_prefix}music command is only available in {tc.mention}")

        try:
            command = content.split(" ", 2)[0]
            await self.actions[command][0](message)
        except:
            await self.actions["help"][0](message)

    @Permissions.spamalot
    @Module.rule(r"^.*$")
    async def on_message(self, message, match):
        tc = self.client.get_channel(self.config["text channel"])
        if not tc == message.channel:
            return ()

        for msg_cont in message.content.split('\n'):
            if "youtube.com" in msg_cont:
                try:
                    url = "https://www.youtube.com/watch/?" + urlencode(dict(v=parse_qs(urlparse(msg_cont).query)['v'][0]))
                except:
                    continue
            elif "youtu.be" in msg_cont:
                try:
                    code = msg_cont.split("/")[-1]
                    url = "https://www.youtube.com/watch/?" + urlencode(dict(v=code))
                except:
                    continue
            else:
                continue

            self.config["queue"].append(url)
            self.save_config()
            await self.client.send_message(message.channel, "Added to queue (position {})".format(len(self.config["queue"])-1))

    async def player_task(self):
        try:
            await self.try_joining_voice_channel()
        except Exception as e:
            pass
        while True:
            await asyncio.sleep(1)
            if self.voice_channel is None:
                continue
            if len(self.config["queue"]) == 0:
                continue

            if self.player:
                if not self.player.is_done():
                    continue
                if len(self.config["queue"]) > 0:
                    self.config["queue"].pop(0)
                    self.save_config()
                if len(self.config["queue"]) == 0:
                    await self.client.send_message(self.client.get_channel(self.config["text channel"]), "No more songs in queue!")
                    self.player = None
                    continue

            next_url = self.config["queue"][0]

            self.player = await self.voice_channel.create_ytdl_player(next_url, before_options="-ss {}".format(self.ffmpeg_ss))
            if self.ffmpeg_ss < self.player.duration:
                self.ffmpeg_ss = 0
                self.player.start()
                await self.client.send_message(self.client.get_channel(self.config['text channel']),
                                               "Playing {} ({})\n{} left in queue".format(
                                                   self.player.title,
                                                   self.player.duration,
                                                   len(self.config["queue"]) - 1))
            else:
                await self.client.send_message(self.client.get_channel(self.config['text channel']),
                                               "Jumped to {}s track ended at {}s".format(
                                                   self.ffmpeg_ss,
                                                   self.player.duration))
                self.ffmpeg_ss = 0
                self.player.stop()
