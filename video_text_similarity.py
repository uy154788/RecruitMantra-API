import os
import json
import urllib.request
from flask import Blueprint, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import moviepy.editor as mp
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import make_chunks
from sentence_transformers import SentenceTransformer, util

# Initialize Blueprint
video_text_similarity_bp = Blueprint('video_text_similarity', __name__)

# Extract audio from video
def extract_audio_from_video(video_path, audio_output_path):
    """Extracts audio from the video and saves it as a .wav file."""
    video = mp.VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(audio_output_path)

# Split audio into chunks
def split_audio(audio_path, chunk_length_ms=60000):
    """Splits audio into chunks of chunk_length_ms milliseconds (default: 60 seconds) and returns a list of chunks."""
    audio = AudioSegment.from_wav(audio_path)
    chunks = make_chunks(audio, chunk_length_ms)
    return chunks

# Convert speech in an audio chunk to text
def speech_to_text(audio_chunk):
    """Converts speech from an audio chunk to text using Google's Speech Recognition API."""
    recognizer = sr.Recognizer()
    chunk_path = "temp_chunk.wav"
    audio_chunk.export(chunk_path, format="wav")

    try:
        with sr.AudioFile(chunk_path) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        text = "[Unintelligible]"
    except sr.RequestError as e:
        text = f"[Request failed: {e}]"
    finally:
        if os.path.exists(chunk_path):
            os.remove(chunk_path)

    return text

# Process audio chunks and combine the extracted text
def process_audio_chunks(audio_path):
    """Processes an audio file by splitting it into chunks and converting each chunk to text."""
    chunks = split_audio(audio_path)
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(speech_to_text, chunks))
    return " ".join(results).strip()

# Compare the extracted text with the original answer
def compare_texts(original_answer, user_answer):
    """Compares two texts using SentenceTransformers to calculate semantic similarity."""
    model = SentenceTransformer('all-MiniLM-L6-v2')
    original_embedding = model.encode(original_answer, convert_to_tensor=True)
    user_embedding = model.encode(user_answer, convert_to_tensor=True)
    similarity = util.cos_sim(original_embedding, user_embedding)
    result = round(similarity.item() * 100, 2)
    return max(0, result)

# Read the JSON data from the file
def read_json_from_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Extract the answer for a given question
def get_answer(question, data):
    return data.get(question, "Question not found.")

@video_text_similarity_bp.route('/process', methods=['POST'])
def process_request():
    request_data = request.get_json()
    question = request_data.get('question')
    video_url = request_data.get('video_url')

    if not question or not video_url:
        return jsonify({"error": "Please provide both question and video_url in the request."}), 400

    # Download video
    video_file = "input_video.mp4"
    audio_file = "extracted_audio.wav"
    try:
        urllib.request.urlretrieve(video_url, video_file)
    except Exception as e:
        return jsonify({"error": f"Error downloading video: {e}"}), 500

    # Load answer data
    file_path = 'dict.txt'
    data = read_json_from_file(file_path)
    original_answer = get_answer(question, data)
    if original_answer == "Question not found.":
        return jsonify({"error": "Question not found in the data."}), 404

    # Extract audio and process text
    extract_audio_from_video(video_file, audio_file)
    extracted_text = process_audio_chunks(audio_file)
    similarity = compare_texts(original_answer, extracted_text)

    # Clean up files
    for temp_file in [audio_file, video_file]:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    return jsonify({
        # "original_answer": original_answer,
        # "extracted_text": extracted_text,
        "Accuracy": similarity
    })
