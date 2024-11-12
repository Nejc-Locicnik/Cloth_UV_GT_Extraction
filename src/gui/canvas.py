import tkinter as tk
from PIL import Image, ImageTk
from ..utils.image_utils import *

class CanvasManager:
    def __init__(self, parent, settings):
        self.parent = parent
        self.settings = settings
        self._init_distance_calc()
        self._init_canvases()
        self.working_image = None
        self.distance_masks = []
        self.segment_masks = []
    
    def _init_distance_calc(self):
        method = self.settings.get("method")
        if method == "delta_e_2000":
            self.method = match_delta_e_2000
        elif method == "euclidean":
            self.method = hsv_match
            self.channels = self.settings.get("channels")
        else:
            raise "Wrong method settings in config.json"
        
    def _init_canvases(self):
        # Add two canvases side by side
        self.sz = self.settings.get("size")
        self.canvas1 = tk.Canvas(self.parent, bg="white", width=self.sz, height=self.sz)
        self.canvas1.grid(row=1, column=0, sticky="nsew")

        self.canvas2 = tk.Canvas(self.parent, bg="white", width=self.sz, height=self.sz)
        self.canvas2.grid(row=1, column=1, sticky="nsew")

    def open_image(self, img_path):
        c_space = f"BGR2{self.settings.get("proc_c_space")}"
        x_cut = (525, 1400)
        y_cut = (35, 910)

        self.working_image = resize_image(cutout(change_color_space(read_image(img_path), c_space), x_cut, y_cut), (self.sz,)*2)

        c_space = f"{self.settings.get("proc_c_space")}2{self.settings.get("display_c_space")}"
        self.image_tk_1 = ImageTk.PhotoImage(Image.fromarray(change_color_space(self.working_image, c_space)))
        self.canvas1.create_image(0, 0, anchor="nw", image=self.image_tk_1)
    
    def add_mask(self, color, threshold):
        dist = match_delta_e_2000(self.working_image, color)
        mask = threshold_color_distance(dist, threshold)
        self.distance_masks.append(dist)
        self.segment_masks.append(mask)

    def update_distance(self, color_idx, color, threshold):
        if color_idx < len(self.distance_masks): # index validity check
            dist = match_delta_e_2000(self.working_image, color)
            mask = threshold_color_distance(dist, threshold)
            self.distance_masks[color_idx] = dist
            self.segment_masks[color_idx] = mask

    def update_seg_mask(self, color_idx, threshold):
        if color_idx < len(self.distance_masks): # index validity check
            dist = self.distance_masks[color_idx]
            mask = threshold_color_distance(dist, threshold)
            self.segment_masks[color_idx] = mask

    def display_mask(self):
        segmentation_mask = combine_masks(self.working_image, self.segment_masks)
        rgb_mask = segment_mask_2_rgb_image(self.working_image, segmentation_mask)

        self.image_tk_2 = ImageTk.PhotoImage(Image.fromarray(rgb_mask))
        self.canvas2.create_image(0, 0, anchor="nw", image=self.image_tk_2)

    def reset_masks(self):
        self.distance_masks = []
        self.segment_masks = []