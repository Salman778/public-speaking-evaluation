import tkinter as tk
from tkinter import ttk, filedialog

from PIL import ImageTk, Image
from cv2 import cv2
from emotion_recognition import get_emotion_predictions

import matplotlib
from matplotlib import style, pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import numpy as np

matplotlib.use("TkAgg")

LARGE_FONT = ("", 12)

video_path = 0

emotions = ('angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral')
style.use('fivethirtyeight')

y_pos = np.arange(len(emotions))


class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.iconbitmap(self, default="assets/app_icon.ico")
        tk.Tk.title(self, "Public Speaking Evaluation")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for f in (StartPage, EmotionRecognitionPage):
            frame = f(container, self)
            self.frames[f] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(StartPage)

    def show_frame(self, cont):
        # show the passed page class
        frame = self.frames[cont]
        frame.tkraise()


class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        logo = ImageTk.PhotoImage(Image.open(
            "assets/app_icon.png"), master=self)
        logo_label = ttk.Label(self, image=logo)
        logo_label.image = logo
        logo_label.pack()

        # Label to explain how to use the buttons
        start_label = ttk.Label(self, text="Load a video or click stream to analyze emotions",
                                font=LARGE_FONT)
        start_label.pack(pady=10, padx=10)
        btn_frame = ttk.Frame(self)
        btn_frame.pack()

        # Load button to load a video
        load_btn = ttk.Button(btn_frame, text="Load Video",
                              command=lambda: self.load_video(controller))
        load_btn.pack(pady=10, padx=10, side="left")

        # Stream button to run the webcam
        stream_btn = ttk.Button(btn_frame, text="Streaming",
                                command=lambda: self.streaming(controller))
        stream_btn.pack(pady=10, padx=10, side="left")

    def load_video(self, controller):
        global video_path
        filetypes = [
            ("Video Files", ("*.mp4", "*.avi")),
            ("MP4", '*.mp4'),
            ("AVI", '*.avi'),
            ('All', '*')
        ]
        video_path = filedialog.askopenfilename(
            title="Select video", filetypes=filetypes)

        if video_path:
            controller.show_frame(EmotionRecognitionPage)

    def streaming(self, controller):
        global video_path
        video_path = 0
        controller.show_frame(EmotionRecognitionPage)


class EmotionRecognitionPage(tk.Frame):
    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="top")

        # Back button to go back to the StartPage
        back_btn = ttk.Button(
            btn_frame, text="Back", command=lambda: self.back_to_start_page(controller))
        back_btn.pack(pady=10, padx=10, side="left")

        # Start/Stop button  to start/stop analyzing
        self.start_stop_btn = ttk.Button(
            btn_frame, text="Start", command=self.start_stop)
        self.start_stop_btn.pack(pady=10, padx=10, side="right")

        # state of analyzing label
        self.initial_state_analyzing = "Press Start to begin analyzing"
        self.state_analyzing = ttk.Label(self,text=self.initial_state_analyzing, font=LARGE_FONT)
        self.state_analyzing.pack()

        # initalize the video variable and create its frame and label
        self.video = None
        self.video_frame = tk.Frame(self)
        self.video_frame.pack()
        self.video_label = tk.Label(self.video_frame)

        # creating and setting up the bar graph
        self.fig_bar = Figure(figsize=(8,8))
        self.ax_graph = self.fig_bar.add_subplot(111)
        self.fig_bar.subplots_adjust(left=0.10)
        self.bars = self.ax_graph.bar(y_pos, np.zeros(
            len(emotions)), align='center', alpha=0.5)
        self.ax_graph.set_ylabel('percentage')
        self.ax_graph.set_title('emotion')
        self.ax_graph.set_xticks(y_pos)
        self.ax_graph.set_xticklabels(emotions)
        self.ax_graph.set_yticks(np.arange(0, 110, 10))

        self.canvas_bar = FigureCanvasTkAgg(self.fig_bar, self.video_frame)
        self.canvas_bar.draw()

        #creating and setting up th line graph
        self.fig_line = Figure(figsize=(8,8))
        self.ax_line = self.fig_line.add_subplot(111)
        self.fig_line.subplots_adjust(left=0.10)
        self.ax_line.set_ylabel('Percentage of Emotion')
        self.ax_line.set_title('Percentage Through Time')
        self.ax_line.set_yticks(np.arange(0, 110, 10))    
        self.canvas_line = FigureCanvasTkAgg(self.fig_line, self.video_frame)
        #initializing emotions dictionary for data to be used in drawing the line graph for each emotion
        self.data_emotions = {emotion: np.array([]) for emotion in emotions}
        print("first\n" , self.data_emotions)
        
        # pregress bar for loading the video and analyzing it
        self.progress_bar = ttk.Progressbar(
            self.video_frame, orient='horizontal', length=270, mode='determinate')

        # average of emotion to count all predictions and devide on number of frames
        self.average_emotion = np.zeros(len(emotions))
        self.numb_of_frames = 0

    def start_stop(self):
        # Check if clicked button is Start convert button to Stop
        if self.start_stop_btn.cget("text") == "Start":
            self.start_stop_btn.config(text="Stop")
            self.state_analyzing.config(text="Analyzing")
            self.average_emotion = np.zeros(len(emotions))
            self.numb_of_frames = 0
            self.data_emotions = {emotion: [] for emotion in emotions}

            self.canvas_line.get_tk_widget().forget()

            if video_path == 0:
                self.video_label.pack(pady=10, padx=10, side="left")
                self.canvas_bar.get_tk_widget().pack(
                    pady=10, padx=10, side="right", fill="both", expand="1")
        
            self.start_video()

        #chack if clicked button is Stop convert it to Start
        elif self.start_stop_btn.cget("text") == "Stop":
            self.video.__del__()
            self.start_stop_btn.config(text="Start")
            self.state_analyzing.config(text="Analyzing results")
            self.video_label.forget()
            self.canvas_bar.get_tk_widget().forget()
            self.canvas_line.get_tk_widget().forget()
            self.show_average()

    def show_average(self):
        self.canvas_bar.get_tk_widget().pack(pady=10, padx=10, side="left")

        self.canvas_line.get_tk_widget().pack()
        self.average_emotion /= self.numb_of_frames
        self.draw_bar_chart(self.average_emotion)
        self.draw_line_chart()

    def start_video(self):
        global video_path
        self.video = VideoCapture(video_path)
        if video_path:
            self.progress_bar.pack(expand=True, fill="both")
            self.load_video()
        else:
            self.stream_video()

    def stream_video(self):
        # read the video from the streaming camera and analyze it
        ret, frame = self.video.get_frame()
        if ret:
            frame, emotion_predictions = get_emotion_predictions(frame)

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = ImageTk.PhotoImage(
                image=Image.fromarray(frame), master=self.video_frame)
            self.video_label.imgtk = image
            self.video_label.config(image=image)
            if(emotion_predictions.all(0)):
                self.add_predictions_data(emotion_predictions)
            self.draw_bar_chart(emotion_predictions)
            self.video_label.after(1, self.stream_video)

        else:
            self.video_label.forget()

    def load_video(self):
        # get the number of frames in the video
        count_frames = int(self.video.count_frames())
        self.progress_bar.config(maximum=count_frames)

        # read video and analyze it
        ret, frame = self.video.get_frame()
        if ret:
            frame, emotion_predictions = get_emotion_predictions(frame)
            if(emotion_predictions.all(0)):
                self.add_predictions_data(emotion_predictions)
            self.progress_bar.step(1)
            self.progress_bar.after(1, self.load_video)
        else:
            # remove progress barstop loading and
            self.progress_bar.forget()
            self.start_stop()
    
    def add_predictions_data(self, emotion_predictions):
        self.average_emotion += emotion_predictions
        self.numb_of_frames += 1
        for data_emotion, prediction in zip(self.data_emotions, emotion_predictions):
            print("adding\n" , self.data_emotions)
            self.data_emotions[data_emotion].append(prediction * 100)

    def draw_bar_chart(self, emotion_predictions):

        emotion_predictions *= 100
        for rect, h in zip(self.bars, emotion_predictions):
            rect.set_height(h)
        self.canvas_bar.draw()
    
    def draw_line_chart(self):
        # This function is to draw line graph for each emotion

        # Lopp throught the data prediction to normalize it
        for data_emotion in self.data_emotions:
            self.data_emotions[data_emotion] = np.array_split(self.data_emotions[data_emotion], 100)
            for index, emotion_prediction in enumerate(self.data_emotions[data_emotion]):
                if emotion_prediction.any():
                    self.data_emotions[data_emotion][index] = emotion_prediction.mean()
                else:
                    self.data_emotions[data_emotion][index] = np.nan

        self.ax_line.clear()
        for data_emotion in self.data_emotions:
            self.ax_line.plot(np.arange(0,100),self.data_emotions[data_emotion], label=data_emotion)
        
        self.ax_line.set_yticks(np.arange(0, 110, 10))
        self.ax_line.set_xticks(np.arange(0, 110, 10))
        self.ax_line.set_ylabel('Percentage of Emotion')
        self.ax_line.set_title('Percentage Through Time')
        self.fig_line.legend()
        self.canvas_line.draw()
        
        
   
    def back_to_start_page(self, controller):
        if self.video:
            self.video.__del__()
        self.state_analyzing.config(text=self.initial_state_analyzing)
        self.start_stop_btn.config(text="Start")
        self.canvas_bar.get_tk_widget().forget()
        self.canvas_line.get_tk_widget().forget()
        self.video_label.forget()
        controller.show_frame(StartPage)


class VideoCapture:
    def __init__(self, video_path=0):
        self.video = cv2.VideoCapture(video_path)
        if not self.video.isOpened():
            raise ValueError("Couldn't open video file", video_path)

    def get_frame(self):
        if self.video.isOpened():
            ret, frame = self.video.read()
            if ret:
                return (ret, frame)
            else:
                return (ret, None)
        else:
            return(False, None)

    def count_frames(self):
        return self.video.get(cv2.CAP_PROP_FRAME_COUNT)

    def __del__(self):
        if self.video.isOpened():
            self.video.release()


if __name__ == "__main__":
    App().mainloop()
