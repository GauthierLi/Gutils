import os 
import cv2
import queue
import numpy as np
import tkinter as tk
from skimage.metrics import structural_similarity as ssim

from tkinter import Canvas
from copy import deepcopy
from typing import Any, List, Dict
from PIL import Image, ImageTk, ImageGrab

class VideoSelector:
    def __init__(self, video_path):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        self.ret, self.frame = self.cap.read()
        if not self.ret:
            raise ValueError("Could not read video.")

        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        self.root = tk.Tk()
        self.root.title("Video Frame Selector")

        self.canvas = Canvas(self.root, width=self.frame.shape[1], height=self.frame.shape[0])
        self.tk_image = ImageTk.PhotoImage(image=Image.fromarray(self.frame))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.pack()

        self.rect = None
        self.start_x = None
        self.start_y = None

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.root.mainloop()

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def on_mouse_drag(self, event):
        cur_x, cur_y = (event.x, event.y)
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, cur_x, cur_y, outline='red')

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, end_x, end_y, outline='blue', fill='')
        self.selected_region = (self.start_x, self.start_y, end_x, end_y)
        print(f"Selected Region: {self.selected_region}")
        self.root.destroy()

    def get_selected_region(self):
        return self.selected_region

def distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2 
    return np.sqrt((x1-x2)**2 + (y1-y2)**2)


class Tracker(object):
    def __init__(self, video_path: str) -> None:
        self.selector = VideoSelector(video_path)
        self.cap = cv2.VideoCapture(video_path)
        selected_region = self.selector.get_selected_region()
        x1, y1, x2, y2 = selected_region
        print("Selected Region (after closing the window):", selected_region)

        self.template = self.selector.frame[y1:y2, x1:x2]
        cv2.imshow("Cropped Frame", self.template[:,:,::-1])
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        self.trakers = []
        self.max_distance = -1
        self.last_pos = None
        self.margin = 15
        self.stop_replace = False

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        while True:
            gray_template = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY) 
            ret, frame = self.cap.read()
            ori_frame = deepcopy(frame)
            if not ret: break
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(gray_frame, gray_template, cv2.TM_CCORR_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            h, w = self.template.shape[:2]
            top_left = max_loc 
            bottom_right = (top_left[0] + w, top_left[1] + h)

            if self.last_pos is not None:
                cur_dis = distance(self.last_pos[0], top_left)
                if self.max_distance == -1:
                    self.max_distance = cur_dis
                else:
                    if cur_dis < 10 * self.max_distance and not self.stop_replace:
                        self.max_distance = max(cur_dis, self.max_distance)
                        if max_val > 0.92:
                            ssim_compare = ssim(cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY), cv2.cvtColor(ori_frame[top_left[1]: bottom_right[1], top_left[0]: bottom_right[0], :], cv2.COLOR_BGR2GRAY))
                            print("ssim: ", ssim_compare)
                            self.template = ori_frame[top_left[1]: bottom_right[1], top_left[0]: bottom_right[0], :]
                            print("replace template: ", max_val)
                    else:
                        print(max_val)
                        top_left, bottom_right = self.last_pos

            self.last_pos = [top_left, bottom_right]
            if top_left[0] > self.margin and top_left[1] > self.margin and\
                bottom_right[0] < 960 - self.margin and bottom_right[1] < 576 - self.margin:
                cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)
                self.stop_replace = False
            else:
                cv2.rectangle(frame, top_left, bottom_right, (0, 0, 255), 2)
                self.stop_replace = True
            cv2.imshow('Tracking', frame) 
            cv2.imshow("Template", cv2.cvtColor(self.template, cv2.COLOR_BGR2RGB))
            if cv2.waitKey(0) & 0xff == ord('q'):
                break
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    video_path = "/tmp/24-12-09/YR-C01-42_20241204_111225.Heavy_Topic_Group.bag.mp4"
    tracker = Tracker(video_path)
    tracker()


