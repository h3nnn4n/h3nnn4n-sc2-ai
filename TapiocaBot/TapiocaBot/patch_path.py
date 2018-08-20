import sys


def patch_path():
    lib_path = 'python-sc2-external'
    if lib_path not in sys.path:
        sys.path.insert(1, lib_path)
