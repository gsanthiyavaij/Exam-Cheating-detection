# 🎓 Smart Exam Hall Cheating Detection System


This is an intelligent proctoring system that uses **face recognition**, **cheating behavior detection**, **audio surveillance**, and a modern **GUI** to detect and report cheating or unauthorized activities in real time during examinations.

📌 Features

 👤 Face Recognition & Attendance (`face2.py`)
- Detects and recognizes students using images in the `pics/` folder.
- Records attendance in `Attendance.csv`.
- Alerts invigilators via email with images if an unknown face is detected.
- Uses voice feedback ("Access Granted" / "Access Denied").

 🔍 Cheating & Mobile Detection (`27.py`)
- Detects cheating behavior and mobile usage using **YOLOv8 models**.
- Activates **buzzer** via Arduino when suspicious activity is detected.
- Records **10 seconds of video and audio** on detection.
- Sends captured video/audio via email to the invigilator.

 🖥 GUI Control Panel (`gui3.py`)
- Built with `customtkinter`.
- Allows invigilators to **start/stop**:
  - Authentication system (face recognition)
  - Cheating detection system (YOLO + audio)
- Each program runs independently using `subprocess`.

---

 🧰 Tech Stack

| Category          | Tools/Libraries                          |
|------------------|-------------------------------------------|
| Face Detection    | `face_recognition`, `cv2`                |
| Object Detection  | `ultralytics`, `YOLOv8`                  |
| Audio Detection   | `pyaudio`, `webrtcvad`, `wave`           |
| GUI               | `customtkinter`                          |
| Email Alerts      | `smtplib`, `email.mime`                  |
| Speech Feedback   | `pyttsx3`                                |
| Hardware Control  | `pyserial` (for Arduino buzzer)          |

---

 📁 Project Structure

cheat/
├── 27.py                    # Cheating & mobile detection + audio alert
├── face2.py                 # Face recognition and attendance logging
├── gui3.py                  # GUI to control the system
├── yolov8\_trained\_model.pt              # YOLO model for cheating
├── yolov8\_trained\_model (1).pt          # YOLO model for mobile detection
├── Attendance.csv           # Stores attendance
├── pics/                    # Folder containing student images

````

 Dataset Sources

This project uses two datasets from Roboflow:

- Mobile phone detection dataset: [Roboflow Mobile Phone Dataset](https://universe.roboflow.com/m17865515473-163-com/mobilephone-wusj2)
- Exam cheating detection dataset: [Roboflow Exam Cheating Dataset](https://universe.roboflow.com/trn-quang-tip/exam-cheating-9iz1y-rrfsz)

The models (`yolov8_trained_model.pt` and `yolov8_trained_model(1).pt`) were trained on these datasets.




 ▶️ How to Run

 1. Install Required Libraries

```bash
pip install opencv-python face_recognition numpy pyttsx3 pyserial webrtcvad pyaudio ultralytics customtkinter
````

 2. Place Student Images

Add student face images in the `pics/` folder with filenames as their names (e.g., `John_Doe.jpg`).

 3. Update Paths and Config

* In `gui3.py`: Update paths to `face2.py` and `27.py`
* In `27.py`: Update YOLO model paths and Arduino port (e.g., `COM3`)
* In all scripts: Replace email and app password with your credentials or move them to a `.env` file for security.

 4. Start the GUI

```bash
python gui3.py
```

---

 📧 Notification System

| Event                       | Action Taken                         |
| --------------------------- | ------------------------------------ |
| Unknown face detected       | Saves images & sends alert email     |
| Cheating or mobile detected | Activates buzzer + sends video email |
| Speech detected             | Activates buzzer + sends audio email |

---

 🔐 Security Notes

* Do **not** hardcode email passwords in production. Use `.env` files or secure vaults.
* Use [App Passwords](https://support.google.com/accounts/answer/185833) for Gmail instead of your main account password.

---

 🧾 License

This project is open-source under the **MIT License**.

---

 👩‍💻 Author

Developed by **Santhiya G**

---



Would you like me to:
- Save this `README.md` as a file and give it to you?
- Help you prepare a `.gitignore` and `.env` example?
- Assist in pushing this to GitHub step-by-step?

Let me know!

