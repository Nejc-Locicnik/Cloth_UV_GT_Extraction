import os
from tkinter import filedialog

def select_directory():
    return filedialog.askdirectory(title="Select Image Directory")

def load_image_paths(directory:str):
    # Return a list of image paths in the specified directory
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(('.png', '.jpg', '.jpeg'))]

def validate_image_directory(directory:str):
    # Check if the directory exists and contains images
    return os.path.isdir(directory) and len(load_image_paths(directory)) > 0

def validate_directory(directory:str):
    # Check if the directory exists
    return os.path.isdir(directory) > 0