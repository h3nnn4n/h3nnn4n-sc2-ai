import sys

def patch_path():
    lib_path = '../libs'

    if lib_path not in sys.path:
        sys.path.insert(1, lib_path)
