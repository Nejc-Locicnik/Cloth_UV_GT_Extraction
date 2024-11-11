import tkinter as tk

class CanvasController:
    def __init__(self, canvas, status_label):
        self.canvas = canvas  # The canvas widget
        self.status_label = status_label  # The status bar label

        # Bind mouse motion event to the canvas
        self.canvas.bind("<Motion>", self.update_mouse_coordinates)

    def update_mouse_coordinates(self, event):
        """Updates the status bar with the mouse coordinates on the canvas."""
        # Get the mouse position relative to the canvas
        x, y = event.x, event.y

        # Check if the mouse is inside the canvas
        if 0 <= x <= self.canvas.winfo_width() and 0 <= y <= self.canvas.winfo_height():
            self.status_label.config(text=f"Mouse Coordinates: ({x}, {y})")
        else:
            self.status_label.config(text="Mouse is outside the canvas")