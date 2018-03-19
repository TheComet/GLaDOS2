import json
import lzma


def load_json_compressed(file_name):
    with lzma.LZMAFile(file_name, 'r') as f:
        return json.loads(f.read().decode('utf-8'))


def save_json_compressed(file_name, o):
    with lzma.LZMAFile(file_name, 'w') as f:
        f.write(json.dumps(o, indent=2).encode('utf-8'))
    return file_name


def load_json(file_name):
    with open(file_name, 'rb') as f:
        return json.loads(f.read().decode('utf-8'))


def save_json(file_name, o):
    with open(file_name, 'wb') as f:
        f.write(json.dumps(o, indent=2).encode('utf-8'))
        return file_name
