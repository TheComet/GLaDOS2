import glados
import derpibooru


class Derpi(glados.Module):
    @glados.Module.command('derpi', '<s|r> [query]', 'Search derpibooru for an image. The first argument is the mode. **s** means **search**, **r** means **random**.')
    async def derpi(self, message, args):
        args = args.split(' ', 1)
        mode = args[0]
        tags = ''
        if len(args) > 1:
            tags = args[1].split(',')

        try:
            if mode == 's':
                search = derpibooru.Search()
                if tags == '':
                    image = next(search)
                else:
                    image = next(search.query(*tags))
            elif mode == 'r':
                search = derpibooru.Search()
                if tags == '':
                    image = next(search.sort_by(derpibooru.sort.RANDOM))
                else:
                    image = next(search.sort_by(derpibooru.sort.RANDOM).query(*tags))
            else:
                await  self.provide_help('derpi', message)
                return

            await self.client.send_message(message.channel, image.url)
        except StopIteration:
            await self.client.send_message(message.channel, "No posts found!")
