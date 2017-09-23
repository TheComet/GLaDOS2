import glados


class Poll(glados.Module):
    def get_help_list(self):
        return [
            glados.Help('poll', '<new> <name> <1. first option 2. second option 3. ...>', 'Start a new poll with a number of options'),
            glados.Help('poll', '<vote> <name> <option>', 'Place your vote in a running poll'),
            glados.Help('poll', '<close|show> <name>', 'Close or show a poll')
        ]

    @glados.Module.commands('poll')
    def handle_poll(self, message, content):
        parts = [x.strip() for x in content.split() if len(x) > 0]
        if len(parts) == 0:
            yield from self.provide_help('poll', message)
            return
        cmd = parts[0]
        if cmd == 'new':
            yield from self.handle_new(message, parts[1:])
        elif cmd == 'vote':
            yield from self.handle_vote(message, parts[1:])
        elif cmd == 'close':
            yield from self.handle_close(message, parts[1:])
        elif cmd == 'show':
            yield from self.handle_show(message, parts[1:])

    def handle_new(self, message, parts):
        if len(parts) < 2:
            yield from self.provide_help('poll', message)
            return

        memory = self.get_memory()
        name = parts[0]
        if name in memory:
            yield from self.client.send_message(message.channel, 'Poll with name "{}" still active'.format(name))
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
            yield from self.client.send_message(message.channel, 'Need at least two options')
            return

        memory[name] = dict()
        memory[name]['options'] = options
        memory[name]['votes'] = dict()

        msg = 'Poll "{}" created! Vote with ``.poll vote {} <number>``'.format(name, name)
        msg = msg + '\n  ' + '\n  '.join(options)
        yield from self.client.send_message(message.channel, msg)

    def handle_vote(self, message, parts):
        if len(parts) < 2:
            yield from self.provide_help('poll', message)
            return

        memory = self.get_memory()
        name = parts[0]
        if not name in memory:
            yield from self.client.send_message(message.channel, 'Unknown poll with name "{}"'.format(name))
            return

        if message.author.id in memory[name]['votes']:
            yield from self.client.send_message(message.channel, 'You already voted!')
            return

        try:
            vote_id = int(parts[1])
        except ValueError:
            yield from self.client.send_message(message.channel, 'Failed to parse your value "{}"'.format(parts[1]))
            return

        if vote_id < 1 or vote_id > len(memory[name]['options']):
            yield from self.client.send_message(message.channel, 'Invalid option "{}"'.format(vote_id))
            return

        memory[name]['votes'][message.author.id] = vote_id
        vote = memory[name]['options'][vote_id - 1]
        yield from self.client.send_message(message.channel, '{} voted for {}!'.format(message.author.name, vote))

    def handle_close(self, message, parts):
        if len(parts) < 1:
            yield from self.provide_help('poll', message)
            return

        memory = self.get_memory()
        name = parts[0]
        if not name in memory:
            yield from self.client.send_message(message.channel, 'Unknown poll "{}"'.format(name))
            return

        vote_dict = dict()
        for author, vote_id in memory[name]['votes'].items():
            if not vote_id in vote_dict:
                vote_dict[vote_id] = 0
            vote_dict[vote_id] += 1

        if len(vote_dict) == 0:
            del memory[name]
            return
        winner_option, winner_votes = sorted(vote_dict.items(), key=lambda kv: kv[1])[-1]
        winner_option_str = memory[name]['options'][winner_option - 1]
        del memory[name]
        yield from self.client.send_message(message.channel,
                'Poll "{}" closed.\nWinning option is "{}" with {} votes'.format(name, winner_option_str, winner_votes))

    def handle_show(self, message, parts):
        if len(parts) < 1:
            yield from self.provide_help('poll', message)
            return

        memory = self.get_memory()
        name = parts[0]
        if not name in memory:
            yield from self.client.send_message(message.channel, 'Unknown poll "{}"'.format(name))
            return

        msg = 'Vote with ``.poll vote {} <number>``'.format(name, name)
        msg = msg + '\n  ' + '\n  '.join(memory[name]['options'])
        yield from self.client.send_message(message.channel, msg)

    @glados.Module.commands('polls')
    def show_polls(self, message, content):
        polls = [k for k, v in self.get_memory().items()]
        yield from self.client.send_message(message.channel, 'Open polls:\n' + '\n  '.join(polls))
