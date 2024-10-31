from flask import Blueprint, request, jsonify
import io
import os
import requests
import numpy as np
import librosa
import joblib
from moviepy.editor import VideoFileClip
from sklearn.preprocessing import LabelEncoder
from pydub import AudioSegment
from collections import defaultdict

# Initialize the Blueprint
audio_emotion_bp = Blueprint('audio_emotion', __name__)

# Load the trained model and label encoder once at the start
model = joblib.load('emotion_detection_randomForest_model.pkl')
emotion_labels = ['neutral', 'calm', 'happy', 'sad', 'angry', 'fearful', 'disgust', 'surprised']
label_encoder = LabelEncoder()
label_encoder.fit(emotion_labels)


# Convert video to WAV audio
def video_to_wav(video_file, output_wav):
    video = VideoFileClip(video_file)
    video.audio.write_audiofile(output_wav, codec='pcm_s16le')  # Specify codec for compatibility


# Split audio file into 5-second chunks
def split_audio(audio_file, chunk_duration=5):
    audio = AudioSegment.from_wav(audio_file)
    chunk_size = chunk_duration * 1000  # Convert seconds to milliseconds
    chunks = []
    for i in range(0, len(audio), chunk_size):
        chunk = audio[i:i + chunk_size]
        chunk_buffer = io.BytesIO()
        chunk.export(chunk_buffer, format='wav')
        chunk_buffer.seek(0)
        chunks.append(chunk_buffer)
    return chunks


# Extract MFCC features for emotion prediction
def extract_features(audio_chunk):
    y, sr = librosa.load(audio_chunk, sr=None)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
    return np.mean(mfccs.T, axis=0)


# Predict emotions from audio chunks
def predict_emotion(chunks):
    emotions = defaultdict(int)
    for chunk in chunks:
        try:
            features = extract_features(chunk)
            features = features.reshape(1, -1)
            predicted_emotion = model.predict(features)
            decoded_emotion = label_encoder.inverse_transform([predicted_emotion[0]])[0]
            emotions[decoded_emotion] += 1
        except Exception as e:
            print(f"Error processing chunk: {e}")
            emotions['unknown'] += 1
    return dict(emotions)


# Calculate confidence level based on emotion frequencies
def calculate_confidence(emotions):
    confidence_level = 0
    emotion_frame_value = sum(emotions.values())

    for emotion, value in emotions.items():
        if emotion == 'happy':
            confidence_level += 0.99 * value
        elif emotion in ['neutral', 'calm']:
            confidence_level += 0.95 * value
        elif emotion == 'surprise':
            confidence_level += 0.8 * value
        elif emotion in ['sad', 'fearful']:
            confidence_level += 0.7 * value
        elif emotion in ['angry', 'disgust']:
            confidence_level += 0.6 * value

    if emotion_frame_value == 0:
        return 0
    confidence = round((confidence_level / emotion_frame_value) * 100, 2)
    return confidence


@audio_emotion_bp.route('/process_video', methods=['POST'])
def process_video():
    data = request.json
    if 'video_url' not in data:
        return jsonify({'error': 'No video URL provided'}), 400

    video_url = data['video_url']
    video_file = 'downloaded_video.mp4'
    output_wav = 'audio.wav'

    try:
        # Download the video
        video_response = requests.get(video_url, stream=True)
        if video_response.status_code != 200:
            return jsonify({'error': 'Failed to download video'}), 400

        # Save the video file
        with open(video_file, 'wb') as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Convert video to WAV
        video_to_wav(video_file, output_wav)

        # Split audio into chunks and predict emotions
        chunks = split_audio(output_wav)
        emotions = predict_emotion(chunks)

        # Calculate confidence level
        confidence = calculate_confidence(emotions)

        return jsonify({'confidence_level': confidence})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


    finally:

        # Clean up temporary files
        if os.path.exists(video_file):
            try:
                os.remove(video_file)
            except PermissionError as pe:
                print(f"PermissionError during file deletion: {pe}")
        if os.path.exists(output_wav):
            os.remove(output_wav)
