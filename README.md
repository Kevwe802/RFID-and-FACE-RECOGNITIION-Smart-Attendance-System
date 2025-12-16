# Smart Attendance System

**AI & RFID-based Attendance System with Face Recognition and Arduino Integration**

---

## Overview

This system combines **RFID cards**, **face recognition**, and **Arduino-controlled hardware** to automate attendance tracking in real-time.  
It stores data in **MySQL**, provides course-wise attendance, and notifies users via **LEDs and buzzer feedback**.  

---

## Features

- **RFID-Based Identification**: Scan ID cards for automatic check-in.  
- **Face Recognition**: ESP32-CAM verifies identity for enhanced security.  
- **Real-Time Attendance Logging**: Attendance saved directly to MySQL database.  
- **Hardware Feedback**: Arduino-controlled buzzer and LEDs indicate success or failure.  
- **Course-Wise Management**: Select course code before starting attendance.  
- **Absentee Tracking**: Automatically marks absentees if not checked in within 24 hours.

---

## Demo

**Video Demo:** [Watch Demo](demo/demo_video.mp4)

**Screenshots:**

![Attendance Dashboard](images/dashboard.png)  
![Face Recognition Capture](images/face_recognition_capture.png)  


---

## Tech Stack

- **Backend**: Python 3  
- **Database**: MySQL  
- **Hardware**: Arduino, ESP32-CAM  
- **Libraries**: OpenCV, face_recognition, pyserial  

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/...
cd RFID-and-FACE-RECOGNITIION-Smart-Attendance-System

```
2. Install dependencies
   
```bash
pip install -r requirements.txt

```
3. Configure MySQL:
   
```bash
Create the database and tables using database.sql.

Update config.py with your database credentials.

```

4. Connect Arduino to the correct COM port.

Usage

1. Run the main Python script:
   
```bash
python main.py

```
2. Select a course code.

3. Scan RFID cards or use face recognition.

4. Attendance is logged in the database.

5. Arduino LEDs and Buzzer indicate success or failure.

## Project Structure
```bash
RFID-and-FACE-RECOGNITION-Smart-Attendance-System/
│
├── README.md                      # Project documentation
├── requirements.txt               # Python dependencies
│
├── arduino/                       # Microcontroller code
│   ├── arduino.ino                # RFID + LED + buzzer logic
│   │
│   ├── demo/                      # Arduino demo files (if any)
│   │
│   └── WifiCam/                   # ESP32-CAM firmware
│       ├── handlers.cpp
│       ├── WifiCam.hpp
│       ├── WifiCam.ino
│       └── README.md
│
├── attendance/                    # Attendance data & face images
│   ├── Attendance.csv             # Attendance records
│   │
│   └── image_folder/              # Registered student images
│       ├── Eta.JPG
│       └── Ovwigho Kevwe.jpg
│
├── Attendance system update main/ # Web-based attendance system
│   ├── app2.py                    # Main Flask application
│   ├── script.py                  # Supporting logic
│   │
│   ├── static/                    # Frontend static files
│   │   ├── logo.jpg
│   │   ├── script.js
│   │   └── style.css
│   │
│   ├── templates/                 # HTML templates
│   │   ├── Base.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── select_course.html
│   │   ├── attendance_report.html
│   │   ├── table.html
│   │   ├── table_view.html
│   │   ├── button.html
│   │   ├── processing.html
│   │   └── logo.jpg
│   │
│   └── __pycache__/               # Python cache (not important)
│
└── images/                        # Project screenshots
    ├── circuit_diagram.PNG
    ├── dashboard.png
    ├── face_recognition_capture.png
    └── student_table.png

```
## System Circuit Diagram

**Screenshots:** ![Face Recognition Capture](images/circuit_diagram.PNG)

