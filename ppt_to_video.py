import os
import sys
from pptx import Presentation
from gtts import gTTS
from moviepy.editor import *
import comtypes.client


output_dir = "output"
def convert_ppt_to_video(ppt_path, output_video="output_2.mp4"):
    # Create temp directories
    if not os.path.exists("temp_images"):
        os.mkdir("temp_images")
    if not os.path.exists("temp_audio"):
        os.mkdir("temp_audio")
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # Convert PPT slides to images using COM interface (Windows only)
    powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
    powerpoint.Visible = 1
    ppt = powerpoint.Presentations.Open(os.path.abspath(ppt_path))

    # Export slides as images
    ppt.SaveAs(os.path.abspath("temp_images/slides"), 17)  # 17 corresponds to PNG format
    ppt.Close()
    powerpoint.Quit()

    # Load presentation to get slide notes
    prs = Presentation(ppt_path)
    clips = []

    for idx, slide in enumerate(prs.slides):
        # Get slide notes
        notes = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
        slide_image_path = f"temp_images/slides/slide{idx+1}.JPG"

        # Convert notes to speech
        if notes.strip():
            audio_path = f"temp_audio/audio_{idx+1}.mp3"
            tts = gTTS(text=notes, lang='en')
            tts.save(audio_path)
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
        else:
            audio_clip = None
            duration = 5  # Default duration if no notes

        # Create video clip
        image_clip = ImageClip(slide_image_path).set_duration(duration)
        if audio_clip:
            image_clip = image_clip.set_audio(audio_clip)
        clips.append(image_clip)

    # Concatenate all clips and write the final video
    if clips:
        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(output_dir + "/" + output_video, fps=24)

    # Clean up temp directories
    for file in os.listdir("temp_images"):
        os.remove(os.path.join("temp_images", file))
    for file in os.listdir("temp_audio"):
        os.remove(os.path.join("temp_audio", file))
    os.rmdir("temp_images")
    os.rmdir("temp_audio")

if __name__ == "__main__":
    # if len(sys.argv) > 1:
    #     ppt_path = sys.argv[1]
    #     convert_ppt_to_video(ppt_path)
    # else:
    #     print("Usage: python ppt_to_video.py <path_to_ppt_file>")

    convert_ppt_to_video("testppt_video.pptx")