import customtkinter as ctk
import subprocess
import threading

# Global variables to store subprocesses
process1 = None
process2 = None

def run_program1():
    global process1  # Declare process1 as global
    def start_process():
        global process1  # Ensure it's the global variable being modified
        program1_path = "D:\\Documents\\cheat\\face2.py"
        process1 = subprocess.Popen(["python", program1_path])
    threading.Thread(target=start_process, daemon=True).start()

def stop_program1():
    global process1
    if process1 is not None:
        process1.terminate()
        process1 = None

def run_program2():
    global process2  # Declare process2 as global
    def start_process():
        global process2  # Ensure it's the global variable being modified
        program2_path = "D:\\Documents\\cheat\\27.py"
        process2 = subprocess.Popen(["python", program2_path])
    threading.Thread(target=start_process, daemon=True).start()

def stop_program2():
    global process2
    if process2 is not None:
        process2.terminate()
        process2 = None

# Main app window
app = ctk.CTk()
app.title("Exam Proctoring")
app.geometry("800x600")

# Left Section for Authentication
frame_left = ctk.CTkFrame(app)
frame_left.pack(side="left", fill="both", expand=True, padx=10, pady=10)
ctk.CTkLabel(frame_left, text="Authentication").pack(pady=10)
auth_button = ctk.CTkButton(frame_left, text="Start Authentication", command=run_program1)
auth_button.pack(pady=5)
stop_auth_button = ctk.CTkButton(frame_left, text="Stop Authentication", command=stop_program1)
stop_auth_button.pack()

# Right Section for Cheating Detection
frame_right = ctk.CTkFrame(app)
frame_right.pack(side="right", fill="both", expand=True, padx=10, pady=10)
ctk.CTkLabel(frame_right, text="Cheating Detection").pack(pady=10)
cheat_button = ctk.CTkButton(frame_right, text="Start Cheating Detection", command=run_program2)
cheat_button.pack(pady=5)
stop_cheat_button = ctk.CTkButton(frame_right, text="Stop Cheating Detection", command=stop_program2)
stop_cheat_button.pack()

app.mainloop()
