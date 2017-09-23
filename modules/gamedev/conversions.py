import glados
import struct
import re
import base64


class Conversions(glados.Module):

    def get_help_list(self):
        return [
            glados.Help('bin', '<data>', 'Convert a number or string to a binary representation'),
            glados.Help('hex', '<data>', 'Convert a number or string to a hexadecimal representation'),
            glados.Help('dec', '<data>', 'Convert a number or string to a decimal representation'),
            glados.Help('oct', '<data>', 'Convert a number or string to an octal representation'),
            glados.Help('b64e', '<data>', 'Encode base64'),
            glados.Help('b64d', '<data>', 'Decode base64'),
        ]

    @glados.Module.commands('bin')
    def bin(self, message, data):
        if data == '':
            await self.provide_help('bin', message)
            return

        data = self.convert_type(data)
        if isinstance(data, str):
            if self.is_hex(data):
                data = 'Interpreted as hex: ```{}```'.format(self.hex_to_binary(data))
            else:
                data = 'Interpreted as string: ```{}```'.format(' '.join([bin(ord(c)).replace('0b', '').rjust(8, '0') for c in data]))
        elif isinstance(data, float):
            data = 'Interpreted as ieee754 float: ```{}```'.format(self.float_to_binary(data))
        else:
            data = 'Interpreted as decimal: ```{}```'.format(bin(data).rjust(8, '0'))

        await self.client.send_message(message.channel, data)

    @glados.Module.commands('hex')
    def hex(self, message, data):
        if data == '':
            await self.provide_help('hex', message)
            return

        data = self.convert_type(data)
        if isinstance(data, str):
            if self.is_binary(data):
                data = 'Interpreted as binary: ```{}```'.format(self.binary_to_hex(data))
            else:
                data = 'Interpreted as string: ```{}```'.format(' '.join([hex(ord(c)).replace('0x', '').rjust(2, '0') for c in data]))
        elif isinstance(data, float):
            data = 'Interpreted as ieee754 float: ```{}```'.format(self.float_to_hex(data))
        else:
            data = 'Interpreted as unsigned integer: ```{}```'.format(hex(data).replace('0x', '').rjust(2, '0'))

        await self.client.send_message(message.channel, data)

    @glados.Module.commands('dec')
    def dec(self, message, data):
        if data == '':
            await self.provide_help('dec', message)
            return

        if self.is_binary(data):
            data = 'Interpreting as binary: ```{}```'.format(self.binary_to_decimal(data))
        elif self.is_hex(data):
            data = 'Interpreted as hex: ```{}```'.format(self.hex_to_decimal(data))
        else:
            await self.client.send_message(message.channel, 'Conversion not implemented')
            return

        await self.client.send_message(message.channel, data)

    @glados.Module.commands('b64e')
    def b64e(self, message, data):
        if data == '':
            await self.provide_help('b64e', message)
            return

        try:
            data = 'Encoded base64: ```{}```'.format(base64.b64encode(str(data).encode()).decode())
        except:
            data = 'Encoding failed.'
        await self.client.send_message(message.channel, data)

    @glados.Module.commands('b64d')
    def b64d(self, message, data):
        if data == '':
            await self.provide_help('b64d', message)
            return

        try:
            data = 'Decoded base64: ```{}```'.format(base64.b64decode(str(data).encode()).decode())
        except:
            data = 'Decoding failed.'
        await self.client.send_message(message.channel, data)

    @staticmethod
    def convert_type(data):
        if Conversions.is_binary(data):
            return str(data)

        if "." in data:
            try:
                return float(data)
            except ValueError:
                pass

        try:
            return int(data)
        except ValueError:
            pass

        return str(data)

    @staticmethod
    def float_to_binary(num):
        return ' '.join(bin(c).replace('0b', '').rjust(8, '0') for c in struct.pack('!f', num))

    @staticmethod
    def float_to_hex(num):
        return ' '.join(hex(c).replace('0x', '').rjust(2, '0') for c in struct.pack('!f', num))

    @staticmethod
    def do_conversion(data, base, prefix):
        data = data.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '').replace(prefix, '')[::-1]
        width = 256
        ret = list()
        for byte in [data[i:][:8][::-1] for i in range(0, len(data), base)]:
            pass

    @staticmethod
    def binary_to_hex(data):
        data = data.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '').replace('0b', '')[::-1]
        ret = list()
        for byte in [data[i:][:8] for i in range(0, len(data), 8)]:
            ret.append(hex(int(byte, 2)).replace('0x', '').rjust(2, '0'))
        return ' '.join(ret)

    @staticmethod
    def binary_to_decimal(data):
        data = data.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '').replace('0b', '')
        ret = list()
        for byte in [data[i:i+8] for i in range(0, len(data), 8)]:
            ret.append(str(int(byte, 2)))
        return ' '.join(ret)

    @staticmethod
    def binary_to_octal(data):
        pass

    @staticmethod
    def hex_to_binary(data):
        data = data.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '').replace('0x', '')
        ret = list()
        for byte in [data[i:i+2] for i in range(0, len(data), 2)]:
            ret.append(bin(int(byte, 16)).replace('0b', '').rjust(8, '0'))
        return ' '.join(ret)

    @staticmethod
    def hex_to_decimal(data):
        data = data.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '').replace('0x', '')
        ret = list()
        for byte in [data[i:i+2] for i in range(0, len(data), 2)]:
            ret.append(str(int(byte, 16)))
        return ' '.join(ret)

    @staticmethod
    def is_binary(data):
        if len(re.findall('0b', data)) > 0:
            return True
        return False

    @staticmethod
    def is_hex(data):
        if len(re.findall('0x', data)) > 0:
            return True
        return False
