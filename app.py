from flask import Flask, request, render_template, send_file
import os
from ppt_to_video import convert_ppt_to_video

app = Flask(__name__)

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
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
        output_video = 'output_video.mp4'
        convert_ppt_to_video(ppt_path=file_path, output_dir=output_dir, output_video=output_video, provider=provider, language=language, accent=accent)
        return send_file(output_dir + "/" + output_video, as_attachment=True)
    return 'Invalid file type'

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.mkdir('uploads')
    app.run(debug=True)