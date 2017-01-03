import glados


class Google(glados.Module):

    def get_help_list(self):
        return [
            glados.Help('google', '<term>', 'Generate a google link')
        ]

    @glados.Module.commands('google')
    def google(self, message, term):
        if term == '':
            yield from self.provide_help('google', message)
            return
