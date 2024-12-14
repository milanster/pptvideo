import tkinter as tk
from tkinter import Text, Toplevel, Label, Button, Entry, messagebox, OptionMenu, StringVar
from PIL import Image, ImageTk, ImageGrab
import speech_recognition as sr
import os
import math

class ScreenCaptureApp:
    CAPTURES_DIR = "captures"
    SCREENSHOT_WINDOW_WIDTH = 1300
    SCREENSHOT_WINDOW_HEIGHT = 900
    IMAGE_CANVAS_WIDTH = 1300
    IMAGE_CANVAS_HEIGHT = 700
    

    def __init__(self, root):
        self.root = root
        self.root.title("Nakisa Screen Capture")
        self.root.geometry("400x200")
        self.root.attributes("-topmost", True)
        
        # Set the application icon
        self.root.iconbitmap('favicon.ico')

        self.label = tk.Label(root, text="Project Name:")
        self.label.pack(pady=5)

        self.project_name_frame = tk.Frame(root)
        self.project_name_frame.pack(pady=5)

        self.project_name_entry = tk.Entry(self.project_name_frame)
        self.project_name_entry.pack(side=tk.LEFT, padx=5)

        self.create_project_button = tk.Button(self.project_name_frame, text="Create Project", command=self.create_project)
        self.create_project_button.pack(side=tk.LEFT, padx=5)

        self.existing_projects = self.get_existing_projects()
        self.selected_project = StringVar(root)
        self.selected_project.set("Select Existing Project")
        self.project_dropdown = OptionMenu(root, self.selected_project, *self.existing_projects, command=self.project_selected)
        self.project_dropdown.pack(pady=5)

        self.project_label = tk.Label(root, text="")
        self.project_label.pack(pady=5)
        self.project_label.pack_forget()  # Hide the label initially

        self.browse_button = tk.Button(root, text="Browse Project", command=self.browse_project)
        self.browse_button.pack(pady=5)
        self.browse_button.pack_forget()  # Hide the button initially

        self.button = tk.Button(root, text="Take Screenshot", command=self.start_screenshot)
        self.button.pack(pady=5)
        self.button.pack_forget()  # Hide the button initially

        # Initialize screenshot counter
        self.screenshot_counter = 0

    def get_existing_projects(self):
        if not os.path.exists(self.CAPTURES_DIR):
            os.makedirs(self.CAPTURES_DIR)
        return [d for d in os.listdir(self.CAPTURES_DIR) if os.path.isdir(os.path.join(self.CAPTURES_DIR, d))]

    def create_project(self):
        project_name = self.project_name_entry.get().strip()
        if not project_name:
            messagebox.showerror("Error", "Please enter a project name.")
            return

        self.project_dir = os.path.join(self.CAPTURES_DIR, project_name)
        if not os.path.exists(self.project_dir):
            os.makedirs(self.project_dir)
            messagebox.showinfo("Success", f"Project '{project_name}' created successfully.")
            self.existing_projects.append(project_name)
            self.project_dropdown['menu'].add_command(label=project_name, command=tk._setit(self.selected_project, project_name, self.project_selected))
        else:
            messagebox.showerror("Error", "Project already exists.")

        self.show_buttons(project_name)

    def project_selected(self, value):
        self.project_dir = os.path.join(self.CAPTURES_DIR, value)
        self.show_buttons(value)

    def show_buttons(self, project_name):
        self.project_name_frame.pack_forget()
        self.project_dropdown.pack_forget()
        self.label.pack_forget()
        self.project_label.config(text=f"Project: {project_name}")
        self.project_label.pack(pady=15, padx=15)
        self.browse_button.pack(pady=5, padx=5)
        self.button.pack(pady=15, padx=15)
        self.root.geometry("300x200")  # Set a specific width and height for the window

    def browse_project(self):
        project_name = self.selected_project.get()
        if project_name == "Select Existing Project":
            messagebox.showerror("Error", "Please select an existing project.")
            return

        self.project_dir = os.path.join(self.CAPTURES_DIR, project_name)
        # self.screenshot_counter = len([f for f in os.listdir(self.project_dir) if f.startswith("capture") and f.endswith(".png")])
        self.screenshot_counter = self.get_highest_image_number()
        if self.screenshot_counter == 0:
            messagebox.showerror("Error", "No screenshots found in the selected project.")
            return

        self.screenshot_filename = os.path.join(self.project_dir, f"capture{self.screenshot_counter}.png")
        self.open_screenshot_window()

    def start_screenshot(self):
        project_name = self.project_name_entry.get().strip()
        if not project_name:
            project_name = self.selected_project.get()
            if project_name == "Select Existing Project":
                messagebox.showerror("Error", "Please enter a project name or select an existing project.")
                return

        self.project_dir = os.path.join(self.CAPTURES_DIR, project_name)
        if not os.path.exists(self.project_dir):
            os.makedirs(self.project_dir)

        # Update screenshot counter based on existing screenshots
        # self.screenshot_counter = len([f for f in os.listdir(self.project_dir) if f.startswith("capture") and f.endswith(".png")]) + 1
        self.screenshot_counter = self.get_highest_image_number() + 1

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
        # Make the window fully visible before taking the screenshot
        self.screenshot_window.attributes("-alpha", 0.0)

        x1 = self.canvas.winfo_rootx() + self.start_x
        y1 = self.canvas.winfo_rooty() + self.start_y
        x2 = self.canvas.winfo_rootx() + event.x
        y2 = self.canvas.winfo_rooty() + event.y

        if x1 == x2 or y1 == y2:
            messagebox.showerror("Error", "Please select a region for the screenshot.")
            self.screenshot_window.attributes("-alpha", 0.3)
            return

        # Take the screenshot
        bbox = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        screenshot = ImageGrab.grab(bbox)
        
        # Save the screenshot
        try:
            self.screenshot_filename = os.path.join(self.project_dir, f"capture{self.screenshot_counter}.png")
            screenshot.save(self.screenshot_filename)
            print(f"Screenshot saved as {self.screenshot_filename}")

            # Save an empty text file
            notes_filename = os.path.join(self.project_dir, f"capture{self.screenshot_counter}.txt")
            with open(notes_filename, "w") as file:
                file.write("")
            print(f"Empty notes file saved as {notes_filename}")

            # Revert the window back to semi-transparent
            self.screenshot_window.attributes("-alpha", 0.3)

            self.screenshot_window.destroy()
            
            # Open the screenshot in a new window with a text area
            self.open_screenshot_window()
        except Exception as e:
            print(f"Error saving screenshot: {e}")
            messagebox.showerror("Error", "Error saving screenshot. Please try again.")
            self.screenshot_window.destroy()

            self.root.deiconify()  # Show the floating window again

    def open_screenshot_window(self):
        image_name = os.path.basename(self.screenshot_filename)
        self.note_window = Toplevel(self.root)
        self.note_window.title(f"{image_name}")
        # self.note_window.geometry("1300x900")  # Set the window size to 1200x800 pixels
        self.note_window.geometry(f"{self.SCREENSHOT_WINDOW_WIDTH}x{self.SCREENSHOT_WINDOW_HEIGHT}")

        # Hide the main window
        self.root.withdraw()

        # Frame for image
        image_frame = tk.Frame(self.note_window, height=self.IMAGE_CANVAS_HEIGHT)
        image_frame.pack(fill=tk.X)

        # Add scrollbars to the image frame
        image_canvas = tk.Canvas(image_frame, width=self.IMAGE_CANVAS_WIDTH, height=self.IMAGE_CANVAS_HEIGHT)
        image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar_y = tk.Scrollbar(image_frame, orient=tk.VERTICAL, command=image_canvas.yview)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = tk.Scrollbar(image_frame, orient=tk.HORIZONTAL, command=image_canvas.xview)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        image_canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # Display the screenshot
        self.img = Image.open(self.screenshot_filename)
        self.img = ImageTk.PhotoImage(self.img)
        self.img_label = Label(image_canvas, image=self.img)
        image_canvas.create_window(math.floor(self.IMAGE_CANVAS_WIDTH / 2), math.floor(self.IMAGE_CANVAS_HEIGHT / 2), anchor='center', window=self.img_label)  # Center the image
        image_canvas.config(scrollregion=image_canvas.bbox(tk.ALL))

        # Frame for text area and buttons
        frame = tk.Frame(self.note_window)
        frame.pack(fill=tk.BOTH, expand=True)

        # Text area for notes with scrollbars
        text_frame = tk.Frame(frame)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar_y = tk.Scrollbar(text_frame, orient=tk.VERTICAL)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = tk.Scrollbar(text_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.text_area = Text(text_frame, height=10, wrap=tk.NONE, yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar_y.config(command=self.text_area.yview)
        scrollbar_x.config(command=self.text_area.xview)

        # Button frame
        button_frame = tk.Frame(frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Microphone button
        mic_button = Button(button_frame, text="Speak", command=self.record_audio)
        mic_button.pack(anchor=tk.N)

        # Save button
        save_button = Button(button_frame, text="Save Notes", command=self.save_notes)
        save_button.pack(anchor=tk.N)

        # Retake screenshot button
        retake_button = Button(button_frame, text="Retake Screenshot", command=self.retake_screenshot)
        retake_button.pack(anchor=tk.N)

        # Save and close button
        save_and_close_button = Button(button_frame, text="Save and Close", command=self.save_and_close)
        save_and_close_button.pack(anchor=tk.N)

        # Delete button
        delete_button = Button(button_frame, text="Delete", command=self.delete_screenshot)
        delete_button.pack(anchor=tk.N)

        # Previous and Next buttons
        prev_button = Button(button_frame, text="Previous", command=self.show_previous_image)
        prev_button.pack(anchor=tk.N)

        next_button = Button(button_frame, text="Next", command=self.show_next_image)
        next_button.pack(anchor=tk.N)

        # Load the initial text
        self.load_text()

        # Protocol handler for closing the screenshot window
        self.note_window.protocol("WM_DELETE_WINDOW", self.on_screenshot_window_close)

    def delete_screenshot(self):
        os.remove(self.screenshot_filename)
        notes_filename = os.path.join(self.project_dir, f"capture{self.screenshot_counter}.txt")
        if os.path.exists(notes_filename):
            os.remove(notes_filename)
        self.show_previous_image_or_main_window()

    def on_screenshot_window_close(self):
        # self.show_previous_image_or_main_window()
        self.note_window.destroy()
        self.root.deiconify()  # Show the main window again

    def show_previous_image_or_main_window(self):
        self.note_window.destroy()
        if self.screenshot_counter > 1:
            self.screenshot_counter -= 1
            self.screenshot_filename = os.path.join(self.project_dir, f"capture{self.screenshot_counter}.png")
            if os.path.exists(self.screenshot_filename):
                self.open_screenshot_window()
            else:
                self.root.deiconify()  # Show the main window again
        else:
            self.root.deiconify()  # Show the main window again

    def save_and_close(self):
        self.save_notes()
        self.on_screenshot_window_close()

    def update_screenshot_display(self):
        self.img = Image.open(self.screenshot_filename)
        self.img = ImageTk.PhotoImage(self.img)
        self.img_label.config(image=self.img)
        self.img_label.image = self.img  # Keep a reference to avoid garbage collection

    def update_window_title(self):
        image_name = os.path.basename(self.screenshot_filename)
        self.note_window.title(f"{image_name}")

    def record_audio(self):
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                print("Listening...")
                audio = recognizer.listen(source)

            try:
                text = recognizer.recognize_google(audio)
                self.text_area.insert(tk.END, text + "\n")
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")
        except OSError:
            messagebox.showerror("Error", "No Default Input Device Available")

    def save_notes(self):
        notes = self.text_area.get("1.0", tk.END)
        notes_filename = os.path.join(self.project_dir, f"capture{self.screenshot_counter}.txt")
        with open(notes_filename, "w") as file:
            file.write(notes)
        print(f"Notes saved as {notes_filename}")

        # Increment the screenshot counter for the next capture
        self.screenshot_counter += 1

    def retake_screenshot(self):
        # Preserve the current text
        self.notes_text = self.text_area.get("1.0", tk.END)

        # Hide the note window
        self.note_window.withdraw()

        # Start the screenshot process again
        self.root.withdraw()  # Hide the floating window
        self.screenshot_window = tk.Toplevel(self.root)
        self.screenshot_window.attributes("-fullscreen", True)
        self.screenshot_window.attributes("-alpha", 0.3)  # Make the window semi-transparent
        self.canvas = tk.Canvas(self.screenshot_window, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_retake_button_release)

    def on_retake_button_release(self, event):
        # Make the window fully visible before taking the screenshot
        self.screenshot_window.attributes("-alpha", 0.0)

        x1 = self.canvas.winfo_rootx() + self.start_x
        y1 = self.canvas.winfo_rooty() + self.start_y
        x2 = self.canvas.winfo_rootx() + event.x
        y2 = self.canvas.winfo_rooty() + event.y

        if x1 == x2 or y1 == y2:
            messagebox.showerror("Error", "Please select a region for the screenshot.")
            self.screenshot_window.attributes("-alpha", 0.3)
            return

        # Take the screenshot
        bbox = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        screenshot = ImageGrab.grab(bbox)
        
        # Save the screenshot (overwrite the previous one)
        try:
            # breakpoint()
            self.screenshot_filename = os.path.join(self.project_dir, f"capture{self.screenshot_counter}.png")
            screenshot.save(self.screenshot_filename)
            print(f"Screenshot saved as {self.screenshot_filename}")

            # Revert the window back to semi-transparent
            self.screenshot_window.attributes("-alpha", 0.3)

            self.screenshot_window.destroy()
            # self.root.deiconify()  # Show the floating window again

            # Show the note window again with preserved text
            self.note_window.deiconify()
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, self.notes_text)

            
        except Exception as e:
            print(f"Error saving screenshot: {e}")
            messagebox.showerror("Error", "Error saving screenshot. Please try again.")
            # self.screenshot_window.destroy()
            # self.root.deiconify()  # Show the floating window again

        # Update the screenshot display
        self.update_screenshot_display()

    def show_previous_image(self):
        while self.screenshot_counter > 1:
            self.screenshot_counter -= 1
            self.screenshot_filename = os.path.join(self.project_dir, f"capture{self.screenshot_counter}.png")
            if os.path.exists(self.screenshot_filename):
                self.update_screenshot_display()
                self.load_text()
                self.update_window_title()
                break

    def show_next_image(self):       
        highest_image_number = self.get_highest_image_number()
        # print(f"Highest image number: {highest_image_number}")
        
        next_counter = self.screenshot_counter + 1

        while True:
            # print(f"Next counter: {next_counter}")
            next_filename = os.path.join(self.project_dir, f"capture{next_counter}.png")
            if os.path.exists(next_filename):
                self.screenshot_counter = next_counter
                self.screenshot_filename = next_filename
                self.update_screenshot_display()
                self.load_text()
                self.update_window_title()
                break
            elif next_counter > highest_image_number:
                break
            else:
                next_counter += 1

    def get_highest_image_number(self):
        image_files = [f for f in os.listdir(self.project_dir) if f.startswith("capture") and f.endswith(".png")]
        if not image_files:
            return 0
        return max(int(f[7:-4]) for f in image_files)

    def load_text(self):
        notes_filename = os.path.join(self.project_dir, f"capture{self.screenshot_counter}.txt")
        if os.path.exists(notes_filename):
            with open(notes_filename, "r") as file:
                notes = file.read()
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, notes)
        else:
            self.text_area.delete("1.0", tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenCaptureApp(root)
    root.mainloop()