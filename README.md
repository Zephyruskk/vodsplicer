# Smash Ultimate VOD Splicing Assistant (VSA)

## Intro
The premise of this project is simple -- I love providing VODs to my local smash community. However, it can be kind of a pain to handle the logistics of the 2-3 hour recording we create at each weekly. I tried making a system wherein each player would enter their names and start the recording before starting their match, but this was unfruitful. 

Therefore, I wrote a script that could watch the video for me and tell me when matches start (`analyzer.py`), as well as one to splice and upload the videos for me (`splicer.py`). Wrapped it together with a GUI (`vodsplicer_gui.py`) and some YouTube API magic (`upload_video.py`), and this is a tool which saves me a considerable amount of time and effort. Here's how to set it up 

I am going to assume basic computer literacy, but do my best to be accomodating. I have experience with Windows and Ubuntu -- hopefully the Linux stuff can carry over to MacOS.

**DISCLAIMER**: This software assumes that Smash Ultimate is recorded at 1080x1920, and is fullscreen while the beginning of games. If your VOD is recorded at a quality other than 1080p, or changes the size/aspect ratio of the actual gameplay, there may need to be some adjustments made to the script to work properly. Please feel free to contact me if you have any questions or worries of this nature at @zephyruskk on Twitter and @zephyrsk on Discord.

## Requirements
### **Python**
This project was developed on Python v3.10.11. It is recommended that you use the latest version of Python, but at least version 3.7 is *required*. To check which version of Python you have installed, open a terminal session -- `Ctrl+Alt+t` on Ubuntu, press the Windows key and type 'cmd' on Windows -- and type `python --version`. 

If you do not have Python installed, you can download Python and find instructions for installation here: https://www.python.org/downloads/.
### **Pip**
This should come with your Python installation. If you are unsure of this for some reason, you can open a terminal session and type `pip --version` to verify that it is installed. We will use this later to install the necessary packages for this project. 

### **Tesseract**
Tesseract is what this project uses for OCR (text recognition). The installation method will depend on your operating system.

For Windows, there is an installer available at https://github.com/UB-Mannheim/tesseract/wiki. Download the latest version and follow the instructions to install Tesseract. It will likely install to a folder called `Tesseract-OCR` in your Program Files. Inside of this directory should be a file called `tesseract.exe`. Save the path to this `.exe` file for later. Or, optionally, add it to your PATH variable, if desired. Again, modifying your PATH is optional. 

For Ubuntu, we can use the built-in package manager system to install Tesseract. Per the directions from https://tesseract-ocr.github.io/tessdoc/Installation.html, run the following commands 
```
sudo apt install tesseract-ocr
sudo apt install libtesseract-ocr
```
Although, we can also use `snap` for this, if preferred. 

For MacOS, Tesseract can be installed with 
```
brew install tesseract
```
The tesseract directory can then be found with `brew info tesseract`, which you may need later. 

### FFmpeg
You would be surprised at how many machine FFmpeg is present on without the user's knowledge as it is quite omni-present. Just type `ffmpeg` into a terminal session to determine if it is installed. Most Mac and Linux users will find it is already installed. Follow the instructions here if you need to install it: https://www.hostinger.com/tutorials/how-to-install-ffmpeg.

### **The YouTube API (optional)**
Included in this project is a script which lets the user automatically upload spliced videos once they are done processing. This is totally optional and requires some work on the user's behalf. This is an excellent video which details what you speficially have to do for this project: https://www.youtube.com/watch?v=aFwZgth790Q. Here is a brief summary of the steps.
- Navigate to `cloud.google.com` and sign in. I will note that this account does not necessarily have to be the same account you wish to upload videos onto.
- Click `Console`.
- Click the `Select a project` dropdown and click `New Project`. Choose a descriptive name (something like VODSplicer Upload... or something). You may leave the 'Location' filed as 'No organization'.
- Create the project and wait for it to finish initializing. The site should notify you when it's done and this should only take a few seconds. Once done, select your new project. 
- You should now see your project's name in the top bar of your page. On the left, there should be a menu opened. If not, click the three-bars icon next to the Google Cloud logo. 
- Select `API & Services` and then select `Enabled APIs & services`.
- Click `ENABlE APIS AND SERVICES`. Search for "Youtube Data API v3" and click the result. Hit `Enable`. It may take a few seconds to process. 
- Once the API has been enabled, select `OAuth consent screen` under `API & Services`. 
- Select `External` and confirm. 
- You should now be at the `Edit app registration` page. Fill out the required information. Save and continue. 
- You should now be in the `Scopes` tab. Click `Add or remove scopes`. 
- Search for "upload a video". Check the scope `.../auth/youtube.upload` under the `YouTube Data API v3` API (make sure it is checked!), and hit `Update`. Save and continue. 
- You should now be in the `Test users` tab. Click `Add Users`. Type in the GMail account of the user with the YouTube account that you wish to upload your VODs to. **THIS IS WHERE IT IS IMPORTANT TO ENSURE THAT YOU ARE CHOOSING THE CORRECT ACCOUNT**. Once you have entered this account into the box, hit `Add`. Save and continue. 
- Navigate to the `Credentials` tab from the left of the screen. Click `Create Credentials` and select `OAuth client ID`. Select `Desktop App` for the Application type, give a name, and hit create. 

If all went well, you now have the credentials necessary to access the YouTube API. Later in this README, there will be a section which specifies what to do with these credentials. 

## Setup

Before anything, please feel free to contact me if you have any issues with this. I am @Zephyruskk on Twitter and @zephyrsk on Discord. 

1. Download this repository! Click `<> Code` and then "Download ZIP". Extract this folder (on Windows, `Extract all`) and move the resulting folder to a safe, accessible location. I recommend the Videos directory in whatever OS you are using. 

2. If you have not added Tesseract to your PATH, navigate into the `user_info` directory and find the file called `tesseract_path.txt`. If it is not present, create it! Place the path to your Tesseract installation into this file. There shouldn't be anything else in this file, just a single line. 

3. Run `install_pip_packages.py` with Python to download this project's dependencies  
If you prefer to do this manually for one reason or another, here are the packages you need and how to install them. Copy and paste the following instructions into a terminal and hit enter (if needed). You can open a terminal in Windows by hitting the Windows key and typing "cmd". In Ubuntu, you can do this with `Ctrl+Alt+t`. 
```bash
(If you choose not use the installer script)
pip install Levenshtein
pip install Pillow
pip install pytesseract
pip install opencv-python
pip install --upgrade google-api-python-client
pip install --upgrade google-auth-oauthlib google-auth-httplib2
pip install oauth2client
```

4. (Optional) If you want to use the YouTube API aspect of this process, find the `client_secrets.json` file in the `user_info` directory of this project. It should look something like this
```json
"client_id": "[[INSERT CLIENT ID HERE]]",
"client_secret": "[[INSERT CLIENT SECRET HERE]]",
```
<ul>Replace `[[INSERT CLIENT ID HERE]]` with your YouTube API client ID, and replace `[[INSERT CLIENT SECRET HERE]]` with your client secret. If you do not know what I am talking to, refer to the **Requirements** section of this document. If you do not know where to find this, but do have the YouTube API setup in a Google Cloud project, navigate to your project, to the side menu, to the `APIs & Services` page, to `Credentials`, and then click on your credentials under `OAuth 2.0 Client IDs`.</ul>

When you run the splicer with automatic uploads on, you will be required to log in to the account you want your VODs to be uploaded to. This should be an authenticated user on your Google Cloud project. 

## Usage
To use this software, run `vodsplicer_gui.py`. There are a couple ways to do this. If you are on Windows, you can right click the file in File Explorer, and select run with Python (which may be called something like "Python 3.10"). If you have multiple options for Python installations to use to run the file, you may come across compatability issues. I would recommend using the same distribution you used on `install_pip_packages.py`. Here is what the GUI should look like. 

![image](https://github.com/Zephyruskk/vodsplicer/assets/106562693/b5a67467-81d2-4268-9957-b2e7b0276bd6)

`Select Input for Analyzer` is where you should start. Clicking this button will open your system's file explorer. Select the VOD that you want to splice. This process will probably take the longest out of any operation (except maybe uploading). It takes my laptop about 14-15 minutes to get through a 2 hour 50 minute VOD. **Please do not move your VOD from it files location until you are positive that each match has been spliced.**

Once this operation is complete, there will be a directory created from your VODs filename under the `sheets` directory of this project. Navigate into this directory, and you will find a `.csv` file that outlines when games start. **THIS STEP IS VERY IMPORTANT** -- It is the only step that cannot be automated. It is now *your* job, to fill in some details. 

Firstly, the analyzer can only extract the in-game tags players use, which is often different from the name they use to enter tournaments with. Fill in the `Player 1` and `Player 2` columns with the appropriate tags, found in your tournaments' bracket. There are a couple important notes to make here. Firstly, Tesseract struggles a bit to get tags 100% correct. As such, there may be occasional typos or extra characters added to tags. Feel free to fix these errors, as that will help with a later component of VSA. If tags are left blank (default controls), then often there will be some nonsense characters in the place of a tag. Again, feel free to amend this. If you have previously run `splicer.py`, my software will attempt to autofill player names based on their in-game tags. This is why it is important to fix this spreadsheet at this step.

The next step is to assign games to set numbers. Games that follow each other chronologically and have the same set number will be spliced together as games of the set set. Again, `analyzer.py` will attempt to guess when sets start and end based on changes to tags, but this is not always accurate. It is hard to predict when sets change if, for instance, the same person plays on a recording setup for multiple sets in a row, or if someone changes their tag mid-set. Amend these as you see fit. Note that it is not important that the set numbers ascend in order as long as they are different from each other. Consider if two sets were accidentally both marked as set number 2. Rather than changing the second set of the pair to number 3 and having to reorder subsequent sets, try assigning it number 52, or something like that. 

Once the VOD's csv file is sufficiently edited, you can click `Select Input for Splicer` and select that csv file. FFmpeg will then begin splicing the VOD into individual videos of each set. If you have checked `Upload to YouTube`, the splicer will attempt to upload each video to YouTube as it is finished (with a pre-generated title). Note that the first time you attempt this with `Upload to YouTube` checked, you will most likely have to log in with the Google account that holds the YouTube channel you wish to upload to. Note that the uploading script will be a "**child process**" of the analyzer and, hence, the GUI. Do not close the GUI until the videos are finished uploading (even if the splicer says it is done), as this will result in unpredictable behavior. Once videos begin "processing" on your YouTube creator dashboard, you should be set to close everything. 

The standard output of the scripts is supplied at the bottom of the GUI for debugging. 

## Thank you!
I hope you'll consider using this project for splicing your VODs. Again, please contact me @zephyrsk on Discord or @zephyruskk on Twitter with any questions or concerns. 

## Credits
OpenCV, Tesseract, and this project are licensed under Apache License 2.0. A copy of this can be found under `CREDITS/LICENSE`.
  
FFmpeg uses the GNU Lesser General Public License, version 2.1, which can be found on gnu.org.

Copyright 2023 Zachary Scott