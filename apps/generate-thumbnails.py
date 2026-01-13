'''
Author:      Chris Carl
Date:        2024-05-11
Email:       chrisbcarl@outlook.com

Description:
    Take a bunch of thumbnails from a video

Example:
    python {filepath} --output-dirpath --sample 69 --keep 13
'''
# noqa: E501
# pylint: disable=(broad-exception-caught)
# stdlib imports
from __future__ import absolute_import, division
import os
import sys
import shutil
import logging
import argparse
import multiprocessing

# 3rd party imports

# project imports
SCRIPT_FILEPATH = os.path.abspath(__file__)
LIBRARY_DIRPATH = os.path.join(os.path.dirname(SCRIPT_FILEPATH), '../')
if LIBRARY_DIRPATH not in sys.path:
    sys.path.append(LIBRARY_DIRPATH)
from library.stdlib import NiceArgparseFormatter
from library.ffmpeg import generate_thumbnails

__doc__ = __doc__.format(
    filepath=__file__,
    shell_multiline='`' if sys.platform == 'win32' else '\\')
LOGGER = logging.getLogger(__name__)
MAX_WORKERS = multiprocessing.cpu_count()
DEFAULT_SAMPLES = 250
DEFAULT_KEEP = 50


def main(
    video_filepath,
    output_dirpath=None,
    samples=DEFAULT_SAMPLES,
    keep=DEFAULT_KEEP,
):
    # type: (str, str, int, int) -> int
    if output_dirpath is None:
        output_dirpath = os.path.join(os.path.dirname(video_filepath),
                                      'thumbnails')
    os.makedirs(output_dirpath, exist_ok=True)
    topic = f'THUMBNAILS - "{video_filepath}" -> "{output_dirpath}" (samples=250, keep=50)'
    LOGGER.info('%s - STARTING', topic)
    thumbnail_filepaths = generate_thumbnails(video_filepath,
                                              output_dirpath,
                                              samples=samples,
                                              keep=keep)
    for thumbnail_filepath in thumbnail_filepaths[0:3]:
        shutil.copy(thumbnail_filepath, os.path.dirname(video_filepath))
    LOGGER.info('%s - PASSED', topic)
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=NiceArgparseFormatter)
    parser.add_argument('video_filepath', type=str, help='video filepath')
    parser.add_argument(
        '-o',
        '--output-dirpath',
        type=str,
        help=
        'either explicit or will be saved to thumbnails folder at the provided video filepath dirpath'
    )
    parser.add_argument('-s',
                        '--samples',
                        type=int,
                        default=DEFAULT_SAMPLES,
                        help='how many to take?')
    parser.add_argument(
        '-k',
        '--keep',
        type=int,
        default=DEFAULT_KEEP,
        help='how many of the samples to keep? set equal to keep all of them')
    parser.add_argument('-ll',
                        '--log-level',
                        type=str,
                        default='INFO',
                        help='log level plz?')

    args = parser.parse_args()

    if args.log_level == 'INFO':
        log_fmt = '%(message)s'
    else:
        log_fmt = '%(asctime)s - %(levelname)10s - %(name)s - %(message)s'
    logging.basicConfig(level=args.log_level, format=log_fmt)

    try:
        return_code = main(
            args.video_filepath,
            output_dirpath=args.output_dirpath,
            samples=args.samples,
            keep=args.keep,
        )
    except KeyboardInterrupt:
        LOGGER.warning('ctrl + c detected')
        return_code = 2

    sys.exit(return_code)
