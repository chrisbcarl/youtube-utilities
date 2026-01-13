'''
Author:      Chris Carl
Date:        2023-10-15
Email:       chrisbcarl@outlook.com

Description:
    Wraps mp3 tagging utils
'''
# stdlib imports
import os
import eyed3
import logging
import re

# third party
from eyed3.id3.frames import ImageFrame

# project imports
from .stdlib import get_value_from_dicts
from .media import ARTIST_DB

LOGGER = logging.getLogger(__name__)
ENCODED_BY = 'chriscarl.com'
COMMENT = '\n'.join([
    'PURELY FAN DRIVEN--NOT FOR PROFIT, SALE, OR MONETARY COMPENSATION',
    'Recorded/converted/EQed by chriscarl.com',
])
YEAR_REGEX = re.compile(r'(\d\d\d\d)')


def get_mp3_tags_from_filepath(filepath):
    # type: (str) -> dict
    '''
    Description:
        given filepaths like:
            # Madeon - Good Faith DJ Set @ 45 East 2022 [Full Concert 4K60] (320 kbps).mp3
            # San Holo - bb u ok? tour @ Frost Amphitheater 2022 [Full Concert 4K60] (320 kbps).mp3
        autogenerate the tags as a dict
    Returns:
        dict
    '''
    basename = os.path.basename(filepath)
    filename = os.path.splitext(basename)[0]

    title = filename.split('[')[0].strip()
    artist, setname, album = None, None, None
    try:
        artist_setname = filename.split('@')  # 2 tokens
        artist_setname, rest = artist_setname  # Madeon - Good Faith DJ Set @ 45 East 2022 [Full Concert 4K60] (320 kbps)
        tokens = artist_setname.split('-')
        if len(tokens) == 2:
            artist, setname = tokens
        else:
            artist = tokens[0]
            setname = 'Live Set'
        artist = artist.strip()
        album = setname.strip()
    except Exception:
        LOGGER.exception('filepath "%s" couldnt get the artist or setname')

    location, year = None, None
    try:
        location_year = rest.split('[')  # 2 tokens
        year = YEAR_REGEX.search(location_year)
        year = year.groups()[0]
        location = location_year.replace(year, '').strip()
    except Exception:
        LOGGER.exception('filepath "%s" couldnt get location or year!', filepath)

    genre = ARTIST_DB.get(artist, {}).get('genre')

    LOGGER.debug('filepath:          "%s"', filepath)
    LOGGER.debug('    title:         %s', title)
    LOGGER.debug('    artist:        %s', artist)
    LOGGER.debug('    setname:       %s', setname)
    LOGGER.debug('    album:         %s', album)
    LOGGER.debug('    location:      %s', location)
    LOGGER.debug('    location_year: %s', location_year)
    LOGGER.debug('    year:          %s', year)
    LOGGER.debug('    genre:         %s', genre)

    kwargs = dict(
        title=title,
        artist=artist,
        album=album,
        year=year,
        genre=genre,
    )
    return kwargs


def tag_mp3(filepath, auto_detect=True, title=None, artist=None, album=None, year=None, genre=None, track_num=1, encoded_by=ENCODED_BY, comment=COMMENT, cover=None):
    # type: (str, bool, str, str, str, int, str, int, str, str, str) -> None
    '''
    Description:
        either provide filepaths like these, or supply the tags directly:
            # Madeon - Good Faith DJ Set @ 45 East 2022 [Full Concert 4K60] (320 kbps).mp3
            # San Holo - bb u ok? tour @ Frost Amphitheater 2022 [Full Concert 4K60] (320 kbps).mp3
    Returns:
        None
    '''
    kwargs = dict(
        title=title,
        artist=artist,
        album=album,
        year=year,
        genre=genre,
        track_num=track_num,
        encoded_by=encoded_by,
        comment=comment,
        cover=cover,
    )
    if auto_detect:
        filepath_kwargs = get_mp3_tags_from_filepath(filepath)
    else:
        filepath_kwargs = {}

    audiofile = eyed3.load(filepath)
    if audiofile.tag is None:
        audiofile.initTag()
    # https://eyed3.readthedocs.io/en/latest/eyed3.id3.html?highlight=encoding_date#module-eyed3.id3.tag
    keys = ['title', 'artist', 'album', 'genre', 'encoded_by', 'track_num']
    for key in keys:
        value = get_value_from_dicts(key, kwargs, filepath_kwargs)
        if value is None:
            continue
        setattr(audiofile.tag, key, value)

    year = get_value_from_dicts('year', kwargs, filepath_kwargs)
    if year is not None:
        audiofile.tag.recording_date = year

    comment = get_value_from_dicts('comment', kwargs, filepath_kwargs)
    if comment is not None:
        audiofile.tag.comments.set(comment)

    # https://stackoverflow.com/questions/38510694/how-to-add-album-art-to-mp3-file-using-python-3
    cover = get_value_from_dicts('cover', kwargs, filepath_kwargs)
    if cover is not None:
        ext = os.path.splitext(cover)[1]
        if ext.lower() not in ['.jpeg', '.jpg']:
            raise OSError('must provide cover in jpeg format!')
        with open(cover, 'rb') as rb:
            cover = rb.read()
        audiofile.tag.images.set(ImageFrame.FRONT_COVER, cover, 'image/jpeg')

    audiofile.tag.save()
