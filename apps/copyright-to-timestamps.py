'''
Author:      Chris Carl
Date:        2023-10-14
Email:       chrisbcarl@outlook.com

Description:
    Convert the text from the Youtube Studio copyright section into usable timestamps in the description!
    Also prints the ffmpeg command string to mute the offending sections.
    ex) mute two sections: between 5-10s and 15-20s:
        ffmpeg -i in.mp4 -vcodec copy -af "volume=enable='between(t,5,10)':volume=0, volume=enable='between(t,15,20)':volume=0" out.mp4

Updated:
    2023-11-08 - chriscarl - added the muted and ffmpeg commands
'''
# pylint: disable=(broad-except)

# stdlib imports
import os
import sys
import argparse
import traceback

# project imports
SCRIPT_FILEPATH = os.path.abspath(__file__)
LIBRARY_DIRPATH = os.path.join(os.path.dirname(SCRIPT_FILEPATH), '../')
if LIBRARY_DIRPATH not in sys.path:
    sys.path.append(LIBRARY_DIRPATH)
from library.media import timestamp_to_tuple, tpl_to_seconds, tpl_to_timestamp


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('-a',
                        '--any-territory',
                        action='store_true',
                        help='Count "Blocked in some territories" as well...')
    parser.add_argument('-p',
                        '--pad-zeros',
                        action='store_true',
                        help='Pad 00:00:01 if the max timestamp is 01:00:00')
    args = parser.parse_args()

    with open(args.input, encoding='utf-8') as r:
        lines = [
            line.strip() for line in r.read().splitlines() if line.strip()
        ]

    if 'content used' not in lines[0].lower():
        print('unknown format! expected content used in 1st line!')
        sys.exit(1)
    if 'impact on the video' not in lines[1].lower():
        print('unknown format! expected content used in 2nd line!')

    blocked = {}
    data = {}
    video_uses_this_songs_melody = None
    song, artist, start, stop, cpright = None, None, None, None, None
    tokens_count = -1
    idx = -1
    try:
        for idx, line in enumerate(lines[2:]):
            if all(ele is not None
                   for ele in [song, artist, start, stop, cpright]):
                song, artist, start, stop, cpright = None, None, None, None, None
                hidden = False

            lowline = line.lower()
            if song is None:
                song = line
                hidden = 'hidden' in lowline  # Metadata is hidden, as the content in question has not been made publicly available by its provider.
                if hidden:
                    song, artist = 'ID', 'ID'
            elif artist is None:
                if "Video uses this song's melody" in line:
                    if video_uses_this_songs_melody is None:
                        video_uses_this_songs_melody = input(
                            f'video uses this songs melody detected... song {song!r}; artist name? '
                        )
                    artist = video_uses_this_songs_melody
                else:
                    artist = line
            elif start is None:
                colonIdx = line.index(':')
                timestamps = line[colonIdx + 1:]
                start, stop = timestamps.split('-')
                start, stop = timestamp_to_tuple(start), timestamp_to_tuple(
                    stop)
            elif cpright is None:
                noimpact = 'no impact' in lowline  # No impact
                cannot = 'video cannot be seen' in lowline  # Video cannot be seen or monetized
                blocked_all = 'blocked in all' in lowline  # Blocked in all territories
                blocked_some = 'blocked in some' in lowline  # Blocked in some territories

                if hidden:
                    print('shit')

                if noimpact:
                    data[start] = f'{artist} - {song}'
                    cpright = False
                    continue

                if cannot:
                    continue  # this line is worthless, have to look at the next

                if blocked_all:
                    blocked[(start, stop)] = f'{artist} - {song}'
                    cpright = True
                elif blocked_some:
                    if args.any_territory:
                        blocked[(start, stop)] = f'{artist} - {song}'
                        cpright = True
                    else:
                        data[start] = f'{artist} - {song}'
                        cpright = False

    except Exception:
        print('exception in line', idx + 2 + 1)
        traceback.print_exc()
        sys.exit(1)

    print('Timestamps from copyright:')
    for tpl in sorted(data):
        timestamp = tpl_to_timestamp(*tpl, pad_zeros=args.pad_zeros)
        artist_song = data[tpl]
        print(f'[{timestamp}] {artist_song}')

    print('\nmuted:')
    ffmpeg_mute_between = []
    for timestamp_tpl in sorted(blocked):
        artist_song = blocked[timestamp_tpl]
        start, stop = timestamp_tpl
        start_secs, stop_secs = tpl_to_seconds(*start), tpl_to_seconds(*stop)
        start_ts, stop_ts = tpl_to_timestamp(
            *start, pad_zeros=args.pad_zeros), tpl_to_timestamp(
                *stop, pad_zeros=args.pad_zeros)
        print(f'[{start_ts}] to [{stop_ts}] {artist_song}')
        ffmpeg_mute_between.append((start_secs, stop_secs))

    print('\nffmpeg filter:')
    ffmpeg_filter = ', '.join(
        f"volume=enable='between(t,{start},{stop})':volume=0"
        for start, stop in ffmpeg_mute_between)
    print(ffmpeg_filter)
