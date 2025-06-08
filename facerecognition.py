import cv2
import face_recognition
import numpy as np
import os
import pyttsx3
import threading
import time
import queue
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email credentials
EMAIL_ADDRESS = "vscorpio791@gmail.com"  # Replace with your email
EMAIL_PASSWORD = "ggcxtwosexczbsqb"   # Replace with your email password
RECIPIENT_EMAIL = "santhiyavaij@gmail.com"  # Replace with the recipient's email

# Function to send email with photos
def send_email_with_photos(subject, body, photos):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        for photo in photos:
            with open(photo, 'rb') as file:
                img_data = file.read()
            part = MIMEText(img_data, 'base64', 'utf-8')
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(photo)}')
            part.add_header('Content-Transfer-Encoding', 'base64')
            msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email with photos sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Initialize text-to-speech engine
engine = pyttsx3.init()
speech_queue = queue.Queue()

# Path to the folder containing images for attendance
path = 'pics'
if not os.path.exists(path):
    os.makedirs(path)

images = []
classNames = []
myList = os.listdir(path)

for cl in myList:
    curImg = cv2.imread(f'{path}/{cl}')
    if curImg is None:
        print(f"Image {cl} could not be loaded. Skipping.")
        continue
    images.append(curImg)
    classNames.append(os.path.splitext(cl)[0])

def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(img)
        if len(encodings) > 0:
            encode = encodings[0]
            encodeList.append(encode)
        else:
            print("No face found in image. Skipping encoding for this image.")
    return encodeList

encodeListKnown = findEncodings(images)
if not encodeListKnown:
    print("No valid encodings found. Ensure your 'pics' folder contains images with detectable faces.")
    exit()
print('Encoding Complete')

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 30)

def markAttendance(name):
    with open('Attendance.csv', 'r+') as f:
        myDataList = f.readlines()
        nameList = []
        for line in myDataList:
            entry = line.split(',')
            nameList.append(entry[0])
        if name not in nameList:
            now = datetime.now()
            dtString = now.strftime('%H:%M:%S')
            f.writelines(f'\n{name},{dtString}')


def clean_name(name):
    return "_".join(name.split('_')[:2])

def speak_from_queue():
    while True:
        text = speech_queue.get()
        if text is None:
            break
        engine.say(text)
        engine.runAndWait()

speech_thread = threading.Thread(target=speak_from_queue)
speech_thread.daemon = True
speech_thread.start()

frame_skip = 5
frame_count = 0
last_recognition_time = time.time()
cooldown_period = 10  # Cooldown period in seconds
last_recognition = {}

while True:
    success, img = cap.read()
    if success:
        frame_count += 1
        if frame_count % frame_skip == 0:
            imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
            imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

            facesCurFrame = face_recognition.face_locations(imgS)
            encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

            for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace, tolerance=0.5)
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
                matchIndex = np.argmin(faceDis)

                recognized_name = "Unknown"
                confidence_threshold = 0.45  # Confidence threshold for recognition

                if matches[matchIndex] and faceDis[matchIndex] < confidence_threshold:
                    recognized_name = clean_name(classNames[matchIndex].upper())
                    current_time = time.time()
                    if recognized_name not in last_recognition or \
                            (current_time - last_recognition[recognized_name]) > cooldown_period:
                        print(f"Recognized: {recognized_name}")
                        speech_queue.put(f"Access Granted: {recognized_name}")
                        markAttendance(recognized_name)
                        last_recognition[recognized_name] = current_time
                    else:
                        print(f"Skipping repeat announcement for {recognized_name}")
                else:
                    print("Recognized: Unknown")
                    speech_queue.put("Access Denied")

                    unauthorized_photos = []
                    for i in range(3):
                        photo_filename = f"unauthorized_{time.time():.0f}_{i + 1}.jpg"
                        cv2.imwrite(photo_filename, img)
                        unauthorized_photos.append(photo_filename)
                        time.sleep(0.5)

                    threading.Thread(
                        target=send_email_with_photos,
                        args=(
                            "Unauthorized Access Detected",
                            "An unauthorized person was detected by the system. See attached photos.",
                            unauthorized_photos,
                        ),
                    ).start()

                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                color = (0, 255, 0) if matches[matchIndex] else (0, 0, 255)

                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                cv2.rectangle(img, (x1, y2 - 35), (x2, y2), color, cv2.FILLED)
                cv2.putText(img, recognized_name,
                            (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

        cv2.imshow("Face Recognition", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
speech_queue.put(None)
speech_thread.join()
cv2.destroyAllWindows()
