from flask import Flask, request, render_template, send_file
import os
from dotenv import load_dotenv
from openai import OpenAI
from ppt_to_video import convert_ppt_to_video


load_dotenv()

app = Flask(__name__)
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def configure_ffmpeg_local(ffmpeg_path: str):
    """
    ffmpeg_path should be the full path to the ffmpeg binary,
    e.g. "/absolute/path/to/my_project/bin/ffmpeg" or
    "C:/path/to/my_project/bin/ffmpeg.exe".
    """
    # Make sure the directory containing ffmpeg is on PATH
    print("Adding ffmpeg to path")
    ffmpeg_dir = os.path.dirname(os.path.abspath(ffmpeg_path))
    print(f"ffmpeg_dir: {ffmpeg_dir}")
    # print(f"PATH env to add:", ffmpeg_dir + os.pathsep + os.environ["PATH"])
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    output_dir = 'output'

    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file and file.filename.endswith('.pptx'):
        # language = request.form['language']
        language = "en"
        provider = request.form['tts_provider']
        accent = request.form['accent']
        openai_voice = request.form['voice']
        min_time_per_slide = int(request.form['min_time_per_slide'])
        pause_time_at_end = int(request.form['pause_time_at_end'])
        speed_factor = float(request.form['speed_factor'])
        fps = int(request.form['fps'])

        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
        output_video = 'output_video.mp4'

        extra_settings = {
            "min_time_per_slide": min_time_per_slide,
            "pause_time_at_end": pause_time_at_end,
            "speed_factor": speed_factor,
            "fps": fps
        }

        convert_ppt_to_video(
            openai_client=openai_client,
            ppt_path=file_path,
            output_dir=output_dir,
            output_video=output_video,
            provider=provider,
            language=language,
            accent=accent,
            openai_voice=openai_voice,
            extra_settings=extra_settings
        )
        full_path = os.path.join(os.getcwd(), output_dir, output_video)
        return send_file(full_path, as_attachment=True)
    return 'Invalid file type'
        
if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.mkdir('uploads')

    ffmpeg_root_path = "ffmpeg"
    if not os.path.exists(ffmpeg_root_path):
        ffmpeg_root_path = "_internal/" + ffmpeg_root_path

    configure_ffmpeg_local(f"{ffmpeg_root_path}/bin/ffmpeg.exe") # add ffmpeg to our path. We need it to speed up audio files
    app.run(debug=True)