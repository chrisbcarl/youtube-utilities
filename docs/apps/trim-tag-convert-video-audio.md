# trim-tag-convert-video-audio
Take a bunch of videos, trim them, convert them to mp3, and tag them!


# Usage
1. combine any videos together if they are in separate pieces
2. create a `defaults.yaml` similar to [defaults.yaml](../defaults.yaml)
3. create a `performances.yaml` similar to [performances.yaml](../performances.yaml)
    - **OPTIONALLY:** combine the 2 into one file
4. Invoke the following:
```bash
# given a bunch of yamls, combine them together, then iterate through the indexes alphanumerically.
python ./apps/trim-tag-convert-video-audio.py defaults-and-performances.yaml

python ./apps/trim-tag-convert-video-audio.py defaults.yaml performances.yaml
```
