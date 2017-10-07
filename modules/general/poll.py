import glados


class Poll(glados.Module):
    def __init__(self, server_instance, full_name):
        super(Poll, self).__init__(server_instance, full_name)
        self.polls = dict()

    @glados.Module.command('pollnew', '<name> <1. first option 2. second option 3. ...>', 'Start a new poll with a number of options')
    async def handle_new(self, message, parts):
        parts = parts.split()
        name = parts[0]
        if name in self.polls:
            await self.client.send_message(message.channel, 'Poll with name "{}" still active'.format(name))
            return

        counter = 1
        options_str = ' '.join(parts[1:])
        options = list()
        while True:
            index_first = options_str.find('{}.'.format(counter))
            index_last = options_str.find('{}.'.format(counter + 1))
            if index_first == -1:
                break
            if index_last == -1:
                options.append(options_str[index_first:].strip())
            else:
                options.append(options_str[index_first:index_last].strip())
            counter += 1

        if counter < 3:
            await self.client.send_message(message.channel, 'Need at least two options')
            return

        self.polls[name] = dict()
        self.polls[name]['options'] = options
        self.polls[name]['votes'] = dict()

        msg = 'Poll "{}" created! Vote with ``{}pollvote {} <number>``'.format(self.command_prefix, name, name)
        msg = msg + '\n  ' + '\n  '.join(options)
        await self.client.send_message(message.channel, msg)

    @glados.Module.command('pollvote', '<name> <option>', 'Place your vote in a running poll')
    async def handle_vote(self, message, parts):
        parts = parts.split()
        name = parts[0]
        if name not in self.polls:
            await self.client.send_message(message.channel, 'Unknown poll with name "{}"'.format(name))
            return

        if message.author.id in self.polls[name]['votes']:
            await self.client.send_message(message.channel, 'You already voted!')
            return

        try:
            vote_id = int(parts[1])
        except ValueError:
            await self.client.send_message(message.channel, 'Failed to parse your value "{}"'.format(parts[1]))
            return

        if vote_id < 1 or vote_id > len(self.polls[name]['options']):
            await self.client.send_message(message.channel, 'Invalid option "{}"'.format(vote_id))
            return

        self.polls[name]['votes'][message.author.id] = vote_id
        vote = self.polls[name]['options'][vote_id - 1]
        await self.client.send_message(message.channel, '{} voted for {}!'.format(message.author.name, vote))

    @glados.Module.command('pollclose', '<name>', 'Close a poll and show the results')
    async def handle_close(self, message, parts):
        parts = parts.split()
        name = parts[0]
        if not name in self.polls:
            await self.client.send_message(message.channel, 'Unknown poll "{}"'.format(name))
            return

        vote_dict = dict()
        for author, vote_id in self.polls[name]['votes'].items():
            if not vote_id in vote_dict:
                vote_dict[vote_id] = 0
            vote_dict[vote_id] += 1

        if len(vote_dict) == 0:
            del self.polls[name]
            return
        winner_option, winner_votes = sorted(vote_dict.items(), key=lambda kv: kv[1])[-1]
        winner_option_str = self.polls[name]['options'][winner_option - 1]
        del self.polls[name]
        await self.client.send_message(message.channel,
                'Poll "{}" closed.\nWinning option is "{}" with {} votes'.format(name, winner_option_str, winner_votes))

    @glados.Module.command('pollshow', '<name>', 'Show the options of a running poll')
    async def handle_show(self, message, parts):
        parts = parts.split()
        name = parts[0]
        if not name in self.polls:
            await self.client.send_message(message.channel, 'Unknown poll "{}"'.format(name))
            return

        msg = 'Vote with ``{}poll vote {} <number>``'.format(self.command_prefix, name, name)
        msg = msg + '\n  ' + '\n  '.join(self.polls[name]['options'])
        await self.client.send_message(message.channel, msg)

    @glados.Module.command('polls', '', 'List all of the polls that are open')
    async def show_polls(self, message, content):
        polls = [k for k, v in self.polls.items()]
        await self.client.send_message(message.channel, 'Open polls:\n' + '\n  '.join(polls))
