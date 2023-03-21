# yt-dlp-maxpath
A python script and a bash shell command to retry with maximum filename when encounter "File name too long" error with `yt-dlp` or `youtube-dl`. The maximum path have 6 characters buffer in case theoretically many fragmenet indexes and extension increment.

## Before:
    xb@dnxb:/tmp$ type -a youtube # Assume I have this bash shell function
    youtube is a function
    youtube () 
    { 
        yt-dlp --ffmpeg-location /home/xiaobai/Downloads/ffmpeg-master-latest-linux64-gpl/bin/ffmpeg -i -c --no-mtime -o './%(title)s-%(upload_date)s-%(id)s.%(ext)s' "$@"
    }

    xb@dnxb:/tmp$ youtube 'https://www.facebook.com/reel/725156119070036/?s=single_unit' # Trying to download will get error:
    [facebook:reel] Extracting URL: https://www.facebook.com/reel/725156119070036/?s=single_unit
    [facebook] Extracting URL: https://m.facebook.com/watch/?v=725156119070036&_rdr
    [facebook] 725156119070036: Downloading webpage
    [facebook] 725156119070036: Downloading MPD manifest
    [info] 725156119070036: Downloading 1 format(s): 2190447124459398v-1+3467337766834560a-1
    ERROR: unable to open for writing: [Errno 36] File name too long: "./😆นึกว่าเล่นโดดยางจะสูญพันธุ์ไปแล้ว ไม่คิดว่าจะได้เห็นเด็กยุคนี้เล่น วัยรุ่น 80',90' น้อยคนไม่เคยเล่น555 ｜ By วาไรตี้4แคว-20230207-725156119070036.f2190447124459398v-1.webm.part"

    ERROR: unable to open for writing: [Errno 36] File name too long: "./😆นึกว่าเล่นโดดยางจะสูญพันธุ์ไปแล้ว ไม่คิดว่าจะได้เห็นเด็กยุคนี้เล่น วัยรุ่น 80',90' น้อยคนไม่เคยเล่น555 ｜ By วาไรตี้4แคว-20230207-725156119070036.f3467337766834560a-1.m4a.part"

    xb@dnxb:/tmp$

## Change bash shell init script:
#### (You need remove all occurrences of `--ffmpeg-location /home/xiaobai/Downloads/ffmpeg-master-latest-linux64-gpl/bin/ffmpeg` if you don't specify ffmpeg, or replace with your ffmpeg path)
#### (You need change the path /home/xiaobai/Downloads/yt-dlp-maxpath/max_path.py to your downloaded script path)
#### (You need change yt-dlp to youtube-dl if you don't use yt-dlp)
    xb@dnxb:/tmp$ vim ~/.bash_aliases # Edit bash shell init script 
    
    function youtube() {
	    yt-dlp --ffmpeg-location /home/xiaobai/Downloads/ffmpeg-master-latest-linux64-gpl/bin/ffmpeg -i -c --no-mtime -o './%(title)s-%(upload_date)s-%(id)s.%(ext)s' "$@"
        if [ $? -eq 1 ]; then echo '[hole] Failed. Trying download with MAX path...';  yt_out="$(PYTHONIOENCODING=utf-8 yt-dlp --ffmpeg-location /home/xiaobai/Downloads/ffmpeg-master-latest-linux64-gpl/bin/ffmpeg -i -c --no-mtime -o './%(title)s-%(upload_date)s-%(id)s.%(ext)s' "$@" 2>&1 >/dev/null | python3 /home/xiaobai/Downloads/yt-dlp-maxpath/max_path.py)"; echo max path: "$yt_out", url: "$@"; yt-dlp --ffmpeg-location /home/xiaobai/Downloads/ffmpeg-master-latest-linux64-gpl/bin/ffmpeg -i -c --no-mtime -o "$yt_out"'-%(upload_date)s-%(id)s.%(ext)s' "$@"; fi
    }
    export -f youtube

    xb@dnxb:/tmp$ . ~/.bash_aliases # Refresh bash shell init script

## After:
    xb@dnxb:/tmp$ youtube 'https://www.facebook.com/reel/725156119070036/?s=single_unit'
    [facebook:reel] Extracting URL: https://www.facebook.com/reel/725156119070036/?s=single_unit
    [facebook] Extracting URL: https://m.facebook.com/watch/?v=725156119070036&_rdr
    [facebook] 725156119070036: Downloading webpage
    [facebook] 725156119070036: Downloading MPD manifest
    [info] 725156119070036: Downloading 1 format(s): 2190447124459398v-1+3467337766834560a
    ERROR: unable to open for writing: [Errno 36] File name too long: "./😆นึกว่าเล่นโดดยางจะสูญพันธุ์ไปแล้ว ไม่คิดว่าจะได้เห็นเด็กยุคนี้เล่น วัยรุ่น 80',90' น้อยคนไม่เคยเล่น555 ｜ By วาไรตี้4แคว-20230207-725156119070036.f2190447124459398v-1.webm.part"

    ERROR: unable to open for writing: [Errno 36] File name too long: "./😆นึกว่าเล่นโดดยางจะสูญพันธุ์ไปแล้ว ไม่คิดว่าจะได้เห็นเด็กยุคนี้เล่น วัยรุ่น 80',90' น้อยคนไม่เคยเล่น555 ｜ By วาไรตี้4แคว-20230207-725156119070036.f3467337766834560a.m4a.part"

    [hole] Failed. Trying download with MAX path...
    max path: 😆นึกว่าเล่นโดดยางจะสูญพันธุ์ไปแล้ว ไม่คิดว่าจะได้เห็นเด็กยุคนี้..., url: https://www.facebook.com/reel/725156119070036/?s=single_unit
    [facebook:reel] Extracting URL: https://www.facebook.com/reel/725156119070036/?s=single_unit
    [facebook] Extracting URL: https://m.facebook.com/watch/?v=725156119070036&_rdr
    [facebook] 725156119070036: Downloading webpage
    [facebook] 725156119070036: Downloading MPD manifest
        [info] 725156119070036: Downloading 1 format(s): 2190447124459398v-1+3467337766834560a-1
    [download] Destination: 😆นึกว่าเล่นโดดยางจะสูญพันธุ์ไปแล้ว ไม่คิดว่าจะได้เห็นเด็กยุคนี้...-20230207-725156119070036.f2190447124459398v-1.webm
    [download] 100% of    3.20MiB in 00:00:06 at 518.46KiB/s
    [download] Destination: 😆นึกว่าเล่นโดดยางจะสูญพันธุ์ไปแล้ว ไม่คิดว่าจะได้เห็นเด็กยุคนี้...-20230207-725156119070036.f3467337766834560a-1.m4a
    [download] 100% of  134.09KiB in 00:00:00 at 146.97KiB/s
    [Merger] Merging formats into "😆นึกว่าเล่นโดดยางจะสูญพันธุ์ไปแล้ว ไม่คิดว่าจะได้เห็นเด็กยุคนี้...-20230207-725156119070036.mkv"
    Deleting original file 😆นึกว่าเล่นโดดยางจะสูญพันธุ์ไปแล้ว ไม่คิดว่าจะได้เห็นเด็กยุคนี้...-20230207-725156119070036.f2190447124459398v-1.webm (pass -k to keep)
    Deleting original file 😆นึกว่าเล่นโดดยางจะสูญพันธุ์ไปแล้ว ไม่คิดว่าจะได้เห็นเด็กยุคนี้...-20230207-725156119070036.f3467337766834560a-1.m4a (pass -k to keep)
    xb@dnxb:/tmp$ 

