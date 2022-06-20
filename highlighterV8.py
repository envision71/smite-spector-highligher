from tkinter import *
import tkinter
from tkinter import filedialog
from tkinter.messagebox import showinfo
from tkinter.ttk import Progressbar
from proglog import ProgressBarLogger, TqdmProgressBarLogger
from Screen_Cap import screen_record as screen
from moviepy.editor import*
import cv2 as cv
import numpy as np
import tkinter as tk
import os

#set up multiple a ROI class to make managing multiple ROI's easier
class ROI:
    def __init__(self, name,roi=[0]):
        self.name = name
        self.roi = roi
        self.toggle = False

class aClip:
    def __init__(self,start,end):
        self.start=start
        self.end=end

    def getStart(self):
        return self.start
    def getEnd(self):
        return self.end
    def setEnd(self,time):
        self.end=time

class MyBarLogger(ProgressBarLogger):
    pb = None
    def set_progressbar(self,pb):
        self.pb = pb
        

    def callback(self, **changes):
        # Every time the logger is updated, this function is called with
        # the `changes` dictionnary of the form `parameter: new value`.

        for (parameter, new_value) in changes.items():
            print ('Parameter %s is now %s' % (parameter, new_value))

    def bars_callback(self, bar, attr, value,old_value=None):
        # Every time the logger progress is updated, this function is called        
        percentage = (value / self.bars[bar]['total']) * 100
        self.pb["maximum"] = 100
        #print(bar,attr,percentage)
        if self.pb is not None and bar == "t":
            self.pb["value"] = int(percentage)
            self.pb.update()



def highlighter(videoPath,outputPath,afterTime,beforeTime,debugv,pb,status_label):
    #Debug mode toggle
    debug = debugv
    #input video
    video = videoPath
    #output file location
    outputfileName = outputPath
    #create the video reader
    cap = cv.VideoCapture(video)
    #get the fps of the video
    fps = cap.get(cv.CAP_PROP_FPS)
    #get the diminsions of the video
    width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
    height =int( cap.get(cv.CAP_PROP_FRAME_HEIGHT))
    #initalize the list to hold the clips
    clip = VideoFileClip(video)
    clipsArray= []
    #the seconds to clip before an event
    Seconds_Before_Kill = beforeTime
    Seconds_After_Kill = afterTime
    #get the max number of frames in the video to hard cap the clips end point.
    maxFrameNum = cap.get(cv.CAP_PROP_FRAME_COUNT)
    pauseImg = cv.imread("pause.jpg")
    pauseImg = cv.resize(pauseImg,(900,600),fx=0,fy=0,
                            interpolation=cv.INTER_CUBIC)

    startCheck = 0
    endCheck = 0
    file=0
    pauseFlag = False

    pb['maximum'] = maxFrameNum
    status_label['text'] = "Scanning Video"

    #toggle is need to capture the point HP
    #goes under a threshold. Otherwise its
    #creating a new clip for every frame
    #someone is under that threshold.
    #blue team roi dictionaries 
    blue1 = {"name":"blue1","toggle":True}
    blue2 = {"name":"blue2","toggle":True}
    blue3 = {"name":"blue3","toggle":True}
    blue4 = {"name":"blue4","toggle":True}
    blue5 = {"name":"blue5","toggle":True}

    #red team roi dictionaries
    red1 = {"name":"red1","toggle":True}
    red2 = {"name":"red2","toggle":True}
    red3 = {"name":"red3","toggle":True}
    red4 = {"name":"red4","toggle":True}
    red5 = {"name":"red5","toggle":True}

    #map objectives roi. Currently not used.
    roiGold = {"name":"goldfurry","toggle":True}
    roiFire = {"name":"firegiant","toggle":True}


    #while the video is being read.
    while (cap.isOpened()):

        #read the frame
        ret,frameOG = cap.read()

        #if end of video.
        if not ret:
            #destroy the windows
            cap.release()
            cv.destroyAllWindows()
            pb['maximum'] = len(clipsArray)
            pb['value'] = 0
            status_label['text'] = "Creating Video"
            #Movie clip list. Other lists can be added incase other videos
            #want to addded.
            movie = []
            if len(clipsArray) > 0:
                #go over the clips array to create the video
                for idx, val in enumerate(clipsArray):
                    clip1=clip.subclip(val.getStart(),val.getEnd())
                    movie.append(clip1)

            if debug: print("concatenating video clips")
            pb['maximum'] = 100
            pb['value'] = 0
            #create a logger to track the progress of combining the clips
            log_clips = MyBarLogger()
            log_clips.set_progressbar(pb)
            #create and publish the combined clips
            final_clip = concatenate_videoclips(movie)
            final_clip.write_videofile(outputfileName + ".mp4",logger=log_clips)
            status_label['text'] = "Created Video"
            pb['value'] = 0
            if debug: print("created video at " + outputfileName)
            break
        #display the frame.
        frame = cv.resize(frameOG,(900,600),fx=0,fy=0,
                           interpolation=cv.INTER_CUBIC)

        #blue team roi
        blue1['roi'] = frame[320:325,40:61]
        blue2['roi'] = frame[340:345,40:61]
        blue3['roi'] = frame[360:365,40:61]
        blue4['roi'] = frame[380:385,40:61]
        blue5['roi'] = frame[400:405,40:61]

        #red team roi
        red1['roi'] = frame[320:325,840:861]
        red2['roi'] = frame[340:345,840:861]
        red3['roi'] = frame[360:365,840:861]
        red4['roi'] = frame[380:385,840:861]
        red5['roi'] = frame[400:405,840:861]

        #list of roi dictionaries
        aroi= [blue1,blue2,blue3,blue4,blue5,
                red1,red2,red3,red4,red5]
                #roiGold,roiFire]
        
        #gold and fire roi
        roiGold['roi'] = frame[57:68,0:100]
        roiFire['roi'] = frame[21:30,0:100]

        progress(pb,maxFrameNum)

        #Get the diffrance of the frame vs the pause screen to
        #know when the game is paused.
        difference =cv.subtract(pauseImg,frame)
        b,g,r = cv.split(difference)
        if (np.mean(b) < 3 and
            np.mean(g) < 13 and
            np.mean(r) < 17 and
            pauseFlag==True):
                if debug: print("game is unpaused")
                pauseFlag =False        
        if (np.mean(b) > 3 and
            np.mean(g) > 16 and
            np.mean(r) > 21):
                if debug: print("game is paused")
                pauseFlag=True
        #get current frame number
        currentFrameNum = cap.get(cv.CAP_PROP_POS_FRAMES)
        #search through all the RROIs
        for e in aroi:
            #mask for green in an image
            mask = cv.inRange(e['roi'],(0,0,0),(100,100,100))
            #ratio of how much green to other
            ratio = ((mask.size-cv.countNonZero(mask)))/(mask.size)
            #if green is below a threshold then start the clip
            if(ratio<0.14):
                if(e['toggle'] == True and pauseFlag == False):
                    #create the start and end points for a clip.
                    start=int((currentFrameNum/fps)-(Seconds_Before_Kill))
                    end= int((currentFrameNum/fps)+(Seconds_After_Kill))
                    if debug: print("og start {0} og check {1}".format(start,startCheck))
                    #if the start of the clip is sometime between the previous
                    #clip then instead extend the end point of the previous clip.
                    if (start-startCheck<=(Seconds_Before_Kill+Seconds_After_Kill) or
                        start<=endCheck):
                        if debug: print("changing start to check")
                        start= startCheck
                        if len(clipsArray) != 0:
                            del clipsArray[-1]
                    else:startCheck=start

                    if start<=0: start =0
                    if end>= int(maxFrameNum)/fps:
                        end = (int(maxFrameNum)/fps)-1
                    endCheck=end                    
                    if debug: print("starting clip at {0} and ending at {1} for a length of {2}".format(int(start),int(end),int(end-start)))
                    #create the clip and add it to the array.
                    clip1 = aClip(start,end)
                    clipsArray.append(clip1)
                    if debug: print(len(clipsArray))
                            
                    e['toggle']=False
                    if debug: print("{0} has raitio {1} {2}".format(e['name'], ratio,e['toggle']))
            if(e['toggle'] ==False):
                if(ratio>0.3):
                    e['toggle']=True
                    if debug: print("{} revived".format(e['name']))


        #used for getting clips of objects currently not used.
        mask = cv.inRange(roiGold['roi'],(0,0,0),(100,100,100))
        ratio = ((mask.size-cv.countNonZero(mask)))/(mask.size)
        if debug: cv.imshow('Debug', frame)

        # press Q for emergancy stop 
        if cv.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv.destroyAllWindows()
            break
        
    cap.release()
    cv.destroyAllWindows()

def open_videos(FilePath_Box):
    file = filedialog.askopenfile(initialdir="C/", title="Select a file", filetypes=[('Video files', '*.mp4')])
    if file is not None:
        FilePath_Box.set(file.name)

def open_folder(OutputFolder_Box):
    folder = filedialog.askdirectory()
    if folder is not None:
        OutputFolder_Box.set(folder)


def check_submit(videoPath,outputPath,afterTime,beforeTime,debug,pb,status_label):
    if not os.path.isfile(videoPath) or not (".jpg" in videoPath or ".png" in videoPath or ".mp4" in videoPath):
        tkinter.messagebox.showinfo("Error",  "Not a valid path for video.")
    elif not os.path.isdir(outputPath):
        tkinter.messagebox.showinfo("Error",  "Not a valid output folder.")
    highlighter(videoPath,outputPath,afterTime,beforeTime,debug,pb,status_label)


def progress(pb,max):
    if pb['value'] < max:
        pb['value'] += 1
        pb.update()
        
    else:
       showinfo(message='The progress completed')


def main():
    
    root = tk.Tk()
    root.title("Smite Spectator Highlighter")
    #Main menue frame
    Menu_Frame = Frame(root)
    #ProgressBarFrame
    PBFrame = Frame(root)


    #Progress bar widget
    pb = Progressbar(PBFrame, orient = 'horizontal', length = 100, mode = 'determinate')
    pb_Label = tk.Label(PBFrame,text = "Progress")
    status_label = tk.Label(PBFrame,text = "Not Working")
    pb_Label.grid(row=0,column=0)
    pb.grid(row=0,column=1)
    status_label.grid(row=0,column=2)
    
    

    #Variables
    videoPath = StringVar(name = "videoPath")
    outputPath = StringVar(name = "outputPath")
    Seconds_Before_Kill = IntVar(name= "Seconds_Before_Kill", value = 15)
    Seconds_After_Kill = IntVar(name= "Seconds_After_Kill", value = 15)
    Debug = BooleanVar(name = "Debug",value=False)


    #Entry Boxes
    videoPath_Box = tk.Entry(Menu_Frame,textvariable=videoPath)
    OutPath_Box = tk.Entry(Menu_Frame,textvariable=outputPath)
    Seconds_Before_Kill_Box = tk.Entry(Menu_Frame,textvariable=Seconds_Before_Kill)
    Seconds_After_Kill_Box = tk.Entry(Menu_Frame,textvariable=Seconds_After_Kill)

    #Labels
    pathInTextBox_Label = tk.Label(Menu_Frame,text = "Path to video")
    pathOutTextBox_Label = tk.Label(Menu_Frame,text = "Path to save video to")
    Seconds_Before_Kill_Label = tk.Label(Menu_Frame,text = "Seconds before a kill happens to capture")
    Seconds_After_Kill_Label = tk.Label(Menu_Frame,text = "Seconds after a kill happens to capture")

    #Buttons
    InputBrowse_Button = tk.Button(Menu_Frame, text="Browse", command=lambda:open_videos(videoPath))
    OutputBrowse_Button = tk.Button(Menu_Frame, text="Browse", command=lambda:open_folder(outputPath))
    submitButton = tk.Button(Menu_Frame, text="Submit", command= lambda: check_submit(videoPath.get(),outputPath.get(),
                                                                                    Seconds_After_Kill.get(),Seconds_Before_Kill.get(),
                                                                                    Debug.get(),pb,status_label))
    Debug_Button = tk.Checkbutton(Menu_Frame,text="Debug",variable=Debug)

    #Input grid
    pathInTextBox_Label.grid(row=0,column=0,sticky=W)
    videoPath_Box.grid(row=0,column=1,sticky=W)
    InputBrowse_Button.grid(row=0,column=2,sticky=W)
    #output grid
    pathOutTextBox_Label.grid(row=1,column=0,sticky=W)
    OutPath_Box.grid(row=1,column=1,sticky=W)
    OutputBrowse_Button.grid(row=1,column=2,sticky=W)

    #Timing Grid
    Seconds_Before_Kill_Label.grid(row=3,column=0,sticky=W)
    Seconds_Before_Kill_Box.grid(row=3,column=1)
    Seconds_After_Kill_Label.grid(row=4,column=0,sticky=W)
    Seconds_After_Kill_Box.grid(row=4,column=1)

    submitButton.grid(row=5,column=1,sticky=W)
    Debug_Button.grid(row=5,column=2)
    
    Menu_Frame.pack()
    PBFrame.pack()
    root.mainloop()


if __name__=="__main__": 
    main() 

