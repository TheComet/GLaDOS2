class Help(object):
    def __init__(self, command, argument_list_str, description):
        self.command = command
        self.argument_list = argument_list_str
        self.description = description

    def get(self):
        if not self.argument_list == '':
            return '{0} **{1}** -- *{2}*'.format(self.command, self.argument_list, self.description)
        return '{0} -- *{1}*'.format(self.command, self.description)
