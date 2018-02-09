import json


def load_json(file_name):
    return json.loads(open(file_name, 'rb').read().decode('utf-8'))


def save_json(file_name, o):
    data = json.dumps(o).encode('utf-8')
    open(file_name, 'wb').write(data)
