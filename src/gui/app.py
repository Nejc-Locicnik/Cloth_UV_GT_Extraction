import tkinter as tk
from tkinter import ttk
from tkinter import Menu
from ..utils.file_utils import *
from .canvas import CanvasManager
import json
import gc


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Annotation GUI")
        self.settings = self.load_settings('src/config/settings.json')

        self.canvases = CanvasManager(self, self.settings)
        self.images = None
        self.current_img_index = None
        self.image_dir_path = None
        self.mask_dir_path = None
        self.gt_colors = []

        self._init_menubar()
        self._init_statusbar()
        self._init_toolbar()
        self._init_events()

    def _init_menubar(self):
        # Add Menu Bar
        menubar = Menu(self)
        self.config(menu=menubar)

        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Set image directory", command=self.set_image_directory)
        file_menu.add_command(label="Set masks directory", command=self.set_mask_directory)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Reset colors", command=self.reset_colors)
        menubar.add_cascade(label="Edit", menu=edit_menu)

    def _init_statusbar(self):
        # Status Bar
        self.status_left = tk.Label(self, text="Status: Ready", bd=1, relief=tk.FLAT, anchor="w")
        self.status_right = tk.Label(self, text="Coordinates...", bd=1, relief=tk.FLAT, anchor="e")
        self.status_left.grid(row=1, column=0, columnspan=2, sticky="we", padx=2, pady=2)
        self.status_right.grid(row=1, column=1, columnspan=2, sticky="ew", padx=2, pady=2)

    def _init_toolbar(self):
        # Tool bar
        self.toolbar = tk.Frame(self, width=150, height=self.settings.get("size"), bg="#eeeeee")
        self.toolbar.grid(row=0, column=2, sticky="nsew")

        #self.toolbar.grid_propagate(False)  
        #self.toolbar.rowconfigure([i for i in range(7)], weight=1)  # Evenly distribute row space
        #self.toolbar.columnconfigure([0, 1, 2], weight=1)

        # Button dimensions
        #button_size = self.settings["size"] // 7
        self.controls = []
        for i in range(7):
            row_frame = tk.Frame(self.toolbar)
            row_frame.grid(row=i+1, column=3, padx=2, pady=2, sticky="e")

            button = tk.Button(row_frame, bg="#eeeeee", width=6, relief=tk.RAISED)
            button.grid(row=0, column=0, padx=2, pady=5)

            slider = ttk.Scale(row_frame, from_=0, to=50, orient="horizontal",
                               command=lambda value, i=i: self.update_entry(value, i))
            slider.grid(row=0, column=1, padx=(0, 10))

            # Entry field for each row, linked to the slider
            entry = tk.Entry(row_frame, width=5)
            entry.grid(row=0, column=2)
            entry.insert(0, "0")  # Initialize with 0
            entry.bind("<Return>", lambda event, i=i: self.update_slider(i))
            entry.bind("<FocusOut>", lambda event, i=i: self.update_slider(i))

            self.controls.append((button, slider, entry))
    
    def _init_events(self):
        self.canvases.canvas1.bind("<Motion>", self.update_mouse_coordinates)
        self.canvases.canvas2.bind("<Motion>", self.update_mouse_coordinates)
        self.canvases.canvas1.bind("<Button-1>", self.on_left_click)
        self.bind('<Left>', self.previous_image)  # Left arrow key for previous image
        self.bind('<Right>', self.next_image)    # Right arrow key for next image
        self.bind('<Control-s>', self.save_mask)

    def set_image_directory(self):
        path = select_directory()
        if path:
            if validate_image_directory(path):
                self.image_dir_path = path
                self._init_images()
                self.status_left.config(text="Image directory set.")
            else:
                raise FileNotFoundError("There were no images found in the selected directory.")
    
    def _init_images(self):
        self.images = load_image_paths(self.image_dir_path)
        self.current_img_index = 0
        self.canvases.open_image(self.images[0])
        self.canvases.display_mask()

    def set_mask_directory(self):
        path = select_directory()
        if path:
            if validate_directory(path):
                self.mask_dir_path = path
                self.status_left.config(text="Mask directory set.")
            else:
                raise FileNotFoundError("Not a valid directory?")

    def load_settings(self, file_path):
        """Load settings from a JSON file."""
        if not os.path.exists(file_path):
            print(f"Settings file '{file_path}' not found. Using default settings.")
            return {}  # Return an empty dictionary if the file is missing

        with open(file_path, "r") as file:
            try:
                settings = json.load(file)
            except json.JSONDecodeError:
                print("Error: JSON file is invalid. Using default settings.")
                settings = {}

        return settings

    def update_mouse_coordinates(self, event):
        """Updates the status bar with the mouse coordinates on the canvas."""
        # Get the mouse position relative to the canvas
        x, y = event.x, event.y

        # Check if the mouse is inside the canvas
        if 0 <= x <= self.canvases.canvas1.winfo_width() and 0 <= y <= self.canvases.canvas1.winfo_height():
            self.status_right.config(text=f"Image Coordinates: ({x}, {y})")
        elif 0 <= x <= self.canvases.canvas2.winfo_width() and 0 <= y <= self.canvases.canvas2.winfo_height():
            self.status_right.config(text=f"Image Coordinates: ({x}, {y})") 
        else:
            self.status_right.config(text="Mouse is outside the canvas")

    def on_left_click(self, event):
        """Handle left-click event on the canvas."""
        x, y = event.x, event.y
        if self.canvases.working_image is not None:
            color = self.canvases.working_image[y, x]
            index = len(self.gt_colors)
            threshold = 10
            self.gt_colors.append((index, color, threshold)) # (idx, color, threshold)
            self.color_button(index, color, threshold)
            self.canvases.add_mask(color, threshold)
            self.canvases.display_mask()
            self.status_left.config(text=f"Added color {str(color)} with threshold: {threshold}")
        #print(f"Left-click at coordinates: ({x}, {y})")

    def previous_image(self, event):
        """Display the previous image in the directory."""
        if self.images is not None:
            self.current_img_index = (self.current_img_index - 1) % len(self.images)
            self.canvases.open_image(self.images[self.current_img_index])
            self.update_mask()

    def next_image(self, event):
        """Display the next image in the directory."""
        if self.images is not None:
            self.current_img_index = (self.current_img_index + 1) % len(self.images)
            self.canvases.open_image(self.images[self.current_img_index])
            self.update_mask()

    def update_mask(self):
        self.canvases.reset_masks()
        for idx, color, threshold in self.gt_colors:
            self.canvases.add_mask(color, threshold)
        self.canvases.display_mask()

    def save_mask(self, event):
        if self.mask_dir_path is not None:
            self.status_left.config(text="Saving mask...")
            if self.canvases.segmentation_mask is not None:
                filename = f"{grab_filename(self.images[self.current_img_index]).split("_")[0]}_mask.png"
                self.canvases.save_mask(path_to_file(self.mask_dir_path, filename))
            self.status_left.config(text="Mask saved.")
        else:
            self.status_left.config(text="Saving failed! Set mask directory first!")
    
    def lab2rgb2hex(self, lab):
        rgb = self.canvases.get_rgb_color(lab)
        return "#%02x%02x%02x" % (rgb[0], rgb[1], rgb[2])

    def color_button(self, idx, color, threshold):
        self.controls[idx][0].config(bg=self.lab2rgb2hex(color))
        self.update_entry(threshold, idx)
        self.update_slider(idx)

    def update_entry(self, value, row_index):
        """Update the entry field with the current slider value."""
        entry = self.controls[row_index][2]
        entry.delete(0, tk.END)
        entry.insert(0, f"{int(float(value))}")
        self.canvases.update_seg_mask(row_index, int(float(value)))

    def update_slider(self, row_index):
        """Update the slider based on the entry's value."""
        entry = self.controls[row_index][2]
        slider = self.controls[row_index][1]
        try:
            # Get value from entry and set slider position
            value = int(entry.get())
            if 0 <= value <= 100:  # Assuming slider range is 0 to 100
                slider.set(value)
                self.canvases.update_seg_mask(row_index, value)
            else:
                self.status_left.config(text="Value out of range. Must be between 0 and 100.")
        except ValueError:
            self.status_left.config(text="Invalid entry. Please enter a number.")

    def reset_colors(self):
        self.status_left.config(text="Color selection is reset.")
        self.gt_colors = []
        self._init_toolbar()
        self.update_mask()
        gc.collect()


if __name__ == "__main__":
    app = App()
    app.mainloop()
