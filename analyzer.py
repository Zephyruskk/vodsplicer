import sys, datetime, time, logging
import cv2 as cv
import numpy as np
# import pytesseract
import easyocr
import pandas as pd
import threading
import multiprocessing as mp


temp_threshold = 0.75
# x1, y1 = 960,20
# x2, y2 = 1080, 105

p1_char_coords = 120,0,960,150
p2_char_coords = 1080,0,1919,150

p1_tag_coords = 0,150,275,215
p2_tag_coords = 960,150,1235,215

go_coords = 495,195,1305,505 
p1_coords = 20,40,80,90 # 10,20,100,100 # x1,y1,x2,y2
p2_coords = 980,40,1046,90 # 970,20,1060,100
p3_coords = 19,40,85,90
p4_coords = 980,40,1046,90

player_icon_coords = 0,0,1700,90

batch_size = 16 # how many frames get checked at once (thread count!)
batch_item_length = 30 # frames long


# state variables 
game_start_times = []
game_start_frames = False



def process_frame(frame, frame_number, templates, region_of_interest):
    global game_start_times

    x1,y1,x2,y2 = region_of_interest

    roi = frame[y1:y2, x1:x2]

    roi = cv.cvtColor(roi, cv.COLOR_BGR2GRAY)

    for t in templates:
        res = cv.matchTemplate(roi, t, cv.TM_CCOEFF_NORMED)

        # Find the location of the maximum correlation coefficient in the ROI
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)

        if max_val >= temp_threshold:
            game_start_times.append((frame_number, max_val, frame))
            return True # match found 
        
    return False # no match found

        

# load in keyframes, batch_size at a time
def process_video():

    vid_path = "./media/sample_0003.mkv"
    go_path = "./media/go.png"
    p1_path = "./media/p1.png"
    p2_path = "./media/p2.png"
    p3_path = "./media/p3.png"
    p4_path = "./media/p4.png"

    capture = cv.VideoCapture(vid_path)

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

    p2_t_h, p2_t_w = p2_template.shape[::1]

    if not capture.isOpened():
        print("Error opening video")
    else:
        fps = capture.get(cv.CAP_PROP_FPS)
        print(f"Frames per second: {fps} FPS")
        frame_count = capture.get(cv.CAP_PROP_FRAME_COUNT)
        print(f"Frame count: {frame_count} frames")

    global game_start_times
    frame_no = 0
    
    while capture.isOpened():
        try:
            frames = [None] * batch_size

            for i in range(len(frames)):
                frame_grab = capture.grab()
                ret, frame = capture.retrieve() # decode it!
                frame_no += 1
                if ret:
                    frames[i] = (frame_no, frame)
                
                for i in range(batch_item_length -1): # skip 29 frames
                    temp1 = capture.grab()
                    frame_no += 1
            #         if not temp1:
            #             if frame_no > frame_count:
            #                 return
            
            threads = list()
            for f in frames:
                if f is not None:
                    # print(f"Thread for frame {f[0]} starting...")
                    t = threading.Thread(target=process_frame, args=(f[1], f[0], [p1_template, p2_template, p3_template, p4_template], player_icon_coords))
                    threads.append(t)
                    t.start()
            
            for i,t in enumerate(threads):
                t.join() # wait for the thread to terminate
                # print(f"Thread {i} joined!")
            
            if frame_no >= frame_count - (batch_size * batch_item_length): # every batch, check if we're done
                break # don't check for game starts in the last (batch_size * batch_item_length / fps) seconds MAX -- probably fine 
        except Exception as e:
            print(e)
            break
    
    # post processing
    for i in range(len(game_start_times))[1:][::-1]: # cut off zero index, then reverse order
        if game_start_times[i][0] - game_start_times[i-1][0] < fps*5: # if game start is within 5 seconds of the last game start, get rid of it
            game_start_times.pop(i-1) # take the LATEST frame found to get the clearest possible frame 
    
    capture.release()
    cv.destroyAllWindows()

def scrape_keyframe(frame, reader):

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
            result = reader.readtext(threshold, paragraph="False", detail=0)
            print(result)
            save_strings[i] = result[0]
        except:
            print("No text found! No tag used?")
    
    return [(save_strings[0], save_strings[2]), (save_strings[1], save_strings[3])]
    

if __name__ == '__main__':


    start_time = time.time()

    process_video()

    end_time = time.time()

    sorted_start_times = sorted(game_start_times, key=lambda x: x[0])

    # pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'

    reader = easyocr.Reader(['en'])

    for f,val,image in sorted_start_times:
        datetime_start_time = datetime.timedelta(seconds=f)
        print(f"Game start at : {datetime_start_time}. Conf Value: {val}")

        print(scrape_keyframe(image, reader))
        # cv.imshow(f"{datetime_start_time}", image)
        # key = cv.waitKey(0) & 0xFF

    elapsed_time = end_time - start_time
    print(f"Elapsed: {elapsed_time}")
