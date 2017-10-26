import glados
import os
from os import listdir
from os.path import isfile, dirname, realpath, join
import asyncio
import json
import urllib.request
from PIL import Image
import APNGLib
import time


class Eemote:
    def __init__(self, name, image_path, x_offset, y_offset, x_size, y_size, flip):
        self.name = name
        self.image_path = image_path
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.x_size = x_size
        self.y_size = y_size
        self.flip = flip


class BuildEmotes(glados.Module):
    def __init__(self, server_instance, full_name):
        super(BuildEmotes, self).__init__(server_instance, full_name)

        this_dir = dirname(realpath(__file__))
        self.emotedb_path = join(this_dir, 'emotesdb')
        self.configdb_path = join(this_dir, 'emote_info_db')
        self.worker_threads = 16
        self.building_db = ""
        self.is_running = False
        self.build_dir(join(self.emotedb_path, 'tmp'))

    def build_dir(self, path):
        try:
            os.makedirs(os.path.dirname(path))
        except Exception as E:
            if "File exists" not in str(E):
                print(E)
                return False
        return True

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
            m_img.save(join(self.emotedb_path, name) + ".png", transparency=255, optimize=True)
        else:
            m_img.save(join(self.emotedb_path, name) + ".png", optimize=True)

    def build_emote(self, name, image_path, x_offset, y_offset, x_size, y_size, flip):
        #print("Emote: '" + name + "' Img: " + ImagePath + " o: " + str(xOffset) + " " + str(yOffset) + " s: " + str(xSize) + " " + str(ySize))
        name_base = name + ".tmp"
        frame_cnt = 1
        transform = APNGLib.TransformNoGif1Frame
        if x_size !=0 and y_size !=0:
            transform |= APNGLib.TransformCrop
        if flip is True:
            transform |= APNGLib.TransformFlipHorizontal
        try:
            urllib.request.urlretrieve(image_path, name_base)
            frame_cnt = APNGLib.MakeGIF(name_base, join(self.emotedb_path,name) + ".gif", transform, x_offset, y_offset,
                                        x_size, y_size)
            if (frame_cnt == 1):
                # we tell the function the  not to save if there is only 1 frame, so we can save it as a png instead.
                self.save_target_image(name_base, name, x_offset, y_offset, x_size, y_size, flip, True)

        except Exception as e:
            if (str(e) == "bad transparency mask"):
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

    def build_emote_db(self, data_set):
        for e in data_set:
            self.build_emote(e.name, e.image_path, e.x_offset, e.y_offset, e.x_size, e.y_size, e.flip)

    async def build_db(self, db_name):
        data_set = []
        for i in range(0, self.worker_threads):
            data_set.append([])

        path = join(self.configdb_path, db_name) + ".json"
        if not isfile(path):
            print("Unknown db: " + db_name)
            return
        self.building_db = db_name
        print("Building db: " + db_name)
        json_file = open(path)
        jdata = json.loads(json_file.read())
        json_file.close()
        i = 0
        for key, items in jdata.items():
            # strip out any symbols from the name that'd allow file pathing.
            name = key[1:].replace('/', '').replace('\\', '').replace('.', '')
            emote = items.get("Emotes")
            if not emote: continue
            emote = emote.get("")
            if not emote: continue
            image_path = emote.get("Image")
            offset = emote.get("Offset")
            size = emote.get("Size")
            css_transform = None
            if (emote.get("CSS")): css_transform = emote["CSS"].get("transform")
            flip = False
            x_offset = 0
            y_offset = 0
            x_size = 0
            y_size = 0
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
            data_set[i].append(
                Eemote(name, "https://" + image_path.split('//')[1], x_offset, y_offset, x_size, y_size, flip))
            i = (i + 1) % self.worker_threads
            await asyncio.sleep(0)
        loop = asyncio.get_event_loop()
        tasks = []
        for d in data_set:
            tasks.append(loop.run_in_executor(None, self.build_emote_db, d))
        for t in tasks:
            await t
        print("Finished building: " + db_name)
        return

    async def run_thread(self, content):
        self.is_running = True
        try:
            if not content:
                files = [f for f in listdir(self.configdb_path) if isfile(join(self.configdb_path, f))]
                for f in files:
                    await self.build_db(os.path.splitext(f)[0])
                self.is_running = False
                print("Finished thread!")
                return
            databases = content.split(' ')
            for db in databases:
                await self.build_db(db)
        except Exception as e:
            print("Exception during thread: ")
            print(e)
        self.is_running = False
        print("Finished thread!")
        return

    @glados.Permissions.admin
    @glados.Module.command('ponybuild', '[db] [db...]', 'Admin only usable, use to rebuild the '
                           'entire pony emote cache db, or only a partial db specefied by Opetiondb(i.e: mylittlepony only '
                           'builds for the mylittlepony.json db)')
    async def build_ponydb(self, message, content):
        # since this is a long process, we will spawn a thread to do the work in to not tie of the bot.
        if self.is_running is True:
            await self.client.send_message(message.channel, "Database is currently building: " + self.building_db)
            return
        await self.client.send_message(message.channel, 'Building pony database...this may take awhile.')

        asyncio.ensure_future(self.run_thread(content))
        return
