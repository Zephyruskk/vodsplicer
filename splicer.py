import datetime
import csv
from pathlib import Path
import subprocess

def trim_video(source_file, start_time, end_time, output_file_name):
    cmd = [
        'ffmpeg', 
        '-i', source_file, 
        '-ss', start_time,
        '-to', end_time,
        '-c', 'copy', 
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

# sample = [
#     ['1','Losers Round 4','00:01:28','ksg','DRHANSWEEP','STEVE','Shard','267 152 46','MARIO'],
#     ['1','Losers Round 4','00:06:28','ksg','DRHANSWEEP','STEVE','Shard','267 152 46','MARIO'],
#     ['2','Losers Finals','00:12:22','GameCube','GameCube','GANONDORF','Shard','267 152 46','MARIO'],
#     ['2','Losers Finals','00:17:18','GameCube','GameCube','GANONDORF','Shard','267 152 46','MARIO'],
#     ['2','Losers Finals','00:20:21','GameCube','GameCube','GANONDORF','Shard','267 152 46','MARIO'],
#     ['2','Losers Finals','00:22:50','GameCube','GameCube','GANONDORF','Shard','267 152 46','MARIO'],
# ]

def main():

    temp = Path("./sheets/sample_0001/sample_0001.csv")
    source_file, games = load_csv(temp)
    
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
        output_file_p = source_file.parent / output_filename
        cmd['output file'] = str(output_file_p)
        cmds.append(cmd)


    for cmd in cmds:
        trim_video(cmd['source file'], cmd['start time'], cmd['end time'], cmd['output file'])


if __name__ == '__main__':
    main()
