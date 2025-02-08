import sys, os, traceback
import pathlib
from pathlib import PurePath

from dateutil.parser import parse

from termcolor import cprint
import colorama
from colorama import Fore
BOLD_ONLY = ['bold']
colorama.init() # Windows need this

HIGHER_RED = Fore.LIGHTRED_EX

import platform
plat = platform.system().lower()
if ('window' in plat) or plat.startswith('win'):
    # Darwin should treat as Linux
    IS_WIN = True
    # https://stackoverflow.com/questions/16755142/how-to-make-win32-console-recognize-ansi-vt100-escape-sequences
    # Even though ANSI escape sequence can be enable via `REG ADD HKCU\CONSOLE /f /v VirtualTerminalLevel /t REG_DWORD /d 1`
    # But since this is not big deal to hide logo testing for this project, so no need.
    ANSI_CLEAR = '\r' # Default cmd settings not support ANSI sequence
    ANSI_END_COLOR = ''
    ANSI_BLUE = ''
else:
    IS_WIN = False
    ANSI_CLEAR = '\r\x1b[0m\x1b[K'
    ANSI_END_COLOR = '\x1b[0m\x1b[K'
    ANSI_BLUE = '\x1b[1;44m'

# MAX_PATH 260 need exclude 1 terminating null character <NUL>
# if prefix \\?\ + abspath to use Windows extented-length(i.e. in my case, individual filename/dir can use full 259, no more 259 is fit full path), then the MAX_PATH is 259 - 4 = 255
#[DEPRECATED] no more 259 since always -el now AND Windows 259 - \\?\ == 255 normal Linux
WIN_MAX_PATH = 255 # MAX_PATH 260 need exclude 1 terminating null character <NUL>


# https://stackoverflow.com/a/2556252/1074998
#def rreplace(s, old, new, occurrence):
#    li = s.rsplit(old, occurrence)
#    return new.join(li)


# https://stackoverflow.com/questions/16870663
def validate_date(date_text):
    try:
        parse(date_text)
    except ValueError:
        raise ValueError("Incorrect data format, should be YYMMDD")
    return True


def sanitize(path):
    # trim multiple whitespaces # ".." is the responsibilities of get max path

    # Use PurePath instead of os.path.basename  https://stackoverflow.com/a/31273488/1074998 , e.g.:
    #>>> PurePath( '/home/iced/..'.replace('..', '') ).parts[-1] # get 'iced'
    #>>> os.path.basename('/home/iced/..'.replace('..', '')) # get empty ''
    # Ensure .replace('..', '') is last replacement before .strip() AND not replace back to dot '.'
    # https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file
    
    # [todo:0] Handle case sensitive and reserved file names in Windows like Chrome "Save page as" do
    # For portable to move filename between linux <-> win, should use IS_WIN only (but still can't care if case sensitive filename move to case in-sensitive filesystem). 
    # IS_WIN:
    path = path.replace('<', '').replace('>', '').replace('"', '\'').replace('?', '').replace('*', '').replace('/', '_').replace('\\', '_').replace('|', '_').replace(':', '_').replace('.', '_').strip()
    # Linux:
    #path.replace('/', '|').replace(':', '_').replace('.', '_').strip()

    # Put this after replace patterns above bcoz 2 distinct spaces may merge together become multiple-spaces, e.g. after ' ? ' replace to '  '
    # If using .replace('  ', ' ') will only replace once round, e.g. '    ' become 
    path = ' '.join(path.split()) 

    p = PurePath( path )

    if p.parts:
        return p.parts[-1]
    else:
        return ''
    

# The filesystem limits is 255(normal) , 242(docker) or 143((eCryptfs) bytes
# So can't blindly [:] slice without encode first
# And need decode back after slice
# And to ensure mix sequence byte in UTF-8 and work
#, e.g. abc𪍑𪍑𪍑
# , need try/catch to skip next full bytes of "1" byte ascii" OR "3 bytes 我" or "4 bytes 𪍑"
# ... by looping 4 bytes(UTF-8 max) from right to left
# HTML5 forbid UTF-16, UTF-16/32 not encourage to use in web page
# So only encode/decode in utf-8
# https://stackoverflow.com/questions/13132976
# https://stackoverflow.com/questions/50385123
# https://stackoverflow.com/questions/11820006
def get_max_path(arg_cut, fs_f_max, fpart_excluded_immutable, immutable):
    #print('before f: ' + fpart_excluded_immutable)
    if arg_cut >= 0:
        fpart_excluded_immutable = fpart_excluded_immutable[:arg_cut]
    if immutable:
        # immutable shouldn't limit to 1 byte(may be change next time or next project), so need encode also
        immutable_len = len(immutable.encode('utf-8'))
    else:
        immutable_len = 0

    space_remains = fs_f_max - immutable_len
    if space_remains < 1:
        return '' # No more spaces to trim(bcoz directories name too long), so only shows PinID.jpg

    # range([start], stop[, step])
    # -1 step * 4 loop = -4, means looping 4 bytes(UTF-8 max) from right to left
    for gostan in range(space_remains, space_remains - 4, -1):
        try:
            fpart_excluded_immutable = fpart_excluded_immutable.encode('utf-8')[: gostan ].decode('utf-8')
            break # No break still same result, but waste
        except UnicodeDecodeError:
            pass #print('Calm down, this is normal: ' + str(gostan) + ' f: ' + fpart_excluded_immutable)
    #print('after f: ' + fpart_excluded_immutable)
    # Last safety resort, in case any bug:
    fpart_excluded_immutable_base = sanitize ( fpart_excluded_immutable )
    if fpart_excluded_immutable_base != fpart_excluded_immutable.strip(): # Original need strip bcoz it might cut in space
        cprint(''.join([ HIGHER_RED, '\n[! A] Please report to me which Link/scenario it print this log.\
            Thanks:\n{} # {} # {} # {} # {}\n\n'
            .format(arg_cut, fs_f_max, repr(fpart_excluded_immutable), repr(fpart_excluded_immutable_base), immutable) ]), attrs=BOLD_ONLY, end='' )  
    return fpart_excluded_immutable_base


def get_output_file_path(arg_cut, fs_f_max, pre_immutable, human_fname, save_dir):

    immutable = sanitize(str(pre_immutable))

    if not immutable.strip(): # Ensure add hard-coded extension to avoid empty id and leave single dot in next step
        raise('pre_immutable empty')

    fpart_excluded_ext_before  = sanitize( human_fname )
    #print( 'get output f:' + repr(fpart_excluded_ext_before) )
   
    fpart_excluded_ext = get_max_path(arg_cut, fs_f_max, fpart_excluded_ext_before
            , immutable)
    if fpart_excluded_ext:
        if fpart_excluded_ext_before == fpart_excluded_ext: # means not truncat
            # Prevent confuse when trailing period become '..'ext and looks like '...'
            if fpart_excluded_ext[-1] == '.':
                fpart_excluded_ext = fpart_excluded_ext[:-1]
        else: # Truncated
            # No need care if two/three/... dots, overkill to trim more and loss information
            if fpart_excluded_ext[-1] == '.':
                fpart_excluded_ext = fpart_excluded_ext[:-1]

            fpart_excluded_ext = get_max_path(arg_cut, fs_f_max, fpart_excluded_ext
                , '...' + immutable)

            fpart_excluded_ext = fpart_excluded_ext + '...'

    return fpart_excluded_ext

    '''
    # To make final output path consistent with IS_WIN's abspath above, so also do abspath here:
    # (Please ensure below PurePath's file_path checking is using abspath if remove abspath here in future)
    file_path = os.path.abspath( os.path.join(save_dir, '{}'.format( fpart_excluded_ext)) ) #  + immutable
    #if '111' in file_path:
    #    print('last fp: ' + file_path + ' len: ' + str(len(file_path.encode('utf-8'))))
    try:
        # Note this is possible here if only . while the rest is empty, e.g. './.'
        # But better throws and inform me if that abnormal case.
        if PurePath(os.path.abspath(save_dir)).parts[:] != PurePath(file_path).parts[:-1]:
            cprint(''.join([ HIGHER_RED, '\n[! B] Please report to me which Link/scenario it print this log.\
                Thanks: {} # {} # {} # {} # {} \n\n'
                .format(arg_cut, fs_f_max, fpart_excluded_ext + immutable, save_dir, file_path) ]), attrs=BOLD_ONLY, end='' )  
            file_path = os.path.join(save_dir, '{}'.format( sanitize(fpart_excluded_ext + immutable)))
            if PurePath(os.path.abspath(save_dir)).parts[:] != PurePath(file_path).parts[:-1]:
                cprint(''.join([ HIGHER_RED, '\n[! C] Please report to me which Link/scenario it print this log.\
                    Thanks: {} # {} # {} # {} # {} \n\n'
                    .format(arg_cut, fs_f_max, fpart_excluded_ext + immutable, save_dir, file_path) ]), attrs=BOLD_ONLY, end='' )  
                raise
    except IndexError:
        cprint(''.join([ HIGHER_RED, '\n[! D] Please report to me which Link/scenario it print this log.\
            Thanks: {} # {} # {}\n\n'
            .format(arg_cut, fs_f_max, fpart_excluded_ext + immutable) ]), attrs=BOLD_ONLY, end='' )  
        raise
    #print('final f: ' + file_path)
    return file_path
    '''


py_out = sys.stdin
found_err_line = False;
if not py_out:
    out = ''

error_patterns = [
    "ERROR: unable to open for writing: [Errno 36] File name too long: './",
    'ERROR: unable to open for writing: [Errno 36] File name too long: "./',
    "ERROR: unable to download video data: [Errno 36] File name too long: './", # old
    "ERROR: Unable to download video: [Errno 36] File name too long: './", # new #1
    "ERROR: Unable to download video: [Errno 36] Filename too long: './", # new #2
    'ERROR: unable to download video data: [Errno 36] File name too long: "./', # old
    'ERROR: Unable to download video: [Errno 36] File name too long: "./' # new #1 ('Unable' become uppercase and no 'data')
    'ERROR: Unable to download video: [Errno 36] Filename too long: "./' # new #2 ('Filename' no space)
]

for out in py_out:
    for pattern in error_patterns:
        if out.startswith(pattern):
            err_filename = out.strip().replace(pattern, '', 1)
            err_filename = err_filename.rstrip('"' if '"' in pattern else "'")
            found_err_line = True
            break
    if found_err_line:
        break

if not found_err_line:
    # included `This video is only available for registered users` and `Unable to download webpage_ urlopen error timed out`
    print('Max Path Failed [e1] ' + sanitize(out)) # will be title to download
    sys.exit(1)

if __name__ == '__main__':
    fs_f_max = None
    if IS_WIN:
        fs_f_max = WIN_MAX_PATH
    else:
        #  255 bytes is normaly fs max, 242 is docker max, 143 bytes is eCryptfs max
        # https://github.com/moby/moby/issues/1413 , https://unix.stackexchange.com/questions/32795/
        # To test eCryptfs: https://unix.stackexchange.com/questions/426950/
        # If IS_WIN check here then need add \\?\\ for WIN-only
        for fs_f_max_i in (255, 242, 143):
            try:
                with open('A'*fs_f_max_i, 'r') as f:
                    fs_f_max = fs_f_max_i # if got really this long A exists will come here
                    break
            except FileNotFoundError:
                # Will throws OSError first if both FileNotFoundError and OSError met
                # , BUT if folder not exist then will throws FileNotFoundError first
                # But current directory already there, so can use this trick
                # In worst case just raise it
                fs_f_max = fs_f_max_i # Normally came here in first loop
                break
            except OSError: # e.g. File name too long
                pass #print('Try next') # Or here first if eCryptfs
        #print('fs filename max len is ' + repr(fs_f_max))
        # https://github.com/ytdl-org/youtube-dl/pull/25475
        # https://stackoverflow.com/questions/54823541/what-do-f-bsize-and-f-frsize-in-struct-statvfs-stand-for
        if fs_f_max is None: # os.statvfs ,ay not avaiable in Windows, so lower priority
            #os.statvfs('.').f_frsize - 1 = 4095 # full path max bytes
            fs_f_max = os.statvfs('.').f_namemax

        #print(sys.argv)
        #print(err_filename)
        #print('llen:' + str(len(err_filename.split('-')[-3])) )
        #print('llen:' + str(err_filename.split('-')[-3]) )
        if (err_filename.endswith('.part')) \
                and ( (len(err_filename.split('-')[-3]) in (6, 8)) and parse(err_filename.split('-')[-3]) \
                    or (len(err_filename.split('-')[-2]) in (6, 8)) and parse(err_filename.split('-')[-2]) ):
            if ( (len(err_filename.split('-')[-3]) in (6, 8)) and parse(err_filename.split('-')[-3]) ):
                date_index = -3
            else:
                date_index = -2
            pre_immutable = 'BUFFER' + '-' + '-'.join(err_filename.split('-')[date_index:]) # BUFFER in case mkv to webm and fragment index 1 to 999999
            human_fname = '-'.join(err_filename.split('-')[:date_index]) # Possible '-' in hname
            #print(human_fname)
            save_dir = pathlib.Path().resolve()
            yt_max_output_path = get_output_file_path(-1, fs_f_max, pre_immutable, human_fname, save_dir)
            print(yt_max_output_path) # important to send output to bash
            #rreplace(output_path, pre_immutable, '', 1)
        elif '-NA-' in err_filename:
            pre_immutable = 'BUFFERpart9999' + err_filename.split('-NA-')[-1]
            human_fname = '-NA-'.join(err_filename.split('-NA-')[:-1])
            save_dir = pathlib.Path().resolve()
            #print('imm: ' + (pre_immutable))
            #print('hnmae: ' + str(human_fname))
            yt_max_output_path = get_output_file_path(-1, fs_f_max, pre_immutable, human_fname, save_dir)
            print(yt_max_output_path) # important to send output to bash
        else:
            pre_immutable = 'BUFFERpart9999' + '-'.join(err_filename.split('-')[-2:]) # e.g. BUFFERpart9999-20250208-id123.mp4.ytdl
            human_fname = '-'.join(err_filename.split('-')[:-2]) # e.g. './video title'
            save_dir = pathlib.Path().resolve()
            yt_max_output_path = get_output_file_path(-1, fs_f_max, pre_immutable, human_fname, save_dir)
            print(yt_max_output_path)

            #print('Max Path Failed [e2] ' + sanitize(err_filename)) # will be title to download



