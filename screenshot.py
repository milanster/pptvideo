import tkinter as tk
from PIL import ImageGrab

class ScreenCaptureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Screenshot Tool")
        self.root.geometry("200x100")
        self.root.attributes("-topmost", True)
        
        self.button = tk.Button(root, text="Take Screenshot", command=self.start_screenshot)
        self.button.pack(expand=True)

    def start_screenshot(self):
        self.root.withdraw()  # Hide the floating window
        self.screenshot_window = tk.Toplevel(self.root)
        self.screenshot_window.attributes("-fullscreen", True)
        self.screenshot_window.attributes("-alpha", 0.3)  # Make the window semi-transparent
        self.canvas = tk.Canvas(self.screenshot_window, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline="red", width=2)

    def on_mouse_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_button_release(self, event):
        # Make the window fully opaque before taking the screenshot
        self.screenshot_window.attributes("-alpha", 0)

        x1 = self.canvas.winfo_rootx() + self.start_x
        y1 = self.canvas.winfo_rooty() + self.start_y
        x2 = self.canvas.winfo_rootx() + event.x
        y2 = self.canvas.winfo_rooty() + event.y

        # Take the screenshot
        bbox = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        screenshot = ImageGrab.grab(bbox)
        
        # Save the screenshot
        filename = "screenshot_selected_area.png"
        screenshot.save(filename)
        print(f"Screenshot saved as {filename}")

        # Revert the window back to semi-transparent
        self.screenshot_window.attributes("-alpha", 0.3)

        self.screenshot_window.destroy()
        self.root.deiconify()  # Show the floating window again

if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenCaptureApp(root)
    root.mainloop()