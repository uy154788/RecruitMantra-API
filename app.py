from flask import Flask
from flask_cors import CORS

# Import Blueprints
from skill_extractor import skill_extractor_bp
from emotion_video import emotion_video_bp
from audio_emotion import audio_emotion_bp
from video_text_similarity import video_text_similarity_bp

from hr_question import hr_question_bp
from hr_result import hr_result_bp

from manage_question import manage_question_bp
from manage_result import manage_result_bp

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(skill_extractor_bp, url_prefix='/skills')
app.register_blueprint(emotion_video_bp, url_prefix='/video_emotion')
app.register_blueprint(audio_emotion_bp, url_prefix='/audio_emotion')
app.register_blueprint(video_text_similarity_bp, url_prefix='/video_text')

app.register_blueprint(hr_question_bp, url_prefix='/hr')
app.register_blueprint(hr_result_bp, url_prefix='/hr')

app.register_blueprint(manage_question_bp, url_prefix='/manage')
app.register_blueprint(manage_result_bp, url_prefix='/manage')

if __name__ == '__main__':
    app.run(debug=False)
