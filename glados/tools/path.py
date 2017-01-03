import sys


def add_import_paths(paths):
    for path in paths:
        if not path in sys.path:
            sys.path.append(path)
