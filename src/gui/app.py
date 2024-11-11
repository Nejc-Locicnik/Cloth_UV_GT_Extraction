import tkinter as tk
from tkinter import Menu
from PIL import Image, ImageTk
from ..utils.image_utils import *
from ..utils.file_utils import *
from .control import CanvasController

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Annotation GUI")
        self.geometry("1030x542")  # Adjusted height to fit status bar

        # Configure grid layout
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # Add Menu Bar
        menubar = Menu(self)
        self.config(menu=menubar)

        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Set image directory", command=self.set_image_directory)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Undo")
        edit_menu.add_command(label="Redo")
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # Add two canvases side by side
        self.canvas1 = tk.Canvas(self, bg="white", width=512, height=512)
        self.canvas1.grid(row=1, column=0, sticky="nsew")

        self.canvas2 = tk.Canvas(self, bg="white", width=512, height=512)
        self.canvas2.grid(row=1, column=1, sticky="nsew")

        # Status Bar
        self.status = tk.Label(self, text="Status: Ready", bd=1, relief=tk.SUNKEN, anchor="w")
        self.status.grid(row=2, column=0, columnspan=2, sticky="we", padx=2, pady=2)

        self.controller = CanvasController(self.canvas1, self.status)

    def set_image_directory(self):
        self.dir_path = select_directory()
        if validate_directory(self.dir_path):
            self.images = load_image_paths(self.dir_path)
            img = self.open_image(self.images[0])
            self.display_image(img, self.canvas1)
            # TODO mask
        else:
            raise FileExistsError("There were no images found in the selected directory.")
        
    def open_image(self, img_path):
        c_space = "BGR2LAB"
        size = (512, )*2
        x_cut = (525, 1400)
        y_cut = (35, 910)

        return resize_image(cutout(change_color_space(read_image(img_path), c_space), x_cut, y_cut), size)

    def display_image(self, image, canvas):
        self.image_tk = ImageTk.PhotoImage(Image.fromarray(change_color_space(image, "LAB2RGB")))
        canvas.create_image(0, 0, anchor="nw", image=self.image_tk)

if __name__ == "__main__":
    app = App()
    app.mainloop()
