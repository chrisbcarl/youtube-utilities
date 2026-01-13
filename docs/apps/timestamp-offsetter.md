# Usage - timestamp-offsetter
1. take something that looks like this and save it in a file like [./docs/timestamps.txt](./docs/timestamps.txt)
```log
Timestamps
01:01:10 - Heavy with Hoping
01:05:05 - Piano Solo
01:06:01 - Borealis
01:08:47 - Miracle
01:13:44 - Shelter x All My Friends
```
2. Figure out how much offset you want in seconds, ex: -60 +120, etc
3. run the following to get nice output
```bash
python apps/timestamp-offsetter.py timestamps.txt "-369"
python apps/timestamp-offsetter.py timestamps.txt "+369"
```
```log
00:55:01 - Heavy with Hoping
00:58:56 - Piano Solo
00:59:52 - Borealis
01:02:38 - Miracle
01:07:35 - Shelter x All My Friends
```
