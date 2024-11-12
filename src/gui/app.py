import tkinter as tk
from tkinter import Menu
from ..utils.file_utils import *
from .canvas import CanvasManager
import json

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Annotation GUI")
        self.settings = self.load_settings('src/config/settings.json')

        self.canvases = CanvasManager(self, self.settings)
        self.images = None
        self.current_img_index = None
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
        edit_menu.add_command(label="Undo")
        edit_menu.add_command(label="Redo")
        menubar.add_cascade(label="Edit", menu=edit_menu)

    def _init_statusbar(self):
        # Status Bar
        self.status = tk.Label(self, text="Status: Ready", bd=1, relief=tk.SUNKEN, anchor="w")
        self.status.grid(row=2, column=0, columnspan=2, sticky="we", padx=2, pady=2)

    def _init_toolbar(self):
        # Tool bar
        self.toolbar = tk.Frame(self, width=50, height=self.settings.get("size"), bg="#eeeeee")
        self.toolbar.grid(row=1, column=2, sticky="nsew")
        # TODO buttons, chosen colors visualization etc
    
    def _init_events(self):
        self.canvases.canvas1.bind("<Motion>", self.update_mouse_coordinates)
        self.canvases.canvas2.bind("<Motion>", self.update_mouse_coordinates)
        self.canvases.canvas1.bind("<Button-1>", self.on_left_click)
        self.bind('<Left>', self.previous_image)  # Left arrow key for previous image
        self.bind('<Right>', self.next_image)    # Right arrow key for next image

    def set_image_directory(self):
        path = select_directory()
        if path:
            if validate_image_directory(path):
                self.image_dir_path = path
                self._init_images()
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
            self.status.config(text=f"Image Coordinates: ({x}, {y})")
        elif 0 <= x <= self.canvases.canvas2.winfo_width() and 0 <= y <= self.canvases.canvas2.winfo_height():
            self.status.config(text=f"Image Coordinates: ({x}, {y})") 
        else:
            self.status.config(text="Mouse is outside the canvas")

    def on_left_click(self, event):
        """Handle left-click event on the canvas."""
        x, y = event.x, event.y
        if self.canvases.working_image is not None:
            self.open_popup(self.canvases.working_image[y, x])
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

    def open_popup(self, color):
        """Open a popup window with specific text, number-only field, and an OK button."""
        
        # Create the popup window
        popup = tk.Toplevel(self)
        popup.title("Specify color threshold")
        
        # Display instructions text
        label = tk.Label(popup, text="Please enter an integer:")
        label.pack(pady=10)

        # Validation function to allow only numeric input
        def validate_numeric_input(char):
            return char.isdigit()

        # Register the validation function
        validate_command = popup.register(validate_numeric_input)
        
        # Entry field for numbers only
        entry = tk.Entry(popup, validate="key", validatecommand=(validate_command, '%S'))
        entry.pack(pady=5)

        # OK button to confirm and close the popup
        ok_button = tk.Button(popup, text="OK", command=lambda: self.close_popup(popup, entry.get(), color))
        ok_button.pack(pady=10)

    def close_popup(self, popup, value, color):
        """Handle closing the popup and processing the entered value."""
        if value.isdigit():
            popup.destroy()  # Close the popup window
            index = len(self.gt_colors)
            threshold = int(value)
            self.gt_colors.append((index, color, threshold)) # (idx, color, threshold)
            print(self.gt_colors[-1])
            self.canvases.add_mask(color, threshold)
            self.canvases.display_mask()
        else:
            tk.messagebox.showwarning("Invalid input", "Please enter a valid number.")

if __name__ == "__main__":
    app = App()
    app.mainloop()
