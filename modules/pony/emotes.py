import glados
import os
from os import listdir
from os.path import dirname, realpath, isfile, join
import json
import difflib
import asyncio
import APNGLib
import time
import urllib.request
from PIL import Image


class Eemote:
    def __init__(self, name, image_path, x_offset, y_offset, x_size, y_size, flip, is_nsfw):
        self.name = name
        self.image_path = image_path
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.x_size = x_size
        self.y_size = y_size
        self.flip = flip
        self.is_nsfw = is_nsfw


class Emotes(glados.Module):
    def __init__(self):
        super(Emotes, self).__init__()
        this_dir = dirname(realpath(__file__))
        self.emotes_path = join(this_dir, 'emotesdb')
        self.infodb_path = join(this_dir, 'emote_info_db')
        self.tagdb_path = join(this_dir, 'emote_tag_db')
        self.tag_list = {}
        self.emote_list = {}
        self.raw_emote_list = []
        self.is_running = False

    def setup_global(self):
        self.is_running = True
        asyncio.ensure_future(self.build_emote_db())
        return

    def setup_memory(self):
        self.memory['blacklist'] = {}
        self.memory['blacklist']['allow_nsfw'] = False
        self.memory['config_path'] = join(self.data_dir, "emotes.json")
        self.load_blacklist()

    def load_blacklist(self):
        if isfile(self.memory['config_path']):
            self.memory['blacklist'] = json.loads(open(self.memory['config_path']).read())

    def save_blacklist(self):
        try:
            os.makedirs(os.path.dirname(self.memory['config_path']))
        except Exception as E:
            if "File exists" not in str(E):
                print(E)
                return
                # do nothing as the dirs probably already exist
        f = open(self.memory['config_path'], "w")
        if f:
            f.write(json.dumps(self.memory['blacklist']))

    def save_target_image(self, source, name, x_offset, y_offset, x_size, y_size, flip, convert):
        m_img = Image.open(source)
        m_img = m_img.crop((x_offset, y_offset, x_offset + x_size, y_offset + y_size))
        if flip is True:
            m_img = m_img.transpose(Image.FLIP_LEFT_RIGHT)
        if convert is True:
            m_img.load()
            alpha = m_img.split()[- 1]
            m_img = m_img.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)
            mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
            m_img.paste(255, mask)
            m_img.save(join(self.emotes_path, name) + ".png", transparency=255, optimize=True)
        else:
            m_img.save(join(self.emotes_path, name) + ".png", optimize=True)

    def build_emote(self, name, image_path, x_offset, y_offset, x_size, y_size, flip):
        # print("Emote: '" + name + "' Img: " + ImagePath + " o: " + str(xOffset) + " " + str(yOffset) + " s: " + str(xSize) + " " + str(ySize))
        name_base = name + ".tmp"
        frame_cnt = 1
        transform = APNGLib.TransformCrop | APNGLib.TransformNoGif1Frame
        if flip is True:
            transform |= APNGLib.TransformFlipHorizontal
        try:
            urllib.request.urlretrieve(image_path, name_base)
            frame_cnt = APNGLib.MakeGIF(name_base, join(self.emotes_path, name) + ".gif", transform, x_offset, y_offset,
                                        x_size, y_size)
            if frame_cnt == 1:
                # we tell the function the  not to save if there is only 1 frame, so we can save it as a png instead.
                self.save_target_image(name_base, name, x_offset, y_offset, x_size, y_size, flip, True)

        except Exception as e:
            if str(e) == "bad transparency mask":
                try:
                    # save as regular file instead.
                    self.save_target_image(name_base, name, x_offset, y_offset, x_size, y_size, flip, False)
                except Exception as e2:
                    print("Error2 processing emote: " + name)
                    print(e2)

            else:
                print("Error processing emote: " + name)
                print(e)

        for i in range(0, 3):  # retry a few times in case failure is due to the os hasn't given up a handle right away.
            try:
                os.remove(name_base)
                break
            except:
                time.sleep(1)

    async def build_emote_db(self):
        self.tag_list = {}
        self.emote_list = {}
        self.raw_emote_list = []
        files = [f for f in listdir(self.infodb_path) if isfile(join(self.infodb_path,f))]
        for f in files:
            subreddit = os.path.splitext(f)[0]
            jinfo_file = open(join(self.infodb_path,f))
            jtag_file = open(join(self.tagdb_path,f))
            jinfodata = json.loads(jinfo_file.read())
            jtagdata = json.loads(jtag_file.read())
            jinfo_file.close()
            jtag_file.close()
            self.tag_list[subreddit] = {}
            for key, items in jinfodata.items():
                
                name = key[1:].replace('/', '').replace('\\', '').replace('.', '')
                emote = items.get("Emotes")
                if not emote: continue
                emote = emote.get("")
                if not emote: continue
                image_path = emote.get("Image")
                offset = emote.get("Offset")
                size = emote.get("Size")
                is_nsfw = False
                flip = False
                x_offset = 0
                y_offset = 0
                x_size = 0
                y_size = 0
                css_transform = None
                if (emote.get("CSS")): css_transform = emote["CSS"].get("transform")
                if not image_path:
                    continue
                if offset:
                    x_offset = - offset[0]
                    y_offset = - offset[1]
                if size:
                    x_size = size[0]
                    y_size = size[1]
                if css_transform:
                    flip = True  # this is real dumb right now, but later i hope to actually parse and see if there is any interesting transform affects on emotes, but for now xScale seems to be the most common.
                self.tag_list[subreddit][name] = ""
                tags = jtagdata.get(key)
                if tags:
                    for tag in tags:
                        if not self.tag_list.get(tag):
                            self.tag_list[tag] = {}
                        self.tag_list[tag][name] = ""
                        if tag == "+nsfw":
                            is_nsfw = True
                if not self.emote_list.get(name):
                    self.emote_list[name] = Eemote(name, "https://" + image_path.split('//')[1], x_offset, y_offset,
                                                   x_size, y_size, flip, is_nsfw)
                    self.raw_emote_list.append(name)
                await asyncio.sleep(0)
        self.is_running = False
        print("Finished building emote db.")

    def spellcheck_emote_name(self, emote):
        r = difflib.get_close_matches(emote, self.raw_emote_list, 1, 0.2)
        if len(r) > 0:
            return r[0]
        return ""

    @staticmethod
    def __concat_into_valid_message(list_of_strings):
        ret = list()
        temp = list()
        l = 0
        max_length = 1000

        if len(list_of_strings) == 0:
            return ret

        for s in list_of_strings:
            l += len(s)
            if l >= max_length:
                ret.append('\n'.join(temp))
                l = len(s)
                temp = list()
            temp.append(s)
        ret.append('\n'.join(temp))
        return ret

    def find_emote_path(self, emotename):
        # we use replace to strip any symbols that'd allow file naviagation.
        path = join(self.emotes_path,emotename.replace('/', '').replace('\\', '').replace('.', ''))
        if isfile(path + ".png"):
            return path + ".png"
        if isfile(path + ".gif"):
            return path + ".gif"
        return ""

    @glados.Module.command('pony', '<emote>', 'Shows a pony with the specified emotion. Search '
                           'https://ponymotes.net/view/ to find an emote or use ponylist command (note: not all emotes '
                           'are supported)')
    async def request_pony_emote(self, message, content):

        if not content:
            await self.provide_help('pony', message)
            return

        emote = self.emote_list.get(content)
        if not emote:
            name = self.spellcheck_emote_name(content)
            if name:
                await self.client.send_message(message.channel, 'Unknown emoticon (did you mean: ' + name + "?)")
            else:
                await self.client.send_message(message.channel, 'Unknown emoticon.')
            return

        if self.memory['blacklist'].get(emote.name):
            await self.client.send_message(message.channel, 'Emote is blacklisted on this server.')
            return
        if not self.memory['blacklist']['allow_nsfw'] and emote.is_nsfw:
            await self.client.send_message(message.channel, 'Emote is tagged as nsfw.')
            return

        path = self.find_emote_path(emote.name)
        if not path:
            self.build_emote(emote.name, emote.image_path, emote.x_offset, emote.y_offset, emote.x_size, emote.y_size,
                             emote.flip)
            path = self.find_emote_path(emote.name)
        if not path:
            await self.client.send_message(message.channel, "Emote doesn't work")
            return
        await self.client.send_file(message.channel, path)

    @glados.Permissions.moderator
    @glados.Module.command('ponydel', '<emote>', 'blacklists the specified pony emote from the database for that '
                           'server, only a mod or admin can run this command.')
    async def delete_pony_emote(self, message, content):
        emote = self.emote_list.get(content)
        if not emote:
            name = self.spellcheck_emote_name(content)
            if name:
                await self.client.send_message(message.channel, 'Unknown emoticon (did you mean: ' + name + "?)")
            else:
                await self.client.send_message(message.channel, 'Unknown emoticon.')
            return

        self.memory['blacklist'][emote.name] = 1

        self.save_blacklist()
        await self.client.send_message(message.channel, 'blacklisted emote.')

    @glados.Permissions.moderator
    @glados.Module.command('ponyundel', '<emote>', 'unblacklists the specified pony emote from the database for that '
                           'server, only a mod or admin can run this command.')
    async def undelete_pony_emote(self, message, content):
        emote = self.emote_list.get(content)
        if not emote:
            name = self.spellcheck_emote_name(content)
            if name:
                await self.client.send_message(message.channel, 'Unknown emoticon (did you mean: ' + name + "?)")
            else:
                await self.client.send_message(message.channel, 'Unknown emoticon.')
            return

        self.memory['blacklist'].pop(emote.name, None)
        self.save_blacklist()
        await self.client.send_message(message.channel, 'removed emote from blacklist.')

    @glados.Permissions.moderator
    @glados.Module.command('ponynsfw', '<enable/disable>', 'sets a flag allowing or disallowing nsfw emotes on the '
                           'specefied server, only a mod or admin can run this command.')
    async def pony_nsfw(self, message, content):
        if content != "enable" and content != "disable":
            await self.provide_help('ponynsfw', message)
            return
        enable = content == "enable"
        self.memory['blacklist']['allow_nsfw'] = enable
        self.save_blacklist()
        if enable:
            await self.client.send_message(message.channel, 'nsfw emotes have been enabled.')
        else:
            await self.client.send_message(message.channel, 'nsfw emotes have been disabled.')
        return

    @glados.Module.command('ponylist', '[subreddit | tags]', "pm's you a list of emotes in the specefied subreddits, "
                           "or tagged emotes(i.e: +v) or sends a list of all subreddits if empty.")
    async def get_pony_list(self, message, content):
        response = []
        temp = ""
        per_line = 25
        i = 0
        if not content:
            response.append("List of available tags to search through:")
            for key, items in self.tag_list.items():
                if i == 0:
                    temp = key
                else:
                    temp += " | " + key
                i += 1
                if i == per_line:
                    response.append("``" + temp + "``")
                    i = 0
            if i != 0:
                response.append("``" + temp + "``")
        else:
            tags = content.split()
            response.append("List of emotes which have any of the tags: " + content + "")
            for t in tags:
                tag_list = self.tag_list.get(t)
                if not tag_list:
                    continue
                for key, items in tag_list.items():
                    if i == 0:
                        temp = key
                    else:
                        temp += " | " + key
                    i += 1
                    if i == per_line:
                        response.append("``" + temp + "``")
                        i = 0
            if i != 0:
                response.append("``" + temp + "``")
        response.append('')
        rlist = self.__concat_into_valid_message(response)
        for msg in rlist:
            await self.client.send_message(message.author, msg)
