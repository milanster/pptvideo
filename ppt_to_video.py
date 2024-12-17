import os
import sys
import re
from pptx import Presentation
from gtts import gTTS
from moviepy.editor import *
import comtypes.client
import comtypes

# Define the folder paths at the top
TEMP_IMAGES_FOLDER = 'temp_images'
TEMP_AUDIO_FOLDER = 'temp_audio'

def create_temp_folders():
    if not os.path.exists(TEMP_IMAGES_FOLDER):
        os.makedirs(TEMP_IMAGES_FOLDER)
    if not os.path.exists(TEMP_AUDIO_FOLDER):
        os.makedirs(TEMP_AUDIO_FOLDER)

def clean_temp_folders():
    for folder in [TEMP_IMAGES_FOLDER, TEMP_AUDIO_FOLDER]:
        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)

def cleanup_temp_dirs():
    """Clean up temporary directories with error handling"""
    for directory in [TEMP_IMAGES_FOLDER, TEMP_AUDIO_FOLDER]:
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

def get_min_time_from_notes(notes):
    """
    Searches the given notes for a string like {{min_time:5}} and
    returns the minimum time (in seconds) if found. If not found, returns
    None for the minimum time and the original notes for the second
    argument. If found, the second argument will be the original notes
    with the {{min_time:5}} string removed.
    """
    match = re.search(r'\{\{min_time:(\d+)\}\}', notes)
    if match:
        min_time = int(match.group(1))
        cleaned_notes = re.sub(r'\{\{min_time:\d+\}\}', '', notes)
        return min_time, cleaned_notes
    return None, notes

def remove_comments(notes=None):
    return re.sub(r'\{\*.*?\*\}', '', notes, flags=re.DOTALL) if notes is not None else None # DOTAALL flag is used to match multilines

def convert_ppt_to_video(openai_client, ppt_path, output_dir="output", output_video="output.mp4", provider="google", language='en', accent='com', openai_voice='alloy', min_time_per_slide=6, pause_time_at_end=1):
    try:
        clips = []
        # Create temp directories
        create_temp_folders()
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        print("File path: ", ppt_path)
        if provider == "openai":
            print("Using OpenAI with voice:", openai_voice)
        else:
            print("Using Google")

        # Initialize COM library
        comtypes.CoInitialize()
        # Convert PPT slides to images using COM interface (Windows only)
        powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
        powerpoint.Visible = 1
        ppt = powerpoint.Presentations.Open(os.path.abspath(ppt_path))

        # Export slides as images
        ppt.SaveAs(os.path.abspath(TEMP_IMAGES_FOLDER), 17)  # 17 corresponds to PNG format
        ppt.Close()
        powerpoint.Quit()

        # Load presentation to get slide notes
        prs = Presentation(ppt_path)

        for idx, slide in enumerate(prs.slides):
            # Get slide notes
            notes = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
            slide_image_path = f"{TEMP_IMAGES_FOLDER}/slide{idx+1}.JPG"
            duration = min_time_per_slide if min_time_per_slide is not None else 1

            # get min time from slide if specified, also return cleaned notes {{min_time:X}} if specified
            min_time_from_notes, notes = get_min_time_from_notes(remove_comments(notes)) 

            # Convert notes to speech
            if notes is not None and notes.strip():
                audio_path = f"{TEMP_AUDIO_FOLDER}/audio_{idx+1}.mp3"

                if provider == "openai":
                    # Generate speech using OpenAI
                    response = openai_client.audio.speech.create(
                        model="tts-1",  # or "tts-1-hd" for higher quality
                        voice=openai_voice,  # options: alloy, echo, fable, onyx, nova, shimmer
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
                duration = 1  # Default duration if no notes

            # Ensure minimum time per slide
            if min_time_from_notes is not None:
                duration = max(duration, min_time_from_notes)
            elif min_time_per_slide > 0:
                duration = max(duration, min_time_per_slide)

            # Add pause at end if needed
            if pause_time_at_end > 0:
                duration += pause_time_at_end

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