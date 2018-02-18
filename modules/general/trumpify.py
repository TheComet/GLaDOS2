from glados import Module
from PIL import ImageFont, Image, ImageDraw
from os.path import join, dirname, realpath, exists
from os import makedirs


class Trumpify(Module):

    left_margin = 56
    right_margin = 68
    font_size = 26
    font_pad = 2

    def __init__(self, server_instance, full_name):
        super(Trumpify, self).__init__(server_instance, full_name)

        self.cache_dir = join(self.local_data_dir, 'trumpify')
        if not exists(self.cache_dir):
            makedirs(self.cache_dir)

    @Module.command('trumpify', '<user or text>', 'If user, converts their last message into a trump tweet. If text, '
                    'converts the text into a trump tweet.')
    async def trumpify(self, message, content):
        members, roles, error = self.parse_members_roles(message, content, membercount=1, rolecount=0)
        if error or len(members) == 0:
            text = content
        else:
            text = self.get_member_text(members[0])
            if not text:
                text = content

        file_name = join(self.local_data_dir, 'trumpify', message.author.id + '.png')
        self.generate_tweet(text, file_name)
        await self.client.send_file(message.channel, file_name)

    def get_member_text(self, member):
        for msg in reversed(self.client.messages):
            if msg.author == member:
                return msg.content
        return None

    def generate_tweet(self, text, output_file_name):
        this_path = dirname(realpath(__file__))

        # Load header and footer images
        header_file = join(this_path, 'trump-tweet-header.png')
        footer_file = join(this_path, 'trump-tweet-footer.png')
        header = Image.open(header_file, 'r')
        footer = Image.open(footer_file, 'r')

        # Create the background image and render the tweet text into the middle (making space for header and footer)
        font = ImageFont.truetype(join(this_path, 'DejaVuSerif.ttf'), self.font_size)
        lines = self.wrap_text(text, font, header.size[0])
        canvas_width = header.size[0]
        canvas_height = header.size[1] + footer.size[1] + len(lines) * (self.font_size + self.font_pad * 2)
        canvas = Image.new('RGB', (canvas_width, canvas_height), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        for i, line in enumerate(lines):
            draw.text((self.left_margin, header.size[1] + i*30), line, (0, 0, 0), font=font)

        # Add footer and header
        canvas.paste(header, (0, 0))
        canvas.paste(footer, (0, canvas_height - footer.size[1]))

        canvas.save(output_file_name)

    def wrap_text(self, text, font, img_width):
        max_width = img_width - self.left_margin - self.right_margin

        lines = list()
        buffer = ''
        for word in text.split():
            if font.getsize(buffer + word)[0] < max_width:
                buffer += ' ' + word
            else:
                lines.append(buffer.strip())
                buffer = word
        if buffer:
            lines.append(buffer.strip())
        return lines
