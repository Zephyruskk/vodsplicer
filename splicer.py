import datetime
import csv, sys
from pathlib import Path
import subprocess

def trim_video(source_file, start_time, end_time, output_file_name):
    cmd = [
        'ffmpeg', 
        '-i', source_file, 
        '-ss', start_time,
        '-to', end_time,
        '-c', 'copy', 
        '-y',
        output_file_name
    ]

    subprocess.run(cmd)

def convert_to_dt(time: str):
    hours, minutes, seconds = map(int, time.split(':'))
    td = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
    return td

def load_csv(path):
    f = open(path)
    r = csv.reader(f)

    source_video_file = None
    rows = []
    for i,row in enumerate(r):
        if i == 0:
            source_video_file = row
        if i > 1:
            rows.append(row)

    return (Path(source_video_file[0]), rows)


def main():

    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
        if not csv_path.exists():
            print(f"{str(csv_path)} was not found!") 
            sys.exit(2)
    else:
        print("Please pass a target csv file as an argument after \'python splicer.py\'")
        sys.exit(1)       

    source_file, games = load_csv(csv_path)

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
        cmd['output file'] = str(output_file_p)
        cmds.append(cmd)


    for cmd in cmds:
        trim_video(cmd['source file'], cmd['start time'], cmd['end time'], cmd['output file'])
    
    print('\n\nSplicer done!')


if __name__ == '__main__':
    main()
