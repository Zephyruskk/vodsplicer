import sys, datetime, time, logging
import cv2 as cv
import numpy as np
import pytesseract
import threading
import multiprocessing as mp


p2_temp_threshold = 0.75
# x1, y1 = 960,20
# x2, y2 = 1080, 105

p1_coords = 20,40,80,90 # 10,20,100,100 # x1,y1,x2,y2
p2_coords = 980,40,1046,90 # 970,20,1060,100

batch_size = 16 # how many frames get checked at once (thread count!)
batch_item_length = 30 # frames long


# state variables 
game_start_times = []
game_start_frames = False



def process_frame(frame, frame_number, template, region_of_interest):
    global game_start_times

    x1,y1,x2,y2 = region_of_interest

    roi = frame[y1:y2, x1:x2]

    roi = cv.cvtColor(roi, cv.COLOR_BGR2GRAY)

    res = cv.matchTemplate(roi, template, cv.TM_CCOEFF_NORMED)
    # Find the location of the maximum correlation coefficient in the ROI
    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)

    if max_val <= p2_temp_threshold:
        return None

    game_start_times.append((frame_number, frame))

# load in keyframes, batch_size at a time
def process_video():

    vid_path = "./media/sample_0001.mkv"
    capture = cv.VideoCapture(vid_path)
    # capture = cv.VideoCapture("../obs_rec/aop-10_5_23/sample_Trim.mp4")
    p2_template = "./media/p2.png"
    p2_template = cv.imread(p2_template)
    p2_template = cv.cvtColor(p2_template, cv.COLOR_BGR2GRAY)  # convert to grayscale
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
                    t = threading.Thread(target=process_frame, args=(f[1], f[0], p2_template, p2_coords))
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
            game_start_times.pop(i)
    
    capture.release()
    cv.destroyAllWindows()

if __name__ == '__main__':


    start_time = time.time()

    process_video()

    end_time = time.time()

    sorted_start_times = sorted(game_start_times, key=lambda x: x[0])

    for f,image in sorted_start_times:
        datetime_start_time = datetime.timedelta(seconds=f)
        print(f"Game start at : {datetime_start_time}")

    elapsed_time = end_time - start_time
    print(f"Elapsed: {elapsed_time}")
