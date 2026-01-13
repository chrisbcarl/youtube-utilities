# resize-concat
Take a bunch of mismatched resolution / framerate videos, and concatenate them!


# Usage
1. create a `list.txt` similar to [list.txt](../list.yaml)
2. Invoke the following:
```bash
python ./apps/resize-concat.py list.txt --resolution "4k" --framerate 60
```
