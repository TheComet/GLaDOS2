import sys
import os
from glados.tools.json import load_json_compressed


if len(sys.argv) < 2:
    print("Please specify where the dumpservers.json.xz file is located. You can obtain it with the bot command .dumpservers")
    sys.exit(-1)


info = load_json_compressed(sys.argv[1])


def sanitize_file_name(name):
    return name.replace('/', ':').replace('\\', ':')


def quotes_file_name(author):
    return sanitize_file_name(author) + '.txt'


matched = list()
for server_id in os.listdir("data"):
    if not os.path.isdir(os.path.join("data", server_id)):
        print("skipping file " + os.path.join("data", server_id))
        continue
    if server_id not in info:
        print("Server with ID {} was not found in dumpservers.json.xz file! Skipping...".format(server_id))
        continue
    quote_dir = os.path.join("data", server_id, "quotes")
    if not os.path.isdir(quote_dir):
        print("Server \"{}\" has no quotes! Skipping...".format(info[server_id]["name"]))
        continue

    for quote_file in os.listdir(quote_dir):
        for id, member in info[server_id]["members"].items():
            if quotes_file_name(member["name"].lower()) == quote_file:
                old_file_name = os.path.join(quote_dir, quote_file)
                new_file_name = os.path.join(quote_dir, id + '.txt')
                os.rename(old_file_name, new_file_name)
                matched.append(old_file_name + "  ->  " + new_file_name)
                break
        else:
            print("Failed to match file {} on server {}".format(os.path.join(quote_dir, quote_file), info[server_id]["name"]))

print("Matched {} files".format(len(matched)))
