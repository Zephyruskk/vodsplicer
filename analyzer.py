import sys, datetime, time, logging
import cv2 as cv
import numpy as np
import pytesseract
import pandas as pd
import threading
import multiprocessing as mp

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
vid_path = "./media/sample_0001.mkv"
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
            game_starts.append((frame_number, max_val, frame))
            return True # match found 
        
    return False # no match found

################################################################################################################################
################################################################################################################################

def process_video():
    global fps, frame_count, game_starts

    capture = cv.VideoCapture(vid_path)
    
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

    for i in range(len(rois)):
        gray = cv.cvtColor(rois[i], cv.COLOR_BGR2GRAY)
        noise = cv.medianBlur(gray, 3)
        threshold = cv.threshold(noise, 0, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)[1]
        try:
            result = pytesseract.image_to_string(threshold)
            save_strings[i] = result.strip()
        except:
            print("No text found! No tag used?")
    
    return [(save_strings[0], save_strings[2]), (save_strings[1], save_strings[3])]

################################################################################################################################
################################################################################################################################

def calculate_image_clarity(image):
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    laplacian = cv.Laplacian(gray, cv.CV_64F)
    variance = np.var(laplacian)
    min_c = np.min(gray)
    max_c = np.max(gray)
    contrast = (max_c - min_c)/(max_c + min_c)
    return (variance, contrast)

################################################################################################################################
################################################################################################################################

if __name__ == '__main__':

    start_time = time.time()

    process_video()

    sorted_start_times = sorted(game_starts, key=lambda x: x[0])
    
    # post processing: group frames into arrays
    game_start_groupings = []
    s = 0
    for i in range(len(game_starts))[:-1]:
        if game_starts[i+1][0] - game_starts[i][0] >= fps*5:
            game_start_groupings.append(game_starts[s:(i+1)])
            s = i+1
    game_start_groupings.append(game_starts[s:])

    output_filename = r'C:/Users/zscot/Videos/vodfixer/measures2.mp4'
    codec = cv.VideoWriter_fourcc(*'mp4v')  # Choose the codec (e.g., 'XVID' for AVI, 'mp4v' for MP4)
    fps = 30.0  # Frames per second
    frame_width = 1920  # Width of the frames
    frame_height = 1080  # Height of the frames    # post processing
    out = cv.VideoWriter(output_filename, codec, fps, (frame_width, frame_height))

    font = cv.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    font_color = (0, 255, 0)  # BGR color tuple
    line_thickness = 2

    for i in range(len(game_start_groupings)):
        g = [frame[2] for frame in game_start_groupings[i]]
        for f in g:
            v,c = calculate_image_clarity(f)
            cv.rectangle(f, (45,600),(350, 850), (0,0,0), cv.FILLED)
            cv.putText(f, f"Group: {i}", (50,650), font, font_scale, font_color, line_thickness)
            cv.putText(f, f"Variance: {v}", (50,700), font, font_scale, font_color, line_thickness)
            cv.putText(f, f"Contrast: {c}", (50,750), font, font_scale, font_color, line_thickness)
            out.write(f)
    
    out.release()
    
    exit()

    pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'

    # reader = easyocr.Reader(['en'])

    for f,val,image in sorted_start_times:
        datetime_start_time = datetime.timedelta(seconds=f)
        print(f"Game start at : {datetime_start_time}. Conf Value: {val}")
        # cv.imshow(f"{f}", image)
        # key = cv.waitKey(0) & 0xFF
        # if key == ord('s'):
        #     cv.imwrite(f"C:/Users/zscot/Videos/vodfixer/{f}.png", image)
        cv.destroyAllWindows()

        print(scrape_keyframe(image))
        # cv.imshow(f"{datetime_start_time}", image)
        # key = cv.waitKey(0) & 0xFF

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed: {elapsed_time}")
