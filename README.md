# youtube-utilities
A collection of utilities that may be worth using!


# Apps
1. copyright-to-timestamps: Convert the text from the Youtube Studio copyright section into usable timestamps in the description! [doc](./docs/apps/copyright-to-timestamps.md)
```bash
python apps/copyright-to-timestamps.py copyrights.txt > timestamps.txt
```
2. timestamp-offsetter: Offset already established timestamps from somebody else by n seconds! [doc](./docs/apps/timestamp-offsetter.md)
```bash
python apps/timestamp-offsetter.py timestamps.txt "+369"
```
3. trim-tag-convert-video-audio: Take a bunch of videos, trim them, convert them to mp3, and tag them! [doc](./docs/apps/trim-tag-convert-video-audio.md)
```bash
python ./apps/trim-tag-convert-video-audio.py defaults-and-performances.yaml --socials-filepath ./socials.txt
```
4. resize-concat: Take a bunch of mismatched resolution / framerate videos, and concatenate them!
```bash
python ./apps/resize-concat.py list.txt --resolution "4k" --framerate 60
```
5. generate-thumbnails: Take a bunch of thumbnails from a video
```bash
python ./apps/generate-thumbnails.py movie.mp4 --output-dirpath ./thumbnails --sample 50 --keep 25
```


# Setup
```bash
pip install -r ./requirements.txt
```



# TODO:
1. combine into 1 app...