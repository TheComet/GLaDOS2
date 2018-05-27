import sys
import os
import codecs
import re
from glados.tools.json import load_json_compressed
from time import strptime
from shutil import copyfile
from lzma import LZMAFile


if len(sys.argv) < 2:
    print("Please specify where the dumpservers.json.xz file is located. You can obtain it with the bot command .dumpservers")
    sys.exit(-1)


info = load_json_compressed(sys.argv[1])


class Message(object):
    def __init__(self, raw):
        match = re.match('^\[(.*?)\](.*)$', raw)
        items = match.group(2).split(':')
        self.stamp_str = match.group(1)
        self.stamp = strptime(self.stamp_str, '%Y-%m-%d %H:%M:%S')
        self.server = items[0].strip()
        self.channel = items[1].strip('#').strip()
        match = re.match('^(.*)\((\d+)\)$', items[2].strip())  # need to further split author and ID
        if match:
            self.author = match.group(1)
            self.author_id = match.group(2)
        else:
            self.author = items[2].strip()
            self.author_id = "000000000000000000"
        self.message = items[3].strip()


failed_members = set()
for server_id in os.listdir("data"):
    if not os.path.isdir(os.path.join("data", server_id)):
        print("skipping file " + os.path.join("data", server_id))
        continue
    if server_id not in info:
        print("Server with ID {} was not found in dumpservers.json.xz file! Skipping...".format(server_id))
        continue
    log_dir = os.path.join("data", server_id, "log2")
    if not os.path.isdir(log_dir):
        print("Server \"{}\" has no logs! Skipping...".format(info[server_id]["name"]))
        continue

    for log_file_name in sorted(os.listdir(log_dir)):
        print("Processing file {} on server {}".format(log_file_name, info[server_id]["name"]))
        log_data = LZMAFile(os.path.join(log_dir, log_file_name), 'r').read().decode('utf-8')
        new_log_file = LZMAFile(os.path.join(log_dir, log_file_name), 'w')
        for line in log_data.split('\n'):
            if not line:
                continue
            m = Message(line)

            if m.author_id == "000000000000000000":
                for id, member in info[server_id]["members"].items():
                    if m.author == member["name"]:
                        m.author_id = id
                        break
                else:
                    failed_members.add(m.author)

            log_msg = u'[{0}] {1}({2}): {3}: {4}({5}): {6}\n'.format(
                m.stamp_str,
                info[server_id]["name"],
                server_id,
                m.channel,
                m.author,
                m.author_id,
                m.message)
            new_log_file.write(log_msg.encode('utf-8'))


print("The following members failed to match any IDs in the dumpservers.json.xz file. This means they were no longer part of the server when the server data was dumped.")
for name in failed_members:
    print(name)
