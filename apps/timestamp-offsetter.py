'''
Author:      Chris Carl
Date:        2023-10-14
Email:       chrisbcarl@outlook.com

Description:
    Offset already established timestamps from somebody else by n seconds!
'''
# pylint: disable=(broad-except)

# stdlib imports
from __future__ import division
import sys
import re
import argparse
import traceback
import datetime


TIMESTAMP_REGEX = re.compile(r'(?P<timestamp>\d?\d?\:?\d?\d?\:?\d?\d?)(?P<spacing>\s?\-?\s?)(?P<song>[\w\s\'\-\_\&\@]+)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('offset', type=str, help='seconds to offset, denoted by + or -')
    args = parser.parse_args()

    if not args.offset.startswith('+') and not args.offset.startswith('-'):
        raise ValueError('offset must be formatted like +10 or -10! provided %r' % args.offset)
    operand = args.offset[0]
    value = int(args.offset[1:])
    if operand == '-':
        value = -value

    with open(args.input, encoding='utf-8') as r:
        lines = [line.strip() for line in r.read().splitlines() if line.strip()]

    if 'timestamps' not in lines[0].lower():
        print('unknown format! expected "timestamps" in 1st line!')
        sys.exit(1)

    data = {}
    timestamp, song = None, None
    tokens_count = -1
    try:
        for l, line in enumerate(lines[1:]):
            mo = TIMESTAMP_REGEX.match(line)
            if not mo:
                raise ValueError('line %d is does not match timestamp regex!' % (l + 1))
            groups = mo.groupdict()
            timestamp, song = groups['timestamp'], groups['song']
            colonIdx = line.index(':')
            firstTimestamp = timestamp.split('-')[0].strip()
            h, m, s = None, None, None
            tokens = firstTimestamp.split(':')
            if len(tokens) == 3:
                h, m, s = int(tokens[0]), int(tokens[1]), int(tokens[2])
            elif len(tokens) == 2:
                h, m, s = 0, int(tokens[0]), int(tokens[1])
            elif len(tokens) == 1:
                h, m, s = 0, 0, (tokens[0])
            tokens_count = max([tokens_count, len(tokens)])
            timestamp = (h, m, s)

            data[timestamp] = song
    except Exception:
        print('exception in line', l + 1)
        traceback.print_exc()
        sys.exit(1)

    if tokens_count == 3:
        fmt = '{:02d}:{:02d}:{:02d}'
    elif tokens_count == 2:
        fmt = '{:02d}:{:02d}'
    elif tokens_count == 1:
        fmt = '{:02d}'

    for tpl in sorted(data):
        h, m, s = tpl
        td = datetime.timedelta(hours=h, minutes=m, seconds=s)
        total_seconds = int(td.total_seconds())
        total_seconds += value

        h = total_seconds // 3600
        m = (total_seconds // 60) % 60
        s = total_seconds % 60

        if tokens_count == 3:
            tokens = (h, m, s)
        elif tokens_count == 2:
            tokens = (m, s)
        elif tokens_count == 1:
            tokens = (s,)
        print('%s - %s' % (fmt.format(*tokens), data[tpl]))
