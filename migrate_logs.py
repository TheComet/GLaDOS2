import sys
import os
import codecs
from glados.tools.json import load_json_compressed
from shutil import copyfile
from lzma import LZMAFile


if len(sys.argv) < 2:
    print("Please specify where the dumpservers.json.xz file is located. You can obtain it with the bot command .dumpservers")
    sys.exit(-1)


info = load_json_compressed(sys.argv[1])


def sanitize_file_name(name):
    return name.replace('/', ':').replace('\\', ':')


def logs_file_name(author):
    return sanitize_file_name(author) + '.txt'


matched = list()
for server_id in os.listdir("data"):
    if not os.path.isdir(os.path.join("data", server_id)):
        print("skipping file " + os.path.join("data", server_id))
        continue
    if server_id not in info:
        print("Server with ID {} was not found in dumpservers.json.xz file! Skipping...".format(server_id))
        continue
    log_dir = os.path.join("data", server_id, "logs")
    if not os.path.isdir(log_dir):
        print("Server \"{}\" has no logs! Skipping...".format(info[server_id]["name"]))
        continue
    new_log_dir = os.path.join("data", server_id, "log2")
    if not os.path.exists(new_log_dir):
        os.mkdir(new_log_dir)

    for log_file in os.listdir(log_dir):
        for id, member in info[server_id]["members"].items():
            if logs_file_name(member["name"].lower()) == log_file:
                old_file_name = os.path.join(log_dir, log_file)
                new_file_name = os.path.join(new_log_dir, id + '.txt.xz')
                with LZMAFile(new_file_name, 'w') as f_new:
                    with codecs.open(old_file_name, encoding='utf-8') as f_old:
                        f_new.write(f_old.read().encode('utf-8'))
                matched.append(old_file_name + "  ->  " + new_file_name)
                break
        else:
            print("Failed to match file {} on server {}".format(os.path.join(log_dir, log_file), info[server_id]["name"]))

print("Matched {} files".format(len(matched)))
