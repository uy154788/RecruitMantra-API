from flask import Flask
from skill_extractor import skill_extractor_bp
from emotion_video import emotion_video_bp
from audio_emotion import audio_emotion_bp
from video_text_similarity import video_text_similarity_bp

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(skill_extractor_bp, url_prefix='/skills')
app.register_blueprint(emotion_video_bp, url_prefix='/video_emotion')
app.register_blueprint(audio_emotion_bp, url_prefix='/audio_emotion')
app.register_blueprint(video_text_similarity_bp, url_prefix='/video_text')

if __name__ == '__main__':
    app.run(debug=False)
