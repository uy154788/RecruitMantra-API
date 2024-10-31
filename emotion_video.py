from flask import Blueprint, request, jsonify
import cv2
import mediapipe as mp
from deepface import DeepFace
from collections import defaultdict
import os

# Initialize the Blueprint
emotion_video_bp = Blueprint('emotion_video', __name__)

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,  # Adjust if handling multiple faces
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

@emotion_video_bp.route('/upload', methods=['POST'])
def process_video():
    # Check if a video URL is provided
    data = request.json
    video_path = data.get('video_url') if data else None

    # Initialize video capture
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return jsonify({"error": f"Error opening video file {video_path}"}), 500

    # Initialize emotion counts and confidences
    emotion_counts = defaultdict(int)
    emotion_confidences = defaultdict(list)
    no_face_detected = 0
    frame_skip = 12  # Process every 5th frame
    frame_number = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame_number += 1

        # Skip frames for faster processing
        if frame_number % frame_skip != 0:
            continue

        # Resize frame for faster processing
        aspect_ratio = 320 / frame.shape[1]
        frame = cv2.resize(frame, (320, int(frame.shape[0] * aspect_ratio)))

        # Convert frame to RGB for processing
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect faces using MediaPipe Face Mesh
        results = face_mesh.process(image_rgb)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                h, w, _ = frame.shape
                x_coords = [landmark.x for landmark in face_landmarks.landmark]
                y_coords = [landmark.y for landmark in face_landmarks.landmark]
                x_min, x_max = int(min(x_coords) * w), int(max(x_coords) * w)
                y_min, y_max = int(min(y_coords) * h), int(max(y_coords) * h)

                # Add padding
                padding = 20
                x_min, y_min = max(x_min - padding, 0), max(y_min - padding, 0)
                x_max, y_max = min(x_max + padding, w), min(y_max + padding, h)

                # Crop the face region
                face_roi = frame[y_min:y_max, x_min:x_max]

                try:
                    # Use DeepFace to analyze the face region
                    analysis = DeepFace.analyze(face_roi, actions=['emotion'], enforce_detection=False)

                    # If multiple analyses, take the first one
                    if isinstance(analysis, list):
                        analysis = analysis[0]

                    dominant_emotion = analysis['dominant_emotion']
                    emotion_confidence = analysis['emotion'][dominant_emotion]

                    # Update counts and confidences
                    emotion_counts[dominant_emotion] += 1
                    emotion_confidences[dominant_emotion].append(emotion_confidence)

                except Exception as e:
                    print(f"Error processing frame {frame_number}: {e}")
                    continue
        else:
            no_face_detected += 1

    cap.release()

    # Delete the temporary video file if created
    if os.path.exists(video_path):
        os.remove(video_path)

    confidence_level = 0
    emotion_frame_value = 0
    for emotion, value in emotion_counts.items():
        emotion_frame_value += value
        if emotion == 'happy':
            confidence_level += 0.95 * value
        elif emotion == 'neutral':
            confidence_level += 0.9 * value
        elif emotion == 'surprise':
            confidence_level += 0.6 * value
        elif emotion in ['sad', 'fear']:
            confidence_level += 0.5 * value
        elif emotion in ['angry', 'disgust']:
            confidence_level += 0.3 * value

    total_valid_frame = emotion_frame_value + no_face_detected
    confidence = round((confidence_level / total_valid_frame) * 100, 2)

    # Return the results as JSON
    return jsonify({"average_confidence": confidence})
