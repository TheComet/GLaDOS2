import glados
import derpibooru


class Derpi(glados.Module):

    def get_help_list(self):
        return [
            glados.Help('derpi', '<s|r> [query]', 'Search derpibooru for an image. The first argument is the mode. **s** means **search**, **r** means **random**.')
        ]

    @glados.Module.commands('derpi')
    def derpi(self, message, args):
        if args == '':
            yield from self.provide_help('derpi', message)
            return

        args = args.split(' ', 1)
        mode = args[0]
        tags = ''
        if len(args) > 1:
            tags = args[1].split(',')

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
            yield from  self.provide_help('derpi', message)
            return

        yield from self.client.send_message(message.channel, image.url)
