from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pymysql
import os
import threading
import base64
import cv2
import face_recognition
import serial
import time
import numpy as np
import urllib.request
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import atexit
from serial.serialutil import SerialException

app = Flask(__name__)
app.secret_key = 'my_secret_key'

# --- Config ---
db_config = {'host': 'localhost', 'user': 'root', 'password': '', 'database': 'db_arduino'}
IMAGE_FOLDER = r'C:\Arduino\ATTENDANCE\attendance\image_folder'
os.makedirs(IMAGE_FOLDER, exist_ok=True)
CAM_URL = 'http://192.168.5.116/cam-hi.jpg'
SERIAL_PORT = 'COM3'
BAUD_RATE = 115200

# --- Globals ---
latest_uid = None
selected_course_code = None
attendance_thread = None
attendance_running = False
uid_lock = threading.Lock()  # Added for thread safety

# --- Serial setup ---
def open_serial(port=SERIAL_PORT, baud=BAUD_RATE, timeout=1, retry_delay=1):
    while True:
        try:
            s = serial.Serial(port, baud, timeout=timeout)
            print(f"[INFO] Opened serial port {port}")
            return s
        except SerialException as e:
            print(f"[WARN] Could not open {port}: {e}. Retrying...")
            time.sleep(retry_delay)

ser = open_serial()
atexit.register(lambda: ser and ser.is_open and ser.close())

# --- UID listener thread ---
def listen_uid():
    global latest_uid, ser
    while True:
        try:
            if not ser.is_open:
                print("[INFO] Serial port closed, attempting to reconnect...")
                ser.close()
                ser = open_serial()
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith("UID"):
                    with uid_lock:
                        latest_uid = line.split(":")[-1].strip().replace(" ", "")
                        print(f"[UID Listener] Latest UID: {latest_uid}")
        except SerialException as e:
            print(f"[Serial error] {e}, attempting to reconnect...")
            ser.close()
            time.sleep(1)  # Delay before reconnect attempt
        except Exception as e:
            print(f"[Unexpected serial error] {e}")
        time.sleep(0.05)  # Reduced from 0.1 to improve responsiveness

threading.Thread(target=listen_uid, daemon=True).start()

# --- DB helpers ---
def get_db():
    return pymysql.connect(**db_config)

def get_table_names():
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            return [table[0] for table in cursor.fetchall()]

def get_courses():
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT Course_code FROM courses")
            return [course[0] for course in cursor.fetchall()]

# --- Load face encodings ---
def reload_face_encodings():
    global known_encodings, known_names
    known_encodings, known_names = [], []
    for f in os.listdir(IMAGE_FOLDER):
        path = os.path.join(IMAGE_FOLDER, f)
        img = cv2.imread(path)
        if img is not None:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            enc = face_recognition.face_encodings(rgb)
            if enc:
                known_encodings.append(enc[0])
                known_names.append(os.path.splitext(f)[0])
    print(f"[INFO] Reloaded {len(known_names)} faces.")

# Call after registration or on app start
reload_face_encodings()

# --- Helpers to update Arduino ---
def update_lcd(name, message):
    try:
        ser.write(f"!{name}${message}\n".encode())
        print(f"[LCD] Sent: !{name}${message}")
    except Exception as e:
        print("[LCD error]", e)

def update_status(status):
    try:
        if status == "PRESENT":
            ser.write(b"PRESENT\n")
            print("[Arduino] Sent: PRESENT")
        elif status == "NOT_RECOGNIZED":
            ser.write(b"NOT_RECOGNIZED\n")
            print("[Arduino] Sent: NOT_RECOGNIZED")
    except Exception as e:
        print("[Serial write error]", e)

# --- Mark attendance ---
def mark_attendance(name, uid, course):
    now = datetime.now()
    try:
        with get_db() as conn:
            with conn.cursor() as c:
                print(f"[DB] Checking recent attendance for: {name}, UID={uid}, course={course}")
                c.execute("""SELECT COUNT(*) FROM students_attendance 
                             WHERE Name=%s AND UID=%s AND Course_code=%s AND Timestamp >= %s""",
                          (name, uid, course, now - timedelta(hours=2)))
                if c.fetchone()[0] > 0:
                    update_lcd(name, "Already Present")
                    update_status("PRESENT")
                    print(f"[INFO] {name} already marked recently")
                    return
                c.execute("""INSERT INTO students_attendance (Name, UID, Attendance, Timestamp, Course_code)
                             VALUES (%s, %s, 'Present', %s, %s)""",
                          (name, uid, now, course))
                c.execute("""INSERT INTO attendance_records (Name, UID, Timestamp, Course_code, Present_Count, Absent_Count)
                             VALUES (%s, %s, %s, %s, 1, 0)
                             ON DUPLICATE KEY UPDATE Present_Count=Present_Count+1""",
                          (name, uid, now, course))
                conn.commit()
                print("[DB] Commit done")
        update_lcd(name, "PRESENT")
        update_status("PRESENT")
        print(f"[INFO] Attendance marked for {name}")
    except Exception as e:
        print("[DB error]", e)
        import traceback
        traceback.print_exc()

def check_uid_in_database(uid):
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT Name FROM students WHERE UID=%s", (uid,))
                result = cursor.fetchone()
                return result[0] if result else None
    except Exception as e:
        print("[DB error in check_uid_in_database]:", e)
        return None

def capture_and_recognize_face(timeout=30):
    """
    Stream video from ESP32-CAM, draw boxes and names, 
    return first recognized name (or None after timeout).
    """
    start_time = time.time()
    recognized_name = None
    retries = 3  # Number of retry attempts for camera connection
    retry_delay = 1  # Seconds to wait between retries

    print("[INFO] Starting live face recognition stream...")

    while time.time() - start_time < timeout:
        try:
            # Attempt to read frame from camera with retries
            for attempt in range(retries):
                try:
                    img_resp = urllib.request.urlopen(CAM_URL, timeout=5)
                    imgnp = np.array(bytearray(img_resp.read()), dtype=np.uint8)
                    img = cv2.imdecode(imgnp, -1)
                    if img is None:
                        raise ValueError("Failed to decode image")
                    break
                except (urllib.error.URLError, ValueError) as e:
                    print(f"[Camera error] Attempt {attempt + 1}/{retries}: {e}")
                    if attempt == retries - 1:
                        print("[ERROR] Camera unavailable after retries")
                        return None
                    time.sleep(retry_delay)

            # Resize for faster face detection
            small_img = cv2.resize(img, (0, 0), fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
            rgb_small_img = cv2.cvtColor(small_img, cv2.COLOR_BGR2RGB)

            # Detect and encode faces
            face_locations = face_recognition.face_locations(rgb_small_img, number_of_times_to_upsample=1)
            if not face_locations:
                print("[DEBUG] No faces detected in frame")
                cv2.imshow('ESP32-CAM Feed', cv2.resize(img, (800, 600)))
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("[INFO] Stream manually stopped by user.")
                    break
                continue

            face_encodings = face_recognition.face_encodings(rgb_small_img, face_locations)
            print(f"[DEBUG] Detected {len(face_encodings)} faces")

            for encode_face, face_loc in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(known_encodings, encode_face, tolerance=0.6)
                face_distances = face_recognition.face_distance(known_encodings, encode_face)
                best_match_index = np.argmin(face_distances)

                if matches[best_match_index]:
                    recognized_name = known_names[best_match_index]
                    # Scale back face location to original frame
                    y1, x2, y2, x1 = [v * 4 for v in face_loc]
                    # Draw box and name on the original image
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                    cv2.putText(img, recognized_name, (x1 + 6, y2 - 6), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    print(f"[DEBUG] Drawing box and name: {recognized_name} at ({x1}, {y1}, {x2}, {y2})")
                    break  # Exit loop on first match

            # Display the annotated image
            display_img = cv2.resize(img, (640, 480))  # Ensure the annotated img is displayed
            cv2.imshow('ESP32-CAM Feed', display_img)
            if recognized_name:
                print(f"[INFO] Recognized: {recognized_name}, breaking loop")
                break
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[INFO] Stream manually stopped by user.")
                break

        except Exception as e:
            print(f"[Unexpected camera error]: {e}")
            time.sleep(0.1)  # Brief pause to prevent CPU overload

    cv2.destroyAllWindows()
    return recognized_name

def process_rfid_and_camera(uid, course_code):
    global current_uid
    current_uid = uid

    print(f"[DEBUG] Checking UID in database: {uid}")
    name_from_db = check_uid_in_database(uid)
    if not name_from_db:
        print("[INFO] UID not found in DB")
        update_lcd("Unknown", "Not authorized")
        update_status("NOT_RECOGNIZED")
        return

    print(f"[INFO] UID recognized in DB: {name_from_db}")
    update_lcd(name_from_db, "LOOK AT CAMERA!")

    # Start live stream and try to recognize face
    recognized_name = capture_and_recognize_face(timeout=10)
    print(f"[INFO] Camera detected: {recognized_name}")

    if recognized_name and recognized_name.lower() == name_from_db.lower():
        print("[INFO] Names match! Marking attendance...")
        mark_attendance(name_from_db, uid, course_code)
        update_status("PRESENT")
    else:
        print("[WARN] Names do not match or no face detected!")
        update_lcd(name_from_db, "Incomplete Auth")
        update_status("NOT_RECOGNIZED")

def attendance_loop(course_code):
    global running, latest_uid
    running = True
    print(f"[INFO] Attendance loop started for course: {course_code}")

    cv2.namedWindow('ESP32-CAM Feed', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('ESP32-CAM Feed', 640, 480)

    last_uid = None  # Track last processed UID to avoid duplicates
    while running:
        with uid_lock:
            current_uid = latest_uid
        if current_uid and current_uid != last_uid:  # Process only new UIDs
            print(f"[DEBUG] Processing UID: {current_uid}")
            process_rfid_and_camera(current_uid, course_code)
            last_uid = current_uid
            with uid_lock:
                latest_uid = None  # Clear UID after processing
        time.sleep(0.05)  # Reduced from 0.1 for faster response

        key = cv2.waitKey(10)
        if key == ord('q'):
            running = False
            break

    cv2.destroyAllWindows()
    print("[INFO] Attendance loop stopped")

# --- Routes ---
@app.route('/')
def home():
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register():
    global latest_uid
    if request.method == 'POST':
        UID = request.form.get('UID').strip()
        Name = request.form.get('Name').strip()
        Matric = request.form.get('Matric_number').strip()
        Dept = request.form.get('Department').strip()
        Level = request.form.get('Level').strip()
        webcam_data = request.form.get('webcam_image')
        if webcam_data:
            img_bytes = base64.b64decode(webcam_data.split(',')[1])
            filename = os.path.join(IMAGE_FOLDER, f"{Name}.jpg")
            with open(filename, 'wb') as f:
                f.write(img_bytes)
            # Resize the saved image
            resize_image(filename, target_size=(196, 227))  # Default size, adjustable
        photo = request.files.get('photo_file')
        if photo and photo.filename:
            filename = os.path.join(IMAGE_FOLDER, secure_filename(f"{Name}.jpg"))
            photo.save(filename)
            # Resize the saved image
            resize_image(filename, target_size=(196, 227))  # Default size, adjustable
        try:
            with get_db() as conn:
                with conn.cursor() as c:
                    c.execute("SELECT * FROM students WHERE UID=%s", (UID,))
                    if c.fetchone():
                        return render_template('index.html', error="UID already exists!", UID=UID)
                    c.execute("INSERT INTO students (UID, Name, Matric_number, Department, Level) VALUES (%s,%s,%s,%s,%s)",
                              (UID, Name, Matric, Dept, Level))
                    conn.commit()
            return render_template('index.html', success="Successfully registered!", UID=latest_uid)
        except Exception as e:
            send_email_alert("ESP32-CAM Attendance System: Registration Error", f"Registration failed: {e} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S WAT')}")
            print("[Register error]", e)
            return render_template('index.html', error="Error.", UID=latest_uid)
    return render_template('index.html', UID=latest_uid)

def resize_image(image_path, target_size=(196, 227)):
    """
    Resize an image to the specified target size and overwrite the original.
    
    Args:
        image_path (str): Path to the image file.
        target_size (tuple): Target width and height (e.g., (320, 240)).
    """
    try:
        # Read the image
        img = cv2.imread(image_path)
        if img is None:
            print(f"[ERROR] Failed to read image: {image_path}")
            return

        # Resize the image
        resized_img = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)

        # Overwrite the original image
        cv2.imwrite(image_path, resized_img)
        print(f"[INFO] Resized image saved: {image_path} to {target_size}")
    except Exception as e:
        print(f"[ERROR] Failed to resize image {image_path}: {e}")

@app.route('/get_uid')
def get_uid():
    return jsonify({"uid": latest_uid})

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u,p = request.form.get('username'), request.form.get('password')
        if u=="admin" and p=="admin123":
            session['admin']=True
            return redirect('/dashboard')
        return render_template('login.html', error="Wrong credentials")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'admin' not in session: return redirect('/login')
    return render_template('dashboard.html', tables=get_table_names(), courses=get_courses())

@app.route('/table/<table_name>')
def table(table_name):
    if 'admin' not in session: return redirect('/login')
    try:
        with get_db() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as c:
                c.execute(f"SELECT * FROM `{table_name}`")
                rows = c.fetchall()
        return render_template('table.html', table_name=table_name, rows=rows)
    except:
        return render_template('table.html', table_name=table_name, rows=[])

@app.route('/add_course', methods=['POST'])
def add_course():
    if 'admin' not in session: return redirect('/login')
    course_code = request.form.get('course_code')
    course_name = request.form.get('course_name')
    if course_code and course_name:
        try:
            with get_db() as conn:
                with conn.cursor() as c:
                    c.execute("INSERT INTO courses (Course_code, Course_name) VALUES (%s, %s)",
                              (course_code, course_name))
                    conn.commit()
        except Exception as e:
            print("[Add course error]", e)
    return redirect(f"/table/courses")

@app.route('/delete_row/<table_name>', methods=['POST'])
def delete_row(table_name):
    if 'admin' not in session: return redirect('/login')
    try:
        with get_db() as conn:
            with conn.cursor() as c:
                where = " AND ".join([f"`{k}`=%s" for k in request.form.keys()])
                vals = tuple(request.form.values())
                c.execute(f"DELETE FROM `{table_name}` WHERE {where} LIMIT 1", vals)
                conn.commit()
    except Exception as e:
        print("[Delete row error]", e)
    return redirect(f'/table/{table_name}')

@app.route('/start_attendance', methods=['POST'])
def start_attendance():
    global selected_course_code, attendance_thread, attendance_running
    if 'admin' not in session: return redirect('/login')
    course = request.form.get('course')
    if course and not attendance_running:
        selected_course_code = course
        attendance_thread = threading.Thread(target=attendance_loop, args=(course,), daemon=True)
        attendance_thread.start()
    return redirect('/processing')

@app.route('/processing')
def processing():
    if 'admin' not in session: return redirect('/login')
    return render_template('processing.html')

@app.route('/stop_attendance')
def stop_attendance():
    global attendance_running
    attendance_running = False
    print("[INFO] Attendance stopped by admin")
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/login')

if __name__=='__main__':
    app.run(debug=True, use_reloader=False)