import tkinter as tk
from tkinter import Text, Toplevel, Label, Button, Entry, messagebox, OptionMenu, StringVar
from PIL import Image, ImageTk, ImageGrab
import speech_recognition as sr
import os
import math
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class ScreenCaptureApp:
    CAPTURES_DIR = "captures"
    SCREENSHOT_WINDOW_WIDTH = 1500
    SCREENSHOT_WINDOW_HEIGHT = 900
    IMAGE_CANVAS_WIDTH = 1300
    IMAGE_CANVAS_HEIGHT = 700
    BUTTONS_AREA_WIDTH = 300
    DEFAULT_AI_PROMPT = "You are a presentation assistant that enhances text for slides used in recorded tutorial videos, ensuring the text is clear, professional, concise, and free from casual language such as 'thank you' or 'please', while maintaining a positive tone."
    PROMPT_FILENAME = "ai_prompt.txt"

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

        self.ai_client = OpenAI()
        self.current_ai_prompt = self.DEFAULT_AI_PROMPT
        self.project_dir = None
        self.pre_ai_text = None
        self.ai_undo_button = None

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

        self.selected_project.set(project_name)

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
        if (project_name == "Select Existing Project"):
            messagebox.showerror("Error", "Please select an existing project.")
            return

        self.project_dir = os.path.join(self.CAPTURES_DIR, project_name)
        self.load_prompt()
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

        scrollbar_x = tk.Scrollbar(image_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        image_canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # Display the screenshot
        self.img = Image.open(self.screenshot_filename)
        # Store original image size before converting to PhotoImage
        img_width = self.img.width
        img_height = self.img.height
        self.img = ImageTk.PhotoImage(self.img)
        self.img_label = Label(image_canvas, image=self.img)
        
        # Calculate center coordinates based on both canvas and image dimensions
        x = max(math.floor(self.IMAGE_CANVAS_WIDTH / 2), math.floor(img_width / 2))
        y = max(math.floor(self.IMAGE_CANVAS_HEIGHT / 2), math.floor(img_height / 2))
        
        image_canvas.create_window(x, y, anchor='center', window=self.img_label)
        image_canvas.config(scrollregion=(0, 0, img_width, img_height))

        # Frame for text area and buttons
        frame = tk.Frame(self.note_window)
        frame.pack(fill=tk.BOTH, expand=True)

        # Text area for notes with scrollbars
        text_frame = tk.Frame(frame)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Button frame with minimum width
        button_frame = tk.Frame(frame, width=self.BUTTONS_AREA_WIDTH)  # Set minimum width
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=5)
        button_frame.pack_propagate(False)  # Prevent frame from shrinking

        scrollbar_y = tk.Scrollbar(text_frame, orient=tk.VERTICAL)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = tk.Scrollbar(text_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.text_area = Text(text_frame, height=10, wrap=tk.WORD, yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar_y.config(command=self.text_area.yview)
        scrollbar_x.config(command=self.text_area.xview)

        # Frame for microphone and AI enhance buttons
        mic_ai_frame = tk.Frame(button_frame)
        mic_ai_frame.pack(anchor=tk.N, pady=10)

        # Load microphone icon
        mic_icon = Image.open("microphone.png")
        mic_icon = mic_icon.resize((20, 20), Image.LANCZOS)
        mic_photo = ImageTk.PhotoImage(mic_icon)

        # Microphone button with icon
        mic_button = Button(mic_ai_frame, image=mic_photo, command=self.record_audio, bg="lightblue", fg="black")
        mic_button.image = mic_photo  # Keep a reference to avoid garbage collection
        mic_button.pack(side=tk.LEFT, padx=5)

        # Load AI icon
        ai_icon = Image.open("artificial-intelligence.png")
        ai_icon = ai_icon.resize((20, 20), Image.LANCZOS)
        ai_photo = ImageTk.PhotoImage(ai_icon)

        # AI Enhance button with icon
        ai_enhance_button = Button(mic_ai_frame, image=ai_photo, text=" AI Enhance", compound=tk.LEFT, command=self.ai_enhance, bg="lightblue", fg="black")
        ai_enhance_button.image = ai_photo  # Keep a reference to avoid garbage collection
        ai_enhance_button.pack(side=tk.LEFT, padx=5)

        # AI Undo button (initially hidden)
        self.ai_undo_button = Button(mic_ai_frame, 
                                   text="↩ Undo AI", 
                                   command=self.undo_ai_enhance,
                                   bg="#dc3545", 
                                   fg="white")

        # AI Settings button
        ai_settings_button = Button(mic_ai_frame, text="⚙️", command=self.show_ai_settings, bg="lightblue", fg="black")
        ai_settings_button.pack(side=tk.LEFT, padx=2)
              
        # Frame for retake and delete buttons
        retake_delete_frame = tk.Frame(button_frame)
        retake_delete_frame.pack(anchor=tk.N, pady=10)

        # Retake screenshot button
        retake_button = Button(retake_delete_frame, text="Retake Screenshot", command=self.retake_screenshot, bg="lightblue", fg="black")
        retake_button.pack(side=tk.LEFT, padx=5)

        # Delete button
        delete_button = Button(retake_delete_frame, text="Delete", command=self.delete_screenshot, bg="lightcoral", fg="black")
        delete_button.pack(side=tk.LEFT, padx=5)

        # Previous and Next buttons
        nav_button_frame = tk.Frame(button_frame)
        nav_button_frame.pack(anchor=tk.N, pady=10)

        prev_button = Button(nav_button_frame, text="Previous", command=self.show_previous_image, bg="lightgray", fg="black")
        prev_button.pack(side=tk.LEFT, padx=5)

        next_button = Button(nav_button_frame, text="Next", command=self.show_next_image, bg="lightgray", fg="black")
        next_button.pack(side=tk.LEFT, padx=5)

        # Frame for save buttons with top padding
        save_button_frame = tk.Frame(button_frame)
        save_button_frame.pack(anchor=tk.N, pady=10)

        # Save button
        save_button = Button(save_button_frame, text="Save", command=self.save_notes, bg="lightblue", fg="black")
        save_button.pack(side=tk.LEFT, padx=5)

        # Save and close button
        save_and_close_button = Button(save_button_frame, text="Save and Close", command=self.save_and_close, bg="lightblue", fg="black")
        save_and_close_button.pack(side=tk.LEFT, padx=5)

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
        self.hide_undo_button()
        while self.screenshot_counter > 1:
            self.screenshot_counter -= 1
            self.screenshot_filename = os.path.join(self.project_dir, f"capture{self.screenshot_counter}.png")
            if os.path.exists(self.screenshot_filename):
                self.update_screenshot_display()
                self.load_text()
                self.update_window_title()
                break

    def show_next_image(self):       
        self.hide_undo_button()
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

    def ai_enhance(self):
        try:
            # Store current text for undo
            self.pre_ai_text = self.text_area.get("1.0", tk.END).strip()
            
            # Perform AI enhancement
            enhanced_text = self.call_chatgpt_api(self.pre_ai_text)
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, enhanced_text)
            
            # Show undo button
            self.ai_undo_button.pack(side=tk.LEFT, padx=2)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to enhance text: {str(e)}")

    def undo_ai_enhance(self):
        if self.pre_ai_text is not None:
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, self.pre_ai_text)
            self.pre_ai_text = None
            self.ai_undo_button.pack_forget()

    def call_chatgpt_api(self, text):
        completion = self.ai_client.chat.completions.create(
            model= os.getenv("OPENAI_API_MODEL_ENHANCE"),
            messages=[
                {"role": "system", "content": self.current_ai_prompt},
                {"role": "user", "content": f"Please enhance this text:\n\n{text}"}
            ],
            # max_tokens=1000,
            # temperature=0.7
        )

        return completion.choices[0].message.content.strip()

    def show_ai_settings(self):
        settings_window = Toplevel(self.root)
        settings_window.title("AI Settings")
        settings_window.geometry("400x300")
        
        # Prompt label
        label = Label(settings_window, text="AI Enhancement Prompt:")
        label.pack(pady=5)
        
        # Prompt text area
        prompt_text = Text(settings_window, height=10, wrap=tk.WORD)
        prompt_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        prompt_text.insert("1.0", self.current_ai_prompt)
        
        # Buttons frame
        buttons_frame = tk.Frame(settings_window)
        buttons_frame.pack(pady=10)
        
        def save_prompt():
            new_prompt = prompt_text.get("1.0", tk.END).strip()
            self.save_prompt(new_prompt)
            settings_window.destroy()
            
        def restore_defaults():
            prompt_text.delete("1.0", tk.END)
            prompt_text.insert("1.0", self.DEFAULT_AI_PROMPT)
            
        # Save button
        save_button = Button(buttons_frame, text="Save", command=save_prompt)
        save_button.pack(side=tk.LEFT, padx=5)
        
        # Restore defaults button
        restore_button = Button(buttons_frame, text="Restore Defaults", command=restore_defaults)
        restore_button.pack(side=tk.LEFT, padx=5)
        
        # Cancel button
        cancel_button = Button(buttons_frame, text="Cancel", command=settings_window.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)

    def save_prompt(self, prompt_text):
        if self.project_dir:
            prompt_file = os.path.join(self.project_dir, self.PROMPT_FILENAME)
            with open(prompt_file, 'w') as f:
                f.write(prompt_text)
        self.current_ai_prompt = prompt_text
            
    def load_prompt(self):
        if self.project_dir:
            prompt_file = os.path.join(self.project_dir, self.PROMPT_FILENAME)
            if os.path.exists(prompt_file):
                with open(prompt_file, 'r') as f:
                    self.current_ai_prompt = f.read().strip()
            else:
                self.current_ai_prompt = self.DEFAULT_AI_PROMPT

    def hide_undo_button(self):
        if hasattr(self, 'ai_undo_button'):
            self.ai_undo_button.pack_forget()
        self.pre_ai_text = None

if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenCaptureApp(root)
    root.mainloop()