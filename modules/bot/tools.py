from glados import Module
from glados import Permissions
from glados.tools.json import load_json_compressed, save_json_compressed
from os.path import join


class DumpServers(Module):
    @Permissions.admin
    @Module.command("dumpservers", "", "Dumps all metadata from all channels and users from all servers. IDs, nicks and names. PMs you a JSON file.")
    async def dumpservers(self, message, args):
        o = dict()
        for server in self.client.servers:
            o[server.id] = dict()
            o[server.id]["name"] = server.name
            o[server.id]["channels"] = dict()
            o[server.id]["roles"] = dict()
            o[server.id]["members"] = dict()
            for channel in server.channels:
                o[server.id]["channels"][channel.id] = dict()
                o[server.id]["channels"][channel.id]["name"] = channel.name
                o[server.id]["channels"][channel.id]["topic"] = channel.topic
            for role in server.roles:
                o[server.id]["roles"][role.id] = dict()
                o[server.id]["roles"][role.id]["name"] = role.name
            for member in server.members:
                o[server.id]["members"][member.id] = dict()
                o[server.id]["members"][member.id]["name"] = member.name
                o[server.id]["members"][member.id]["nick"] = member.nick
                o[server.id]["members"][member.id]["bot"] = member.bot

        file_name = join(self.global_data_dir, "dumpservers.json.xz")
        save_json_compressed(file_name, o)
        await self.client.send_file(message.author, file_name)
