import cv2 as cv

def save_frame(frame, filename):
    cv.imwrite(filename, frame)
    print(f"Frame saved as {filename}")

def main():
    video_path = "C:/Users/zscot/Videos/vodfixer/media/sample_0001.mkv"
    capture = cv.VideoCapture(video_path)

    frame_count = 0
    frames_per_step = 30

    read = False

    while True:
        # Read a frame
        if not read:
            ret, frame = capture.read()
        if not ret:
            break
        else:
            read = True

        # Display the frame
        cv.imshow("Video", frame)

        # Check for user input
        key = cv.waitKey(0) & 0xFF

        if key == ord('q'):
            break

        if key == ord('s'):
            # Prompt for coordinates
            print("Enter the coordinates of the region to save (x1,y1,x2,y2):")
            coords = input().split(',')
            x1, y1, x2, y2 = [int(coord) for coord in coords]

            # Validate coordinates
            if x1 < 0 or y1 < 0 or x2 >= frame.shape[1] or y2 >= frame.shape[0]:
                print("Invalid coordinates!")
                continue

            # Extract the region of interest
            roi = frame[y1:y2, x1:x2]

            # Generate a unique filename based on frame count
            filename = f"frame_{frame_count}.png"

            # Save the region as an image
            save_frame(roi, filename)
            continue
        
        read = False

        # Move to the next frame
        for _ in range(frames_per_step - 1):
            capture.grab()
        frame_count += frames_per_step

    capture.release()
    cv.destroyAllWindows()

if __name__ == '__main__':
    main()
