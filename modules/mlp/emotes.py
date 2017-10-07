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
    def __init__(self, server_instance, full_name):
        super(Emotes, self).__init__(server_instance, full_name)

        this_dir = dirname(realpath(__file__))
        self.emotes_path = join(this_dir, 'emotesdb')
        self.infodb_path = join(this_dir, 'emote_info_db')
        self.tagdb_path = join(this_dir, 'emote_tag_db')
        self.custom_emote_filename = 'ponybot.json'
        self.tag_list = {}
        self.emote_list = {}
        self.raw_emote_list = []
        self.is_running = True
        self.build_dir(join(self.emotes_path, "tmp"))
        self.blacklist = {}
        self.allow_nsfw = False
        self.config_path = join(self.local_data_dir, "emotes.json")
        self.load_blacklist()

        asyncio.ensure_future(self.build_emote_db())

    def load_blacklist(self):
        if isfile(self.config_path):
            self.blacklist = json.loads(open(self.config_path).read())

    @staticmethod
    def build_dir(path):
        try:
            os.makedirs(os.path.dirname(path))
        except Exception as E:
            if "File exists" not in str(E):
                print(E)
                return False
        return True

    def save_blacklist(self):
        if not self.build_dir(self.config_path):
            return
        f = open(self.config_path, "w")
        if f:
            f.write(json.dumps(self.blacklist))

    def save_target_image(self, source, name, x_offset, y_offset, x_size, y_size, flip, convert):
        m_img = Image.open(source)
        if x_size!=0 and y_size!=0:
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

    def sanitize_name(self, name):
        # we use replace to strip any symbols that'd allow file naviagation.
        return name.replace('/', '').replace('\\', '').replace('.', '')

    def build_emote(self, name, image_path, x_offset, y_offset, x_size, y_size, flip, convert):
        # print("Emote: '" + name + "' Img: " + ImagePath + " o: " + str(xOffset) + " " + str(yOffset) + " s: " + str(xSize) + " " + str(ySize))
        name_base = name + ".tmp"
        frame_cnt = 1
        transform = APNGLib.TransformNoGif1Frame
        if x_size != 0 and y_size != 0:
            transform |= APNGLib.TransformCrop
        if flip is True:
            transform |= APNGLib.TransformFlipHorizontal
        try:
            urllib.request.urlretrieve(image_path, name_base)
            if os.path.splitext(image_path)[1]==".png":
                frame_cnt = APNGLib.MakeGIF(name_base, join(self.emotes_path, name) + ".gif", transform, x_offset, y_offset,
                                        x_size, y_size)
            else:
                frame_cnt = 1
            if frame_cnt == 1:
                # we tell the function the  not to save if there is only 1 frame, so we can save it as a png instead.
                self.save_target_image(name_base, name, x_offset, y_offset, x_size, y_size, flip, convert)

        except Exception as e:
            if str(e) == "bad transparency mask":
                try:
                    # save as regular file instead.
                    self.save_target_image(name_base, name, x_offset, y_offset, x_size, y_size, flip, False)
                except Exception as e2:
                    print("Error2 processing emote: " + name)
                    print(e2)
                    return False

            else:
                print("Error processing emote: " + name)
                print(e)
                return False
        for i in range(0, 3):  # retry a few times in case failure is due to the os hasn't given up a handle right away.
            try:
                os.remove(name_base)
                break
            except:
                time.sleep(1)
        return True

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
                name = self.sanitize_name(key[1:])
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

    def find_emote_path(self, emotename):
        path = join(self.emotes_path, self.sanitize_name(emotename))
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

        if self.blacklist.get(emote.name):
            await self.client.send_message(message.channel, 'Emote is blacklisted on this server.')
            return
        if not self.allow_nsfw and emote.is_nsfw:
            await self.client.send_message(message.channel, 'Emote is tagged as nsfw.')
            return

        path = self.find_emote_path(emote.name)
        if not path:
            if not self.build_emote(emote.name, emote.image_path, emote.x_offset, emote.y_offset, emote.x_size, emote.y_size,
                             emote.flip, True):
                await self.client.send_message(message.channel, "Emote doesn't work")
                return
            path = self.find_emote_path(emote.name)
        await self.client.send_file(message.channel, path)

    @glados.DummyPermissions.admin
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

        self.blacklist[emote.name] = 1

        self.save_blacklist()
        await self.client.send_message(message.channel, 'blacklisted emote.')

    @glados.DummyPermissions.admin
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

        self.blacklist.pop(emote.name, None)
        self.save_blacklist()
        await self.client.send_message(message.channel, 'removed emote from blacklist.')

    @glados.DummyPermissions.admin
    @glados.Module.command('ponynsfw', '<enable/disable>', 'sets a flag allowing or disallowing nsfw emotes on the '
                           'specefied server, only a mod or admin can run this command.')
    async def pony_nsfw(self, message, content):
        if content != "enable" and content != "disable":
            await self.provide_help('ponynsfw', message)
            return
        enable = content == "enable"
        self.allow_nsfw = enable
        self.save_blacklist()
        if enable:
            await self.client.send_message(message.channel, 'nsfw emotes have been enabled.')
        else:
            await self.client.send_message(message.channel, 'nsfw emotes have been disabled.')
        return


    @glados.DummyPermissions.admin
    @glados.Module.command('ponyadd', '<emote> <pngimagepath> [Optional tags]', 'adds a custom pony emote to the bot, and adds it the servers json file')
    async def pony_add(self, message, content):
        csplit = content.split()
        if len(csplit)<2:
            return await self.provide_help('ponyadd', message)

        name = self.sanitize_name(csplit[0])
        emote = self.emote_list.get(csplit[0])
        is_nsfw = False
        if emote:
            return await self.client.send_message(message.channel, 'emote name is already in use.')

        if not self.build_emote(name, csplit[1], 0, 0, 0, 0, False, False):
            return await self.client.send_message(message.channel, 'Failed to create emote.')

        #append new emote into our bot's json file.
        jinfo_file = open(join(self.infodb_path, self.custom_emote_filename))
        jtag_file = open(join(self.tagdb_path,self.custom_emote_filename))
        jinfodata = json.loads(jinfo_file.read())
        jtagdata = json.loads(jtag_file.read())
        jinfo_file.close()
        jtag_file.close()
        jinfodata['/'+name] = {}
        jinfodata['/'+name]["Emotes"] = {}
        jinfodata['/'+name]["Emotes"][""] = {}
        jinfodata['/'+name]["Emotes"][""]["Image"] = csplit[1]
        jtagdata['/'+name] = []
        for tag in csplit:
            if tag==csplit[0] or tag==csplit[1]:
                continue
            if tag[0]!='+':
                tag = '+' + tag
            if not self.tag_list.get(tag):
                self.tag_list[tag] = {}
            self.tag_list[tag][name] = ""
            if tag == "+nsfw":
                is_nsfw = True
            jtagdata['/'+name].append(tag)
        jinfo_file = open(join(self.infodb_path, self.custom_emote_filename), 'w')
        jtag_file = open(join(self.tagdb_path, self.custom_emote_filename), 'w')
        jinfo_file.write(json.dumps(jinfodata))
        jtag_file.write(json.dumps(jtagdata))
        jinfo_file.close()
        jtag_file.close()
        #add emote to existing db.
        self.emote_list[name] = Eemote(name, csplit[1], 0, 0, 0, 0, False, is_nsfw)
        self.raw_emote_list.append(name)
        return await self.client.send_message(message.channel, 'Added '+name+' to emote list.')

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
        for msg in self.pack_into_messages(response):
            await self.client.send_message(message.author, msg)
