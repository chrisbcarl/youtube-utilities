'''
Author:      Chris Carl
Date:        2023-10-15
Email:       chrisbcarl@outlook.com

Description:
    Wraps utils i just can't live without

Notes:
    2024-10-02 - chrisbcarl@outlook.com - FIX: find_common_directory had a bug with the drive letter on Windows...
'''
# stdlib imports
import os
import sys
import time
import logging
import argparse
import subprocess
from typing import List, Tuple, Optional

# project imports

LOGGER = logging.getLogger(__name__)


class NiceArgparseFormatter(argparse.ArgumentDefaultsHelpFormatter,
                            argparse.RawDescriptionHelpFormatter):
    pass


def get_value_from_dicts(key, *dicts):
    '''
    Description:
        given a bunch of dicts, get the first one's value, and if none are found, return None
    '''
    for dick in dicts:
        val = dick.get(key)
        if val is not None:
            return val
    return None


def get_safe_basename(filename):
    '''
    https://stackoverflow.com/a/7406369
    '''
    tokens = []
    for c in os.path.basename(filename).strip():
        if c.isalpha() or c.isdigit():
            tokens.append(c)
    return ''.join(tokens)


def indent(text, token='    ', count=1):
    '''
    '''
    lines = text.splitlines()
    lines = [f'{token * count}{line}' for line in lines]
    return '\n'.join(lines)


DEFAULT_STDOUT_FILE_DIRPATH = 'C:/temp/ffmpeg-std' if sys.platform == 'win32' else '/tmp/ffmpeg-std'
DEFAULT_STDOUT_FILE_DIRPATH = os.path.abspath(DEFAULT_STDOUT_FILE_DIRPATH)


def run_subprocess(args,
                   descriptive_filepath_for_stdout,
                   dirpath=DEFAULT_STDOUT_FILE_DIRPATH,
                   cwd=None):
    # type: (List[str], str, str, str) -> Tuple[int, str, str]
    stdout = None
    stderr = None
    shell = False

    now = time.time()
    basename = get_safe_basename(descriptive_filepath_for_stdout)
    os.makedirs(dirpath, exist_ok=True)
    stdout_filepath = os.path.abspath(
        os.path.join(dirpath, f'{now}_{basename}.stdout'))
    stdout = open(stdout_filepath, 'w', encoding='utf-8')
    stderr_filepath = os.path.abspath(
        os.path.join(dirpath, f'{now}_{basename}.stderr'))
    stderr = open(stderr_filepath, 'w', encoding='utf-8')
    LOGGER.debug('stdout: "%s", stderr: "%s"', stdout_filepath,
                 stderr_filepath)

    kwargs = dict(shell=shell, stdout=stdout, stderr=stderr, cwd=cwd)
    LOGGER.debug('invoking ffmpeg cmd: %r, kwargs: %s', args, kwargs)
    try:
        exit_code = subprocess.check_call(args,
                                          universal_newlines=True,
                                          **kwargs)
        LOGGER.debug('results for ffmpeg:  %r, exit_code: %d', args, exit_code)
    except subprocess.CalledProcessError as cpe:
        exit_code = cpe.returncode
        LOGGER.exception('failed command with exit code %s!', exit_code)
        if isinstance(args, list):
            LOGGER.error(subprocess.list2cmdline(args))
        else:
            LOGGER.error(args)
        LOGGER.error('stdout: "%s"', stdout_filepath)
        LOGGER.error('stderr: "%s"', stderr_filepath)
    stdout.close()
    with open(stdout_filepath, encoding='utf-8') as r:
        stdout = r.read()
    stderr.close()
    with open(stderr_filepath, encoding='utf-8') as r:
        stderr = r.read()
    if exit_code == 0:
        os.remove(stdout_filepath)
        os.remove(stderr_filepath)
    return exit_code, stdout, stderr


class LiveDict(object):
    data = None

    def __init__(self,
                 reload_function,
                 reload_function_args=None,
                 reload_function_kwargs=None):
        self.reload_function = reload_function
        self.reload_function_args = reload_function_args or []
        self.reload_function_kwargs = reload_function_kwargs or {}
        self.data = self.reload_function(*self.reload_function_args,
                                         **self.reload_function_kwargs)

    def reload(self):
        self.data = self.reload_function(*self.reload_function_args,
                                         **self.reload_function_kwargs)

    def get(self, key, default=None):
        self.reload()
        return self.data.get(key, default)


def find_common_directory(paths):
    # type: (List[str]) -> Optional[str]
    '''fairly crude algo:
        D:/bnl/2024-08-05_railyards-boulevard_sacremento-ca/rossy/2024-08-25_rossy_la-state-historic-park/youtube.txt
        D:/bnl/2024-08-05_railyards-boulevard_sacremento-ca/wavedash/2024-08-25_wavedash_la-state-historic-park/youtube.txt
        D:/bnl/2024-08-05_railyards-boulevard_sacremento-ca/whethan/2024-08-25_whethan_la-state-historic-park/youtube.txt
        D:/bnl/2024-08-05_railyards-boulevard_sacremento-ca/jai-wolf/2024-08-25_jai-wolf_la-state-historic-park/youtube.txt
        D:/bnl/2024-08-05_railyards-boulevard_sacremento-ca/madeon/2024-08-25_madeon_la-state-historic-park/youtube.txt
    should result in
        D:/bnl/2024-08-05_railyards-boulevard_sacremento-ca
    '''
    path_tokens = []
    longest = []
    for path in paths:
        fullpath = os.path.abspath(path)
        tokens = fullpath.split(os.sep)
        path_tokens.append(tokens)
        if len(tokens) > len(longest):
            longest = tokens

    for i in range(len(longest), 0, -1):
        lng = longest[0:i]
        results = []
        for path_token in path_tokens:
            result = all(path_token[ele] == lng[ele]
                         for ele in range(len(lng)))
            results.append(result)
        if all(results):
            result = os.path.join(
                *lng
            )  # on windows this makes the drive wrong, so add that back in
            if ':' in result:
                result = result.replace(':', ':\\')
            return result
    return None
