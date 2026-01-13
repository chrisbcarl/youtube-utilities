'''
Author:      Chris Carl
Date:        2023-10-27
Email:       chrisbcarl@outlook.com

Description:
    Take a bunch of videos of different resolutions/framerates,
    homogenize them
    concat them

Example:
    python {filepath} {shell_multiline}
        list.txt 3840 60 {shell_multiline}
'''
# stdlib imports
from __future__ import absolute_import, division
import os
import sys
import re
import logging
import argparse
import subprocess
from collections import OrderedDict

# 3rd party imports

# project imports
SCRIPT_FILEPATH = os.path.abspath(__file__)
LIBRARY_DIRPATH = os.path.join(os.path.dirname(SCRIPT_FILEPATH), '../')
if LIBRARY_DIRPATH not in sys.path:
    sys.path.append(LIBRARY_DIRPATH)
from library.stdlib import NiceArgparseFormatter


__doc__ = __doc__.format(filepath=__file__, shell_multiline='`' if sys.platform == 'win32' else '\\')
LOGGER = logging.getLogger(__name__)
RESOLUTIONS = {
    '720p': 1280,
    '1080p': 1920,
    '2k': 2560,
    '4k': 3840
}
FILE_REGEX = re.compile(r"file '(.*)'")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=NiceArgparseFormatter)
    parser.add_argument('list_txt', type=str, help='list.txt formatted as "file \'filepath\'\\nfile \'filepath\'\\n"')
    parser.add_argument('--resolution', type=str, default='4k', choices=RESOLUTIONS, help='resolution?')
    parser.add_argument('--framerate', type=str, default=60, help='framerate?')
    parser.add_argument('--output', type=str, help='explicit output_filepath?')
    parser.add_argument('-ll', '--log-level', type=str, default='INFO', help='log level plz?')

    args = parser.parse_args()

    if args.log_level == 'INFO':
        log_fmt = '%(message)s'
    else:
        log_fmt = '%(asctime)s - %(levelname)10s - %(name)s - %(message)s'
    logging.basicConfig(level=args.log_level, format=log_fmt)

    LOGGER.info('starting...')

    LOGGER.info('analyzing...')
    resolution = RESOLUTIONS[args.resolution]
    filepaths = OrderedDict()
    ext = None
    dirpath = None
    list_txt_dirpath = os.path.abspath(os.path.dirname(args.list_txt))
    with open(args.list_txt, encoding='utf-8') as r:
        list_txt = r.read()
        for l, line in enumerate(list_txt.splitlines()):
            stripped = line.strip()
            if not stripped:
                continue
            mo = FILE_REGEX.match(stripped)
            if not mo:
                raise RuntimeError(f'line {l} of "{args.list_txt}" doesnt match expected format!')
            filepath = mo.groups()[0]
            filepath = os.path.join(list_txt_dirpath, filepath)
            LOGGER.info('line %d: "%s"', l, filepath)
            left = os.path.splitext(filepath)[0]
            if ext is None:
                ext = os.path.splitext(filepath)[1]
                dirpath = os.path.dirname(filepath)
                if not args.output:
                    args.output = os.path.join(dirpath, f'concatenated{ext}')
                else:
                    args.output = os.path.abspath(args.output)
                LOGGER.info('setting output file to "%s"', args.output)
            renamed = f'{left}-{resolution}-{args.framerate}fps{ext}'
            filepaths[filepath] = renamed

    LOGGER.info('preparing...')
    converted_list_filepath = f'{args.list_txt}-converted'
    with open(converted_list_filepath, 'w', encoding='utf-8') as w:
        for value in filepaths.values():
            w.write(f"file '{value}'\n")

    LOGGER.info('converting...')
    for f, filepath in enumerate(filepaths.keys()):
        renamed = filepaths[filepath]
        LOGGER.info('converting %d / %d "%s" @ %s %sfps', f + 1, len(filepaths), filepath, args.resolution, args.framerate)

        cmd = [
            # ffmpeg -hide_banner -h encoder=hevc_nvenc
            'ffmpeg', '-y',
            '-i', filepath,
            # can probably flip this to get 1080 instead of 1920
            '-vf', f'scale={resolution}:-2,setsar=1:1,fps={args.framerate}',
            '-c:v', 'hevc_nvenc',
            # https://superuser.com/questions/1296374/best-settings-for-ffmpeg-with-nvenc
            # https://superuser.com/a/1667740 - the hevc_nvenc non existent flags
            '-rc', 'constqp', '-qp', '24', '-preset', 'p7', '-tune', 'hq', '-rc-lookahead', '4',
            '-c:a', 'copy',
            renamed
        ]
        command = subprocess.list2cmdline(cmd)
        LOGGER.info(command)
        subprocess.check_call(cmd)

    LOGGER.info('concatting...')
    cmd = [
        'ffmpeg', '-y',
        '-safe', '0',
        '-f', 'concat',
        '-i', converted_list_filepath,
        '-c', 'copy',
        args.output
    ]
    command = subprocess.list2cmdline(cmd)
    LOGGER.info(command)
    subprocess.check_call(cmd)

    LOGGER.info('done!')
