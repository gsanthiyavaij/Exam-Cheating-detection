import cv2
from ultralytics import YOLO
import serial
import webrtcvad
import numpy as np
import pyaudio
import wave
import time
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

# Global flag to indicate recording in progress
recording_in_progress = threading.Event()

# Connect to Arduino
arduino = serial.Serial('COM3', 9600)  # Replace 'COM3' with the correct port for your Arduino

# Load the YOLO models
cheating_model = YOLO(r"C:\Users\USER\Downloads\yolov8_trained_model.pt")  # Cheating detection model
mobile_model = YOLO(r"C:\Users\USER\Downloads\yolov8_trained_model (1).pt")  # Mobile detection model

# Start the webcam feed
cap = cv2.VideoCapture(0)

# Set the desired width and height for the camera feed
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)


# Define the class IDs for "cheating" and "mobile"
cheating_class_id = 0  # Replace with the class ID for cheating in your dataset
mobile_class_id = 0  # Replace with the class ID for mobile in your dataset

# Parameters for VAD and Audio Recording
sample_rate = 16000  # Audio sample rate (16kHz for WebRTC VAD)
frame_duration = 10  # Duration of each frame in ms
frame_size = int(sample_rate * frame_duration / 1000)  # Frame size in samples
recording_duration = 10  # Duration of the voice recording in seconds

# Initialize the WebRTC VAD (1 = Aggressive mode)
vad = webrtcvad.Vad(2)  # Can be set to 0 (very aggressive), 1 (aggressive), 2 (moderate), 3 (least aggressive)

# Function to detect speech in audio data
def detect_speech(audio_data):
    frames = []
    for start in range(0, len(audio_data), frame_size):
        end = min(start + frame_size, len(audio_data))
        frame = audio_data[start:end]
        
        # Apply VAD to each frame
        is_speech = vad.is_speech(frame.tobytes(), sample_rate)
        frames.append(is_speech)
    
    return frames

# Function to record 10 seconds of audio when speech is detected
def record_audio(stream, duration=10):
    frames = []
    start_time = time.time()
    print("Recording 10 seconds of audio...")

    while time.time() - start_time < duration:
        audio_data = np.frombuffer(stream.read(frame_size), dtype=np.int16)
        frames.append(audio_data.tobytes())

    return b''.join(frames)

# Function to save recorded audio to a WAV file
def save_audio(file_name, audio_data):
    with wave.open(file_name, 'wb') as wf:
        wf.setnchannels(1)  # Mono channel
        wf.setsampwidth(2)  # 16-bit samples
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data)
    print(f"Audio saved as {file_name}")

# Function to send the audio file via email
def send_audio_email(filename, subject="Suspicious Noise Detected"):
    print(f"Preparing to send audio email with {filename}...")

    wait_time = 15  # Maximum wait time in seconds
    elapsed_time = 0

    # Wait for the file to become available and non-zero
    while elapsed_time < wait_time:
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            break
        time.sleep(1)  # Wait for 1 second
        elapsed_time += 1
    else:
        print(f"Error: File {filename} is not ready or is empty.")
        return

    # Send email with audio file
    try:
        sender_email = "vscorpio791@gmail.com"  # Replace with your Gmail address
        app_password = "ggcxtwosexczbsqb"  # Replace with your App Password
        receiver_email = "santhiyavaij@gmail.com"  # Replace with the recipient's email

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        with open(filename, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename={filename}")
            msg.attach(part)

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print(f"Email sent successfully with attachment: {filename}")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Function to analyze live microphone audio and detect speech
def analyze_live_audio():
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, input=True, frames_per_buffer=frame_size)
    
    print("Recording... Press 'Ctrl+C' to stop.")
    
    try:
        speech_detected = False  # Variable to track if speech is detected
        
        while True:
            audio_data = np.frombuffer(stream.read(frame_size), dtype=np.int16)
            
            # Detect speech in the live audio data
            frames = detect_speech(audio_data)
            if any(frames) and not speech_detected:  # If speech detected and not already recording
                print("Speech detected! Recording for 10 seconds...")

                # Record 10 seconds of audio
                recorded_audio = record_audio(stream, duration=recording_duration)
                
                # Save the recorded audio to a file
                timestamp = int(time.time())
                file_name = f"recorded_audio_{timestamp}.wav"
                save_audio(file_name, recorded_audio)

                # Trigger buzzer if speech is detected
                arduino.write(b'B')  # Send the signal to Arduino (Buzzing)
                print("Speech detected! Buzzing...")

                speech_detected = True  # Set flag to indicate that speech was detected and recorded
                time.sleep(1)  # Add a short delay to avoid immediate re-triggering

                # Send the recorded audio via email
                send_audio_email(file_name)

            elif not any(frames):
                speech_detected = False  # Reset flag when no speech is detected

            else:
                print("No speech detected.")
    
    except KeyboardInterrupt:
        print("\nRecording stopped.")
        stream.stop_stream()
        stream.close()
        p.terminate()

# Start audio detection in a separate thread
audio_detection_thread = threading.Thread(target=analyze_live_audio)
audio_detection_thread.daemon = True  # Ensures the thread exits with the main program
audio_detection_thread.start()

# Parameters for video recording
video_duration = 10  # Duration for video recording in seconds

# Global flag to prevent duplicate recordings
recording_in_progress = False

# Function to record a video asynchronously
def record_video_async(filename, duration=10, fps=10):
    def record():
        print(f"Starting video recording: {filename}")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(filename, fourcc, fps, (640, 480))

        start_time = time.time()
        frame_interval = 1.0 / fps  # Interval between frames
        frames_written = 0

        while time.time() - start_time < duration:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            out.write(frame)
            frames_written += 1
            time.sleep(frame_interval)  # Maintain desired frame rate

        out.release()
        print(f"Video saved as {filename}")
        print(f"Frames written: {frames_written}")

    # Run video recording in a separate thread
    threading.Thread(target=record).start()

# Function to send the video file via email
def send_email(filename, subject="Detection Alert"):
    print(f"Preparing to send email with {filename}...")
    wait_time = 15  # Maximum wait time in seconds
    elapsed_time = 0

    # Wait for the file to become available and non-zero
    while elapsed_time < wait_time:
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            break
        time.sleep(1)  # Wait for 1 second
        elapsed_time += 1
    else:
        print(f"Error: File {filename} is not ready or is empty.")
        return

    # Send email as before
    try:
        sender_email = "vscorpio791@gmail.com"  # Replace with your Gmail address
        app_password = "ggcxtwosexczbsqb"  # Replace with your App Password
        receiver_email = "santhiyavaij@gmail.com"  # Replace with the recipient's email

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        with open(filename, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename={filename}")
            msg.attach(part)

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print(f"Email sent successfully with attachment: {filename}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        
last_event_time = 0  # Timestamp of the last recorded event

def send_email_with_video(video_filename, subject):
    # Wait until the file is created and closed by the VideoWriter
    while not os.path.exists(video_filename):
        time.sleep(1)

    print(f"Preparing to send email with {video_filename}...")
    send_email(video_filename, subject)

def process_detections(results, class_id, confidence_threshold, label):
    global recording_in_progress, last_event_time

    for detection in results[0].boxes:
        cls_id = int(detection.cls)
        confidence = float(detection.conf)

        if cls_id == class_id and confidence > confidence_threshold:
            current_time = time.time()

            if recording_in_progress or current_time - last_event_time < 10:
                return  # Avoid duplicate recordings

            print(f"{label.capitalize()} detected! Buzzing...")

            if label == "cheating":
                arduino.write(b'N')
            elif label == "mobile":
                arduino.write(b'M')

            # Record and send video
            last_event_time = current_time
            video_filename = f"{label}_video_{int(current_time)}.avi"
            record_video_async(video_filename, duration=10)

            # Delay email until video recording is done
            threading.Thread(target=send_email_with_video, args=(video_filename, f"{label.capitalize()} Alert")).start()

# Main function for multi-model detection
def detect_cheating_and_mobile():
    
     # Set the OpenCV window to fullscreen
    cv2.namedWindow("Multi-Model Detection", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Multi-Model Detection", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Perform inference for both models
        cheating_results = cheating_model(frame)
        mobile_results = mobile_model(frame)

        # Process detections for cheating
        process_detections(cheating_results, cheating_class_id, 0.55, "cheating")

        # Process detections for mobile
        process_detections(mobile_results, mobile_class_id, 0.65, "mobile")

        # Render the results on the frame
        cheating_frame = cheating_results[0].plot()
        mobile_frame = mobile_results[0].plot()
        combined_frame = cv2.addWeighted(cheating_frame, 0.5, mobile_frame, 0.5, 0)

        # Display the combined frame
        cv2.imshow("Multi-Model Detection", combined_frame)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Start the detection
if __name__ == "__main__":
    try:
        detect_cheating_and_mobile()
    finally:
        cap.release()
        cv2.destroyAllWindows()
        arduino.close()
