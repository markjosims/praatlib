import os
import subprocess
from pathlib import Path
from copy import deepcopy
from platform import system

path = Path(__file__).parent.absolute()

system_name = system()
if system_name == 'Windows':
    praat_dir = r"C:\Program Files\Praat\Praat.exe"
    if not os.path.exists(praat_dir):
        praat_dir = r"C:\Program Files (x86)\Praat.exe"
elif system_name == 'Darwin':
    praat_dir = '/Applications/Praat.app/Contents/MacOS/Praat'
else:
    praat_dir = '/usr/bin/praat'

def formant_from_audio(filename, outfile=None, time_step=0, formant_max=5, hertz_max=5000,
                       window_length=0.025, pre_emphasis=50, jsonify=False):
    if not outfile:
        outfile = filename.replace('.wav', '.Formant')
    subprocess.call([
        praat_dir, '--run', os.path.join(path, 'soundToFormant.praat'),
        filename, outfile, str(time_step), str(formant_max),
        str(hertz_max), str(window_length), str(pre_emphasis)
    ])
    if jsonify:
        return jsonify_formant(outfile)

# given a nested dictionary with a subdict entry with default parameters
# and subdicts with parameters for specific vowels
# make a formant object for the default parameters and for each specific vowel
# specified by 'keys' arg (or all if 'keys' is None)
def make_formant_objs(wav_file, params, keys=None):
    generate_outfile = lambda fname, key : fname.replace('.wav', f'-{key}.Formant')
    if not keys:
        if 'default' not in params:
            params['default'] = {}
        keys = params.keys()
    for k in keys:
        formant_from_audio(wav_file, generate_outfile(wav_file, k), **params[k])

# tries to find formant obj from a wav file with a specific key
# (specifying parameters used in formant algorithm)
# if does not exist, return default
def find_formant_obj(wav_file, key):
    frmnt_file = wav_file.replace('.wav', f'-{key}.Formant')
    if os.path.isfile(frmnt_file):
        return jsonify_formant(frmnt_file)
    frmnt_file = wav_file.replace('.wav', f'-default.Formant')
    return jsonify_formant(frmnt_file)

def pitch_from_audio(filename, time_step=0.01, pitch_min=75, pitch_max=600):
    subprocess.call([
        praat_dir, '--run', os.path.join(path, 'soundToPitch.praat'),
        filename, str(time_step), str(pitch_min), str(pitch_max)
    ])

def textgrid_from_audio(filename):
    subprocess.call([
        praat_dir, '--run', 'soundToTextgrid.praat',
        filename
    ])

def get_voice_report(filename, start, end, time_step=0.01, pitch_min=75, pitch_max=600):
    outfile = filename.replace('.wav', '-voice_report.txt')
    subprocess.call([
        praat_dir, '--run', 'getVoiceReport.praat',
        filename, outfile, str(start), str(end), str(time_step), str(pitch_min), str(pitch_max)
    ])
    return outfile

def jsonify_voice_report(filename):
    json_obj = {}
    with open(filename, 'r') as f:
        f.readline()
        line = f.readline()
        while line:
            key = line.strip().replace(':', '')
            this_obj = {}
            json_obj[key] = this_obj
            line = f.readline()
            while line.startswith(' '*3):
                key, val = line.split(sep=':')
                key, val = key.strip(), val.strip()
                this_obj[key] = val
                line = f.readline()
    return json_obj

def jsonify_pitch(filename):
    matrix = jsonify_matrix(filename)
    return flatten_json_matrix(matrix)

def flatten_json_matrix(json_obj):
    del json_obj['ymin']
    del json_obj['ymax']
    del json_obj['ny']
    del json_obj['dy']
    del json_obj['y1']
    frames = json_obj.pop('columns')[0]
    json_obj['frames'] = frames
    return json_obj

def jsonify_matrix(filename):
    json_obj = {}
    with open(filename, 'r') as f:
        read_header(f, json_obj, "z [] []:")
        dx = json_obj['dx']
        start_time = json_obj['x1']
        line = f.readline().strip()
        numcols = json_obj['ny']
        cols = []
        for i in range(numcols):
            if line.strip() != f'z [{i+1}]:':
                print(line)
                print(f"Check the matrix file {filename} is formatted correctly with {numcols} columns.")
                return
            this_col, line = read_matrix_col(f, i, dx, start_time)
            cols.append(this_col)
    json_obj['columns'] = cols
    return json_obj
        
        

def read_matrix_col(f, col_i, dx, start_time):
    line = f.readline().strip()
    col = []
    while line and line != f'z [{col_i+1}]:':
        index_str, freq = key_arg_equals(line)
        y, x = all_args_in_brackets(index_str)
        if y != col_i+1:
            print('Check matrix columns are formatted correctly.')
        time = start_time + dx * x
        cell = {"time": time, "freq": freq}
        col.append(cell)
        line = f.readline().strip()
    return col, line

def jsonify_formant(filename):
    json_obj = {}    
    with open(filename, 'r') as f:
        read_header(f, json_obj, "frames []:")
        dx = json_obj['dx']
        start_time = json_obj['x1']
        line = f.readline().strip()
        frames = []
        json_obj['frames'] = frames
        while line.startswith("frames"):
            frame_num = arg_in_brackets(line)
            time = frame_num * dx + start_time
            frame, line = read_formant_frame(f, json_obj, time)
            frames.append(frame)
        return json_obj

def read_formant_frame(f, json_obj, time):
    frame = {}
    frame['time'] = time
    line = f.readline().strip()
    while '=' in line:
        key, val = key_arg_equals(line)
        frame[key] = val
        line = f.readline().strip()
    assert line == 'formant []:'
    line = f.readline().strip()
    formants = []
    
    while line and not line.startswith('frames'):
        formant_num = arg_in_brackets(line)
        assert formant_num-1 == len(formants), line
        formant = {}
        formant["formant_num"] = formant_num
        formants.append(formant)
        line = f.readline().strip()
        while '=' in line:
            key, arg = key_arg_equals(line)
            formant[key] = arg
            line = f.readline().strip()

    formants_dict = {}
    for formant in formants:
        number = formant.pop("formant_num")
        formants_dict[f"f{number}"] = formant
    
    frame['formants'] = formants_dict
    return frame, line

def get_value_at_time(json_obj, time, ignore_error=False):
    frames = json_obj['frames']
    min_displace = float('inf')
    index = None
    for i, frame in enumerate(frames):
        frame_time = frame['time']
        displace = abs(time-frame_time)
        if displace < min_displace:
            index = i
            min_displace = displace
        if displace > min_displace:
            break
    if not index:
        if ignore_error:
            # return an object with values set to nan
            return set_leaves_as_na(frames[0], copy=True)
        raise IndexError("Time out of range for formant object.")
    return frames[index]

def get_avg_over_interval(json_obj, start, end, key=None, keys=None):
    frames = json_obj['frames']
    values = []
    for frame in frames:
        if (frame['time'] >= start) and (frame['time'] <= end):
            if keys:
                val = frame.copy()
                for k in keys:
                    val = val[k]
            else:
                val = frame[key]
            values.append(val)
    return sum(values)/len(values)

def get_max_frame(json_obj, start, end, value):
    valid_frames = [frame for frame in json_obj['frames'] if start < frame['time'] < end]
    max = float('-inf')
    max_frame = None
    for frame in valid_frames:
        if frame[value] > max:
            max = frame[value]
            max_frame = frame
    return max_frame

def get_min_frame(json_obj, start, end, value):
    valid_frames = [frame for frame in json_obj['frames'] if start < frame['time'] < end]
    min = float('inf')
    min_frame = None
    for frame in valid_frames:
        if frame[value] < min:
            min = frame[value]
            min_frame = frame
    return min_frame

def jsonify_textgrid(filename, encoding='utf8'):
    json_obj = {}
    with open(filename, 'r', encoding=encoding) as f:
        read_header(f, json_obj, 'item []:')
        tiers = []
        json_obj['tiers'] = tiers
        line = f.readline().strip()
        while line.startswith('item'):
            item_idx = arg_in_brackets(line)
            assert item_idx-1 == len(tiers)
            this_tier, line = read_tier(f)
            tiers.append(this_tier)
    return json_obj
        
        
def read_header(f, json_obj, stop_str):
    line = f.readline()
    while not line_has_stopstr(line, stop_str):
        if '=' in line:
            key, val = key_arg_equals(line)
            json_obj[key] = val
        line = f.readline().strip()
    return line

def line_has_stopstr(line, stop_str):
    if type(stop_str) is str:
        return line.startswith(stop_str)
    else:
        # assume stop_str is list of possible strs
        for stop in stop_str:
            if line.startswith(stop):
                return True
    return False

def read_tier(f):
    segments = []
    tier = {}
    line = read_header(f, tier, ['intervals:', 'points:'])
    seg_str = line.split(sep=':')[0] # should be 'intervals' or 'points'
    tier[seg_str] = segments
    _, tier['size'] = key_arg_equals(line)
    line = f.readline().strip()
    while line.startswith(seg_str):
        this_seg, line = read_segment(f, seg_str)
        segments.append(this_seg)
    return tier, line

def read_segment(f, seg_str):
    interval = {}
    line = f.readline().strip()
    while line and not line.startswith(seg_str)\
    and not line.startswith('item'):
        key, val, line = read_interval_arg(f, line, seg_str)
        interval[key] = val
        
    return interval, line

def slice_textgrid(tg_obj, start, end):
    assert end > start
    assert start >= 0
    duration = end-start
    tg_slice = deepcopy(tg_obj)
    tg_slice['xmax'] = duration
    for i, tier in enumerate(tg_obj['tiers']):
        tg_slice['tiers'][i] = slice_tier(tier, start, end)
    return tg_slice

def slice_tier(tier, start, end):
    new_tier = deepcopy(tier)
    xmin, xmax = tier['xmin'], tier['xmax']
    
    new_start = xmin - start if start < xmin else 0
    new_end   = xmax - start if xmax < end else end-start
    
    if new_start > end:
        return
    if new_end <= 0:
        return
    
    new_tier['xmin'] = new_start
    new_tier['xmax'] = new_end
    
    for i, interval in enumerate(tier['intervals']):
        new_interval = slice_interval(interval, start, end)
        new_tier['intervals'][i] = new_interval
        
    new_tier['intervals'] = [intvl for intvl in new_tier['intervals'] if intvl]
    new_tier['size'] = len(new_tier['intervals'])
    return new_tier
        
def slice_interval(interval, start, end):
    new_interval = interval.copy()
    
    xmin, xmax = interval['xmin'], interval['xmax']
    new_start = xmin - start if start < xmin else 0
    new_end   = xmax - start if xmax < end else end
    
    if new_start > (end-start):
        return
    if new_end <= 0:
        return
    
    new_interval['xmin'] = new_start
    new_interval['xmax'] = new_end
    
    return new_interval

def erase_tg_interval(tg_obj, start, end, skip_tiers=[]):
    assert end > start
    assert start >= 0
    new_tg = deepcopy(tg_obj)
    for i, tier in enumerate(tg_obj['tiers']):
        if tier['name'] in skip_tiers:
            continue
        new_tg['tiers'][i] = erase_tier_interval(tier, start, end)
    return new_tg

def erase_tier_interval(tier, start, end):
    new_tier = deepcopy(tier)
    erased_interval_i = None
    after_erase_i = None
    for i, interval in enumerate(tier['intervals']):
        if interval['xmax'] >= start:
            if erased_interval_i is None:
                erased_interval_i = i
            elif interval['xmin'] < end:
                new_tier['intervals'].remove(interval)
            elif not after_erase_i:
                after_erase_i = i
    erasure_xmax = tier['intervals'][after_erase_i]['xmin']\
        if after_erase_i else tier['intervals'][-1]['xmax']
    if (len(new_tier['intervals'])>erased_interval_i+1):
        post_erase_int = new_tier['intervals'][erased_interval_i+1]
        if post_erase_int['text'] == '':
            erasure_xmax = post_erase_int['xmax']
            new_tier['intervals'].remove(post_erase_int)
    new_tier['intervals'][erased_interval_i]['xmax'] = erasure_xmax
    new_tier['intervals'][erased_interval_i]['text'] = ''
    new_tier['size'] = len(new_tier['intervals'])
    return new_tier

def json_to_tg(json_obj, filename, encoding='utf8'):
    with open(filename, 'w', encoding=encoding) as f:
        write_header(json_obj, f)
        for i, tier in enumerate(json_obj['tiers']):
            f.write(f'    item [{i+1}]:\n')
            write_tier(tier, f)
            
def write_tier(tier, f):
    f.write(f"{' '*8}class = \"{tier['class']}\" \n")
    f.write(f"{' '*8}name = \"{tier['name']}\" \n")
    f.write(f"{' '*8}xmin = {tier['xmin']} \n")
    f.write(f"{' '*8}xmax = {tier['xmax']} \n")
    f.write(f"{' '*8}intervals: size = {len(tier['intervals'])} \n")
    for i, interval in enumerate(tier['intervals']):
        write_interval(interval, i, f)

def write_interval(interval, i, f):
    f.write(f"{' '*8}intervals [{i+1}]:\n")
    f.write(f"{' '*12}xmin = {interval['xmin']} \n")
    f.write(f"{' '*12}xmax = {interval['xmax']} \n")
    f.write(f"{' '*12}text = \"{interval['text']}\" \n")
    
    
def write_header(json_obj, f):
    header = \
f"""File type = "ooTextFile" 
Object class = "TextGrid" 

xmin = {json_obj['xmin']}
xmax = {json_obj['xmax']} 
tiers? <exists> 
size = {len(json_obj['tiers'])} 
item []: 
"""
    f.write(header)
    
def get_tier(tg_obj, name, to_lower=True, lazy=True):
    if not lazy:
        out = []
    if type(name) is list:
        for n in name:
            try:
                if lazy:
                    return get_tier(tg_obj, n, to_lower, lazy)
                else:
                    out.append(get_tier(tg_obj, n, to_lower, lazy))
            except KeyError:
                continue
        if lazy:
            return
        return out
    if to_lower:
        name = name.lower()
    for tier in tg_obj['tiers']:
        if to_lower and tier['name'].lower().strip() == name:
            if lazy:
                return tier
            out.append(tier)
        elif tier['name'].strip() == name:
            if lazy:
                return tier
            out.append(tier)
    if not lazy and out:
        return out
    names = [tier['name'] for tier in tg_obj['tiers']]
    raise KeyError(f'Tier name {name} not found in textgrid with tiers {names}')

def get_interval(time, tier=None, tg_obj=None, tier_name=None, to_lower=True):
    time = try_cast_to_numeric(time)
    
    if not tier:
        assert tg_obj and tier_name, "Either a tier object must be passed or else "+\
        "a textgrid object with the name of the tier being queried."
        tier = get_tier(tg_obj, tier_name, to_lower, True)
        
    for inter in tier['intervals']: 
        if inter['xmin'] <= time <= inter['xmax']:
            return inter
    return IndexError("No interval in tier with specified time.")


def read_interval_arg(f, arg_str, seg_str):
    line = f.readline().strip()
    arg_labels = [
        'item', 'xmin', 'xmax',
        'number', 'mark', 'text'
    ]
    while line and (not line.startswith(seg_str))\
    and (not any(line.startswith(lab) for lab in arg_labels) ):
        arg_str += line
        line = f.readline().strip()        
    key, val = key_arg_equals(arg_str)
    return key, val, line

def read_file_safe(filename, encoding):
    if type(encoding) is list:
        for enc in encoding:
            try:
                return open(filename, 'r', encoding=enc)
            except UnicodeError:
                continue
    return open(filename, 'r', encoding=encoding)

def remove_quotes(f):
    def g(s):
        return f(s.replace('"', ''))
    return g
        

def str_before_char(s, c):
    idx = s.index(c)
    return s[:idx].strip()

def str_after_char(s, c):
    idx = s.index(c)
    return s[idx+1:].strip()

def str_btw_chars(s, start, end):
    out = str_after_char(s, start)
    out = str_before_char(out, end)
    return out

@remove_quotes
def arg_in_brackets(s):
    val = str_btw_chars(s, '[', ']')
    return try_cast_to_numeric(val)

def all_args_in_brackets(s):
    args = []
    is_arg = False
    last_arg = ''
    for char in s:
        if char == '[':
            is_arg = True
        elif char == ']':
            args.append(last_arg)
            last_arg = ''
            is_arg = False
        elif is_arg:
            last_arg += char
    return [try_cast_to_numeric(arg) for arg in args]

@remove_quotes
def key_arg_equals(s):
    key = str_before_char(s, '=')
    val = str_after_char(s, '=')
    return key, try_cast_to_numeric(val)
     
def try_cast_to_numeric(val):
    if type(val) in (int, float):
        return val
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return val

def set_leaves_as_na(d, copy=False):
    if copy:
        d = deepcopy(d)
    for k, v in d.items():
        if type(v) is dict:
            d[k] = set_leaves_as_na(v)
        else:
            d[k] = 'NAN' #change to np.nan?
    return d