'''
Author:      Chris Carl
Date:        2023-10-15
Email:       chrisbcarl@outlook.com

Description:
    Take a bunch of videos, trim them, convert them to mp3, and tag them!

Example:
    python {filepath} {shell_multiline}
        docs/defaults.yaml docs/performances.yaml {shell_multiline}
        --sequential
'''
# pylint: disable=(broad-exception-caught)
# stdlib imports
from __future__ import absolute_import, division
import os
import sys
import json
import shutil
import logging
import argparse
import multiprocessing
import concurrent.futures
from typing import List

# 3rd party imports
import yaml

# project imports
SCRIPT_FILEPATH = os.path.abspath(__file__)
LIBRARY_DIRPATH = os.path.join(os.path.dirname(SCRIPT_FILEPATH), '../')
if LIBRARY_DIRPATH not in sys.path:
    sys.path.append(LIBRARY_DIRPATH)
import library
from library.stdlib import NiceArgparseFormatter, indent, run_subprocess, find_common_directory
from library.media import Video, ARTIST_DB
from library.ffmpeg import trim_args, mp3_args, generate_thumbnails, generate_gif
from library.mp3 import tag_mp3

__doc__ = __doc__.format(
    filepath=__file__,
    shell_multiline='`' if sys.platform == 'win32' else '\\')
LOGGER = logging.getLogger(__name__)
MAX_WORKERS = multiprocessing.cpu_count()
with open(os.path.join(os.path.dirname(library.__file__),
                       'youtube_description.template'),
          encoding='utf-8') as r:
    YOUTUBE_DESCRIPTION_TEMPLATE = r.read()
MODES = ['trim', 'mp3', 'tag', 'thumb', 'gif', 'market', 'yt']


def pipeline(video, modes=None):
    # type: (Video, list) -> int
    modes = modes or MODES
    os.makedirs(video.output_dirpath, exist_ok=True)

    exit_code = 0
    if 'trim' in modes:
        topic = f'00 - TRIMMING - {video}'
        video_filepath = os.path.abspath(
            os.path.join(video.output_dirpath, video.video_filename))
        if not (video.start or video.stop):
            LOGGER.warning('%s - SKIPPING', topic)
            os.makedirs(video.output_dirpath, exist_ok=True)
            video_filepath = os.path.abspath(
                os.path.join(video.output_dirpath, video.video_filename))
            shutil.copy2(video.filepath, video_filepath)
        else:
            LOGGER.info('%s - STARTING', topic)
            args = trim_args(video.filepath, video_filepath, video.start,
                             video.stop)
            exit_code, _, _ = run_subprocess(args, video_filepath)
            if exit_code != 0:
                LOGGER.error('%s - FAILED', topic)
                return exit_code
            LOGGER.info('%s - PASSED', topic)

    # # video tagging causes conversion to go bad, not sure why.
    # topic = f'02 - {video} - video tagging'
    # LOGGER.info('%s - STARTING', topic)
    # tag_mp3(
    #     video_filepath,
    #     auto_detect=False,
    #     title=video.title,  # thats the only thing we can try
    # )
    # LOGGER.info('%s - PASSED', topic)

    if 'mp3' in modes:
        topic = f'02 - MP3 - {video}'
        LOGGER.info('%s - STARTING', topic)
        audio_filepath = os.path.abspath(
            os.path.join(video.output_dirpath, video.audio_filename))
        args = mp3_args(video_filepath,
                        audio_filepath,
                        bitrate=video.bitrate,
                        sampling_frequency=48000)
        exit_code, _, _ = run_subprocess(args, audio_filepath)
        if exit_code != 0:
            LOGGER.error('%s - FAILED', topic)
            return exit_code
        LOGGER.info('%s - PASSED', topic)

    if 'tag' in modes:
        topic = f'03 - TAGGING - {video}'
        LOGGER.info('%s - STARTING', topic)
        tag_mp3(
            audio_filepath,
            auto_detect=False,
            title=video.title,
            artist=video.artist,
            album=video.album,
            year=video.year,
            genre=video.genre,
            track_num=video.track_num,
            cover=video.cover,
        )
        LOGGER.info('%s - PASSED', topic)

    if 'thumb' in modes:
        topic = f'04 - THUMBNAILS - {video}'
        LOGGER.info('%s - STARTING', topic)
        thumbnail_dirpath = os.path.join(video.output_dirpath, 'thumbnails')
        thumbnail_filepaths = generate_thumbnails(video_filepath,
                                                  thumbnail_dirpath,
                                                  samples=250,
                                                  keep=50)
        for thumbnail_filepath in thumbnail_filepaths[0:3]:
            shutil.copy(thumbnail_filepath, video.output_dirpath)
        LOGGER.info('%s - PASSED', topic)

    if 'gif' in modes:
        topic = f'05 - GIF - {video}'
        LOGGER.info('%s - STARTING', topic)
        gif_filepath = os.path.join(video.output_dirpath,
                                    f'{video.video_filename}.gif')
        passed = generate_gif(thumbnail_filepaths,
                              gif_filepath,
                              delay=10,
                              megabytes=16)
        if passed:
            LOGGER.info('%s - PASSED', topic)
        else:
            LOGGER.error('%s - FAILED', topic)
            exit_code = 1

    LOGGER.info('%s - FINISHED!!!', video)
    return exit_code


def trim_tag_convert_marketing_yt(
        *yamls,
        confirm=False,
        sequential=False,
        marketing_filepath=None,
        cwd=os.getcwd(),
        modes=None,
):
    # type: (list, bool, bool, str, str, list) -> int
    modes = modes or MODES

    manifests = []
    for yaml_filepath in yamls:
        yaml_filepath = os.path.abspath(yaml_filepath)
        with open(yaml_filepath, encoding='utf-8') as r:
            man = yaml.safe_load(r)
        man['defaults']['manifest_filepath'] = yaml_filepath
        man['defaults']['manifest_basename'] = os.path.basename(yaml_filepath)
        man['defaults']['manifest_dirpath'] = os.path.dirname(yaml_filepath)
        man['defaults']['manifest_filename'] = os.path.splitext(
            os.path.basename(yaml_filepath))[0]
        manifests.append(man)

    # absorb all yamls / combine them
    manifest = dict(defaults={}, performances=[])
    for man in manifests:
        man_defaults = man.get('defaults', {})
        manifest['defaults'].update(man_defaults)
        man_performances = man.get('performances', [])
        manifest['performances'].extend(man_performances)

    problems = []

    # comb through all the metadata
    default_video = Video(**manifest['defaults'])
    videos = []
    for p, performance in enumerate(manifest['performances']):
        try:
            video = Video.from_other(default_video, **performance)
            videos.append(video)
        except Exception as e:
            problems.append(
                f'performance idx {p} is no good thanks to exception: "{e}"!')

    for v, video in enumerate(videos):
        if video.track_num is not None:
            continue
        video.track_num = v + 1

    # let the user know these will be the outputs in a tree
    LOGGER.info('proposed output tree will be as follows:')
    for v, video in enumerate(videos):
        try:
            LOGGER.info('\n%s', video.verbose())
            LOGGER.info(
                '    socials:\n%s',
                indent(json.dumps(ARTIST_DB.get(video.artist, {}), indent=2),
                       count=2))
        except Exception as e:
            problems.append(
                f'video idx {v} is no good thanks to exception: "{e}"!')

    # if any tags would be missing, tell the UserWarning
    for video in videos:
        for problem in video.problems():
            problems.append(f'{problem} in "{video.filepath}"')

    if problems:
        if confirm:
            raise RuntimeError(
                'problems were detected! you dont want to confirm this!')
        for problem in problems:
            LOGGER.error('PROBLEM: %s', problem)

    if not confirm:
        try:
            print('\n\n')
            print('videos:', len(videos))
            print('modes: ', modes)
            yes = input(f'does this look right (y/n)? ').strip().lower()
            if not yes.startswith('y'):
                LOGGER.warning('cancelling!')
                return 2
        except KeyboardInterrupt:
            print('')  # since input did a carriage return
            LOGGER.warning('cancelling!')
            return 2

    # run the pipeline
    return_code = None
    if sequential:
        LOGGER.warning('running in sequential mode!')
        for video in videos:
            exit_code = pipeline(video, modes=modes)
            if exit_code != 0:
                return_code = exit_code
                break
    else:
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=MAX_WORKERS) as executor:
            # Start the load operations and mark each future with its URL
            future_to_exit_code = {
                executor.submit(pipeline, video, modes=modes): video
                for video in videos
            }
            for future in concurrent.futures.as_completed(future_to_exit_code):
                exit_code = -1
                video = future_to_exit_code[future]
                try:
                    exit_code = future.result()
                    return_code = exit_code
                except Exception:
                    LOGGER.exception('%r exception!', video)
                    return_code = 1
                    break
                else:
                    if exit_code != 0:
                        LOGGER.error('%s failed with exit code %d!', video,
                                     exit_code)
                    else:
                        LOGGER.info('%s succeeded with exit code %d!', video,
                                    exit_code)

    if return_code != 0:
        return return_code

    if 'market' in modes:
        LOGGER.info('generating the marketing text!')
        if marketing_filepath is None:
            common_directory = find_common_directory(
                [video.output_dirpath for video in videos])
            if not common_directory:
                common_directory = cwd
            marketing_filepath = os.path.abspath(
                os.path.join(common_directory, 'marketing.txt'))
        dirname = os.path.dirname(marketing_filepath)
        os.makedirs(dirname, exist_ok=True)

        socials_lines = []
        for video in videos:
            socials_lines.append(video.artist)
            socials_lines.append(indent('socials:', count=1))
            artist_dict = ARTIST_DB.get(video.artist, {})
            for entry in ['twi', 'ins', 'mov', 'mp3', 'ytb']:
                line = indent(f'{entry}: {artist_dict.get(entry, "???")}',
                              count=2)
                socials_lines.append(line)
            socials_lines.append('')
            socials_lines.append(indent('publish request:', count=1))
            socials_lines.append(
                f"Hey {video.artist}, I loved your set at {video.album} and I managed to capture the whole thing! I'd like your permission to post, planning on going public Friday afternoon. If you'd rather I take it down or I send you the source files so you can release it yourself thats ok too. Thanks!"
            )
            socials_lines.append(indent('marketing post:', count=1))
            socials_lines.append(
                f"@{video.artist} your set had so much energy--there was a whole crowd stage right that knew all the words, it was infectious! Second to last song had me bopping and weaving, I loved this set!\n\nhttps://youtube-link.com"
            )
            socials_lines.append('\n')
        with open(marketing_filepath, 'w', encoding='utf-8') as w:
            w.write('\n'.join(socials_lines))
        LOGGER.info('wrote socials text at "%s"!', marketing_filepath)

    if 'yt' in modes:
        LOGGER.info('generating the youtube text!')
        for video in videos:
            youtube_filepath = os.path.join(video.output_dirpath,
                                            'youtube.txt')
            with open(youtube_filepath, 'w', encoding='utf-8') as w:
                artist_dict = ARTIST_DB.get(video.artist, {})
                all_commentary = ''
                commentary = '\n'.join(
                    ele.strip() for ele in
                    video.commentary.splitlines()) if video.commentary else ''
                additional_commentary = '\n'.join(
                    ele.strip()
                    for ele in video.additional_commentary.splitlines(
                    )) if video.additional_commentary else ''
                if video.commentary and video.additional_commentary:
                    all_commentary = f'\n{additional_commentary}\n{commentary}'
                elif video.commentary and not video.additional_commentary:
                    all_commentary = f'\n{commentary}'
                elif not video.commentary and video.additional_commentary:
                    all_commentary = f'\n{additional_commentary}'
                timestamps = ''
                if video.timestamps:
                    timestamps = '\n' + "\n".join(
                        ele.strip() for ele in video.timestamps.splitlines()
                        if ele.strip())
                content = YOUTUBE_DESCRIPTION_TEMPLATE.format(
                    artist=video.artist,
                    twi=artist_dict.get('twi', '???'),
                    ins=artist_dict.get('ins', '???'),
                    mov=video.mov or '???',
                    mp3=video.mp3 or '???',
                    ytb=video.ytb or '???',
                    all_commentary=all_commentary,
                    venue=video.venue,
                    city=video.city,
                    state=video.state,
                    date=video.date,
                    video_stats=video.video_stats,
                    timestamps=timestamps,
                )
                w.write(content)
            LOGGER.info('wrote youtube text at "%s"!', youtube_filepath)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=NiceArgparseFormatter)
    parser.add_argument(
        'yamls',
        type=str,
        nargs='+',
        default=[],
        help='YAML files that may contain [defaults] or [performances]')
    parser.add_argument(
        '-c',
        '--confirm',
        action='store_true',
        help=
        'do you want to skip confirmation and pre-confirm before seeing the output preview?'
    )
    parser.add_argument(
        '-s',
        '--sequential',
        action='store_true',
        help='would you rather execute sequentially rather than concurrently?')
    parser.add_argument('-ll',
                        '--log-level',
                        type=str,
                        default='INFO',
                        help='log level plz?')
    parser.add_argument(
        '-mf',
        '--marketing-filepath',
        type=str,
        help='an explicit place to put your marketing text guidance file')
    parser.add_argument('-m',
                        '--modes',
                        type=str,
                        nargs='+',
                        choices=MODES,
                        default=MODES,
                        help='only generate the following modes')

    args = parser.parse_args()

    if args.log_level == 'INFO':
        log_fmt = '%(message)s'
    else:
        log_fmt = '%(asctime)s - %(levelname)10s - %(name)s - %(message)s'
    logging.basicConfig(level=args.log_level, format=log_fmt)

    try:
        return_code = trim_tag_convert_marketing_yt(
            *args.yamls,
            confirm=args.confirm,
            sequential=args.sequential,
            marketing_filepath=args.marketing_filepath,
            modes=args.modes,
        )
    except KeyboardInterrupt:
        LOGGER.warning('ctrl + c detected')
        return_code = 2

    sys.exit(return_code)


if __name__ == '__main__':
    main()
