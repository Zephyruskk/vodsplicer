import datetime
import csv, sys
from pathlib import Path
import subprocess

def trim_video(source_file, start_time, end_time, output_file_name, game_info, upload_to_yt):
    cmd = [
        'ffmpeg', 
        '-i', source_file, 
        '-ss', start_time,
        '-to', end_time,
        '-c', 'copy', 
        '-y',
        output_file_name
    ]
    print(cmd)
    # subprocess.run(cmd)

    if upload_to_yt:
        upload_to_youtube(output_file_name, game_info)

def upload_to_youtube(file_to_upload, game_info):

    title = f"{game_info['round']} -- {game_info['p1_tag']} {game_info['p1_chars']} vs. {game_info['p2_tag']} {game_info['p2_chars']}"

    cmd = [
        'python',
        'upload_video.py',
        f"--file={file_to_upload}",
        f"--title={title}",
        "--keywords=Super Smash Bros. Ultimate, Tournament",
        "--category=20",
        "--privacyStatus=private",
    ]

    print(cmd)
    p = subprocess.Popen(cmd)

def convert_to_dt(time: str):
    hours, minutes, seconds = map(int, time.split(':'))
    td = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
    return td

def load_game_csv(path):
    f = open(path)
    r = csv.reader(f)

    source_video_file = None
    rows = []
    for i,row in enumerate(r):
        if i == 0:
            source_video_file = row
        if i > 1:
            rows.append(row)
    
    f.close()

    return (Path(source_video_file[0]), rows)

def update_tags_db(games):
    tags_dict = {}
    try:
        f = open("./sheets/tag_tracker.csv", 'r', newline='')
        rows = csv.reader(f)
        for row in rows:
            if row:
                tags = row[1:]
                tags_dict[row[0]] = tags
        f.close()
    except:
        print('Tag tracker not found! It will be made for you.')
        
    
    names_tags = [(g[3], g[4]) for g in games]
    names_tags.extend([(g[6], g[7]) for g in games])

    for name, tag in names_tags:
        if name in tags_dict.keys():
            if tag not in tags_dict[name]:
                tags_dict[name].append(tag)
        else:
            tags_dict[name] = [tag]
    
    # some dictionary comprehension, as a treat
    sorted_tags_dict = {k: tags_dict[k] for k in sorted(tags_dict, 
                                                        key=lambda x: x.lower())}

    f = open("./sheets/tag_tracker.csv", 'w', newline='')
    writer = csv.writer(f)

    for k,v in sorted_tags_dict.items():
        write_row = [k]
        write_row.extend(v)
        writer.writerow(write_row)
    f.close()
    


def main():
    upload_to_yt = False
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
        if not csv_path.exists():
            print(f"{str(csv_path)} was not found!") 
            sys.exit(2)
        if len(sys.argv) > 2:
            if sys.argv[2] == '--upload':
                upload_to_yt = True
    else:
        print("Please pass a target csv file as an argument after \'python splicer.py\'")
        sys.exit(1)      

    source_file, games = load_game_csv(csv_path)
    update_tags_db(games)

    sets = []
    s = 0
    for i,g in enumerate(games[:-1]):
        if int(games[i][0]) != int(games[i+1][0]):
            sets.append(games[s:(i+1)])
            s = i+1
    sets.append(games[s:])

    cmds = []
    for i,s in enumerate(sets):
        cmd = {}
        cmd['source file'] = str(source_file)
        
        start_str = s[0][2]
        start_dt = convert_to_dt(start_str) - datetime.timedelta(seconds=20)
        start_dt = max(start_dt, datetime.timedelta(seconds=0))

        end_str = s[-1][2]
        end_dt = convert_to_dt(end_str) + datetime.timedelta(minutes=7, seconds=30)
        if i < len(sets) - 1:
            next_start_str = sets[i+1][0][2]
            next_start_dt = convert_to_dt(next_start_str) - datetime.timedelta(minutes=1)
            end_dt = min(end_dt, next_start_dt)
        
        cmd['start time'] = str(start_dt)
        cmd['end time'] = str(end_dt)

        output_filename = f"{s[0][1].replace(' ', '')}_{s[0][3]}-v-{s[0][6]}.mkv"
        output_file_p = csv_path.parent / output_filename
        cmd['output file'] = str(output_file_p.resolve())
        
        p1_chars = []
        p2_chars = []
        for g in s:
            if g[5] not in p1_chars:
                p1_chars.append(g[5])
            if g[8] not in p2_chars:
                p2_chars.append(g[8])
        p1_chars_str = '('
        p1_chars_str += p1_chars[0]
        for c in p1_chars[1:]:
            p1_chars_str += f", {c}"
        p1_chars_str += ')'

        p2_chars_str = '('
        p2_chars_str += p2_chars[0]
        for c in p2_chars[1:]:
            p2_chars_str += f", {c}"
        p2_chars_str += ')'

        cmd['game info'] = {
            'round': s[0][1],
            'p1_tag': s[0][3],
            'p1_chars': p1_chars_str,
            'p2_tag': s[0][6],
            'p2_chars': p2_chars_str
        }
        cmds.append(cmd)


    for cmd in cmds:
        trim_video(cmd['source file'], cmd['start time'], cmd['end time'], cmd['output file'], cmd['game info'], upload_to_yt=upload_to_yt)


    
    print('\n\nSplicer done!')


if __name__ == '__main__':
    main()
