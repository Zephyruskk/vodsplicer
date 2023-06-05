import sys, datetime, time, logging, csv
import cv2 as cv
import numpy as np
import pytesseract
import pandas as pd
import threading
import multiprocessing as mp
import Levenshtein
from pathlib import Path

fps, frame_count = 0,0 # globals, for later
temp_threshold = 0.75 # template threshold, be above this to clock player icons

# all coords are x1,y1,x2,y2

p1_char_coords = 120,0,960,150 
p2_char_coords = 1080,0,1919,150

p1_tag_coords = 0,150,275,215
p2_tag_coords = 960,150,1235,215

go_coords = 495,195,1305,505 

p1_coords =  10,20,100,100 # 20,40,80,90 
p2_coords = 980,40,1046,90 # 970,20,1060,100
p3_coords = 19,40,85,90
p4_coords = 980,40,1046,90

player_icon_coords = 0,0,1700,90

batch_size = 16 # how many frames get checked at once (thread count!)
batch_item_length = 30 # frames long

# file paths
source_vid_path = "./media/sample_0001.mkv"
go_path = "./media/go.png"
p1_path = "./media/p1.png"
p2_path = "./media/p2.png"
p3_path = "./media/p3.png"
p4_path = "./media/p4.png"

# state variables, [frame number, confidence value, np frame array]
game_starts = []

################################################################################################################################
################################################################################################################################

# detect if player icons are in a given frame
def process_frame(frame, frame_number, templates, region_of_interest):
    global game_starts

    x1,y1,x2,y2 = region_of_interest

    roi = frame[y1:y2, x1:x2]
    roi = cv.cvtColor(roi, cv.COLOR_BGR2GRAY)

    for t in templates:
        res = cv.matchTemplate(roi, t, cv.TM_CCOEFF_NORMED)

        # Find the location of the maximum correlation coefficient in the ROI
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)

        if max_val >= temp_threshold:
            game_starts.append([frame_number, max_val, frame])
            return True # match found 
        
    return False # no match found

################################################################################################################################
################################################################################################################################

def process_video():
    global fps, frame_count, game_starts

    capture = cv.VideoCapture(source_vid_path)
    
    # reading in templates
    go_template = cv.imread(go_path)
    go_template = cv.cvtColor(go_template, cv.COLOR_BGR2GRAY)
    p1_template = cv.imread(p1_path)
    p1_template = cv.cvtColor(p1_template, cv.COLOR_BGR2GRAY)  # convert to grayscale
    p2_template = cv.imread(p2_path)
    p2_template = cv.cvtColor(p2_template, cv.COLOR_BGR2GRAY)  # convert to grayscale
    p3_template = cv.imread(p3_path)
    p3_template = cv.cvtColor(p3_template, cv.COLOR_BGR2GRAY)  # convert to grayscale
    p4_template = cv.imread(p4_path)
    p4_template = cv.cvtColor(p4_template, cv.COLOR_BGR2GRAY)  # convert to grayscale

    ## filling in video details ##
    if not capture.isOpened():
        print("Error opening video")
    else:
        fps = capture.get(cv.CAP_PROP_FPS)
        print(f"Frames per second: {fps} FPS")
        frame_count = capture.get(cv.CAP_PROP_FRAME_COUNT)
        print(f"Frame count: {frame_count} frames")

    frame_no = 0 # counting frames
    while capture.isOpened():
        try:
            # grabbing frames
            frames = [None] * batch_size

            for i in range(len(frames)):
                frame_grab = capture.grab() 
                ret, frame = capture.retrieve() # decode it!
                frame_no += 1
                if ret:
                    frames[i] = (frame_no, frame)
                
                # skip frames
                for i in range(batch_item_length -1): # skip 29 frames
                    temp1 = capture.grab()
                    frame_no += 1
            
            # processing frames
            threads = list()
            for f in frames:
                if f is not None:
                    t = threading.Thread(target=process_frame, args=(f[1], f[0], [p1_template, p2_template, p3_template, p4_template], p1_coords))
                    threads.append(t)
                    t.start()
            
            for i,t in enumerate(threads):
                t.join() 
            
            if frame_no >= frame_count - (batch_size * batch_item_length): # every batch, check if we're done
                break # don't check for game starts in the last (batch_size * batch_item_length / fps) seconds MAX -- probably fine 
        except Exception as e:
            print(e)
            break
    
    capture.release()
    cv.destroyAllWindows()

################################################################################################################################
################################################################################################################################

# getting tags and characters
def scrape_keyframe(frame):

    # get character names + tags
    x1,y1,x2,y2 = p1_char_coords
    p1_char_roi = frame[y1:y2, x1:x2]
    x1,y1,x2,y2 = p1_tag_coords
    p1_tag_roi = frame[y1:y2, x1:x2]

    x1,y1,x2,y2 = p2_char_coords
    p2_char_roi = frame[y1:y2, x1:x2]
    x1,y1,x2,y2 = p2_tag_coords
    p2_tag_roi = frame[y1:y2, x1:x2]

    rois = [p1_char_roi, p2_char_roi, p1_tag_roi, p2_tag_roi]
    save_strings = ["Player 1 Character", "Player 2 Character", "Player 1", "Player 2"]
    config = r''
    for i in range(len(rois)):
        if i > 1: config = r'--psm 7'
        gray = cv.cvtColor(rois[i], cv.COLOR_BGR2GRAY)
        noise = cv.medianBlur(gray, 3)
        threshold = cv.threshold(noise, 175, 255, cv.THRESH_BINARY)[1]

        # cv.imshow(save_strings[i], threshold)
        # key = cv.waitKey() & 0xFF
        # cv.destroyAllWindows()

        try:
            result = pytesseract.image_to_string(threshold, config=config)
            save_strings[i] = result.strip()
        except:
            print("No text found! No tag used?")
    
    return [(save_strings[0], save_strings[2]), (save_strings[1], save_strings[3])]

################################################################################################################################
################################################################################################################################

# returns index of the best match of strings from a group (lowest Levenshtein distance)
def average_string(group):
    avg_distances = []

    for i,string1 in enumerate(group):
        total_dist = 0
        for j,string2 in enumerate(group):
            if i != j:
                distance = Levenshtein.distance(string1, string2)
                total_dist += distance
        avg_dist = total_dist / (len(group) - 1)
        avg_distances.append(avg_dist)
    
    return avg_distances.index(min(avg_distances))

################################################################################################################################
################################################################################################################################

if __name__ == '__main__':
    pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'

    start_time = time.time()

    process_video()

    sorted_start_times = sorted(game_starts, key=lambda x: x[0])

    # scrape keyframes w pytesseract
    for i,frame in enumerate(sorted_start_times):
        f,val,image = frame
        # datetime_start_time = datetime.timedelta(seconds=(f/60))
        # print(f"Game start at : {datetime_start_time}. Conf Value: {val}")
        sorted_start_times[i].append(scrape_keyframe(image)) # formatted as [[Player 1 char, Player 1 tag], [Player 2 char, Player 2 tag]]
    
    # post processing: group frames into arrays by proximity
    game_start_groupings = []
    s = 0
    for i in range(len(game_starts))[:-1]:
        if game_starts[i+1][0] - game_starts[i][0] >= fps*5:
            game_start_groupings.append(game_starts[s:(i+1)])
            s = i+1
    game_start_groupings.append(game_starts[s:])

    final_starts = [] 
    '''FINAL, clean data
    @0 -- Frame Number
    @1 -- [Player 1 char, Player 1 tag]
    @2 -- [Player 2 char, Player 2 tag]
    @3 -- Frame (np array)
    '''
    for g in game_start_groupings:
        #0 frame number
        starting_frame_number = g[0][0]

        #1, #2 player info
        scraped = [frame[3] for frame in g] # list comprehension bs incoming (HE DID NOT PLAN AHEAD)
        p1_char_samples, p1_tag_samples, p2_char_samples, p2_tag_samples = [s[0][0] for s in scraped], [s[0][1] for s in scraped], [s[1][0] for s in scraped], [s[1][1] for s in scraped]

        p1_char_i = average_string(p1_char_samples)
        p1_tag_i = average_string(p1_tag_samples)
        p2_char_i = average_string(p2_char_samples)
        p2_tag_i = average_string(p2_tag_samples)

        p1_char = p1_char_samples[p1_char_i].replace("\n", " ")
        p1_tag = p1_tag_samples[p1_tag_i]
        p2_char = p2_char_samples[p2_char_i].replace("\n", " ")
        p2_tag = p2_tag_samples[p2_tag_i]

        #3 frame
        frame_at_start = g[-1]

        frame_info = {}
        frame_info['frame number'] = starting_frame_number
        frame_info['p1 info'] = (p1_char, p1_tag)
        frame_info['p2 info'] = (p2_char, p2_tag)
        frame_info['frame'] = frame_at_start

        final_starts.append(frame_info)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed: {elapsed_time}")

    file_stem = Path(source_vid_path).stem
    dir_name = Path("./sheets/" + file_stem)

    Path.mkdir(dir_name, parents=True, exist_ok=True)

    csv_file = Path(str(dir_name) + "/" + file_stem + ".csv")

    f = open(csv_file, 'w', newline='')

    writer = csv.writer(f)

    writer.writerow([str(Path(source_vid_path).resolve())])
    writer.writerow(["SET #", "ROUND", "STARTING FRAME", "PLAYER 1", "P1 TAG", "P1 CHARACTER", "PLAYER 2", "P2 TAG", "P2 CHARACTER"])

    for s in final_starts:
        td = datetime.timedelta(seconds=(s['frame number']/60)).seconds
        hours, rem = divmod(td, 3600)
        minutes, seconds = divmod(rem, 60)
        start_hh_tt_ss = f"{hours:02}:{minutes:02}:{seconds:02}"
        writer.writerow([
            '', '', start_hh_tt_ss, '', s['p1 info'][1], s['p1 info'][0], '', s['p2 info'][1], s['p2 info'][0]
        ])
        print(f"{s['frame number']}: {s['p1 info']}, {s['p2 info']}")

    f.close()
    


