import os
import sys
from pptx import Presentation
from gtts import gTTS
from moviepy.editor import *
import comtypes.client
import comtypes
from dotenv import load_dotenv
from openai import OpenAI

openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def cleanup_temp_dirs():
    """Clean up temporary directories with error handling"""
    for directory in ["temp_images", "temp_audio"]:
        if os.path.exists(directory):
            try:
                for file in os.listdir(directory):
                    try:
                        file_path = os.path.join(directory, file)
                        if os.path.isfile(file_path):
                            os.chmod(file_path, 0o777)  # Give full permissions
                            os.remove(file_path)
                    except Exception as e:
                        print(f"Warning: Could not remove file {file}: {e}")
                os.rmdir(directory)
            except Exception as e:
                print(f"Warning: Could not remove directory {directory}: {e}")

def convert_ppt_to_video(ppt_path, output_dir="output", output_video="output.mp4", provider="google", language='en', accent='com'):
    try:
        clips = []
        # Create temp directories
        if not os.path.exists("temp_images"):
            os.mkdir("temp_images")
        if not os.path.exists("temp_audio"):
            os.mkdir("temp_audio")
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        print("File path: ", ppt_path)
        if provider == "openai":
            print("Using OpenAI")
        else:
            print("Using Google")

        # Initialize COM library
        comtypes.CoInitialize()
        # Convert PPT slides to images using COM interface (Windows only)
        powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
        powerpoint.Visible = 1
        ppt = powerpoint.Presentations.Open(os.path.abspath(ppt_path))

        # Export slides as images
        ppt.SaveAs(os.path.abspath("temp_images"), 17)  # 17 corresponds to PNG format
        ppt.Close()
        powerpoint.Quit()

        # Load presentation to get slide notes
        prs = Presentation(ppt_path)

        for idx, slide in enumerate(prs.slides):
            # Get slide notes
            notes = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
            slide_image_path = f"temp_images/slide{idx+1}.JPG"

            # Convert notes to speech
            if notes.strip():
                audio_path = f"temp_audio/audio_{idx+1}.mp3"

                if provider == "openai":
                    # Generate speech using OpenAI
                    response = openai_client.audio.speech.create(
                        model="tts-1",  # or "tts-1-hd" for higher quality
                        voice="alloy",  # options: alloy, echo, fable, onyx, nova, shimmer
                        input=notes
                    )
                    
                    # Save the audio file
                    response.stream_to_file(audio_path)
                else: # default / google
                    tts = gTTS(text=notes, lang=language, tld=accent)
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
            final_clip.close()  # Explicitly close the clip
    finally:
        # Clean up resources
        for clip in clips:
            clip.close()
        cleanup_temp_dirs()

if __name__ == "__main__":
    # if len(sys.argv) > 1:
    #     ppt_path = sys.argv[1]
    #     convert_ppt_to_video(ppt_path)
    # else:
    #     print("Usage: python ppt_to_video.py <path_to_ppt_file>")

    convert_ppt_to_video("testppt_video.pptx")