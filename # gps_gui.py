import sys
import cv2
import folium
import json
import os
import threading
import shutil
import time

from flask import Flask, request 
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QSizePolicy
)
from PyQt5.QtCore import QTimer, Qt, QUrl
from PyQt5.QtGui import QImage, QPixmap, QFont, QPainter  # <--- Added QPainter
from PyQt5.QtWebEngineWidgets import QWebEngineView

# ==========================================
# PART 1: FLASK SERVER (Background Thread)
# ==========================================

DATA_LOCK = threading.Lock() 

LATEST_DATA = {
    "lat": 17.5456,  # Default BITS Hyd
    "lon": 78.5718,
    "image_updated": False
}

flask_app = Flask(__name__)
UPLOAD_FOLDER = "received_images"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@flask_app.route('/upload_image', methods=['POST'])
def upload_image():
    global LATEST_DATA
    try:
        with DATA_LOCK:
            # 1. Update GPS Data
            lat = request.form.get('latitude')
            lon = request.form.get('longitude')
            
            if lat and lon:
                LATEST_DATA["lat"] = float(lat)
                LATEST_DATA["lon"] = float(lon)
                print(f"[DATA] GPS Received: {lat}, {lon}")

            # 2. Save Image Safely
            if 'image' in request.files:
                file = request.files['image']
                
                temp_path = os.path.join(UPLOAD_FOLDER, "temp_detected.jpg")
                final_path = os.path.join(UPLOAD_FOLDER, "detected.jpg")
                
                file.save(temp_path)
                
                try:
                    # Small delay to let GUI release the file
                    time.sleep(0.05) 
                    if os.path.exists(final_path):
                        os.remove(final_path)
                    os.rename(temp_path, final_path)
                    
                    LATEST_DATA["image_updated"] = True
                    print("[IMAGE] New detection saved.")
                except PermissionError:
                    print("[WARNING] File locked by GUI. Skipping.")
                except Exception as e:
                    print(f"Image Save Error: {e}")
                
        return "Success", 200
            
    except Exception as e:
        print(f"[ERROR] Server Exception: {e}")
        return str(e), 200

def run_flask_server():
    flask_app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)


# ==========================================
# PART 2: PyQt5 GUI
# ==========================================

# ------------------ VIDEO FEED WIDGET ------------------
class VideoFeedWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.label = QLabel("Webcam Feed (Local)")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: white;")
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            qimg = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
            scaled = qimg.scaled(640, 480, Qt.KeepAspectRatio)
            self.label.setPixmap(QPixmap.fromImage(scaled))

    def closeEvent(self, event):
        if self.cap.isOpened():
            self.cap.release()
        super().closeEvent(event)


# ------------------ GPS MAP WIDGET (FIXED) ------------------
# ------------------ GPS MAP WIDGET (WITH MARKER HISTORY) ------------------
class GPSWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.map_view = QWebEngineView()
        self.coord_label = QLabel("Waiting for GPS...")
        self.coord_label.setAlignment(Qt.AlignRight)
        self.coord_label.setStyleSheet("color: white; padding: 8px; font-weight: bold;")

        # Store the current location
        self.latitude = LATEST_DATA["lat"]
        self.longitude = LATEST_DATA["lon"]

        # LIST TO STORE ALL PAST DETECTION POINTS
        self.detection_history = [] 

        self.generate_map()

        layout.addWidget(self.map_view)
        layout.addWidget(self.coord_label)
        self.setLayout(layout)

    def generate_map(self):
        # Create map centered on the LATEST detection
        gps_map = folium.Map(location=[self.latitude, self.longitude], zoom_start=16)
        
        # 1. Loop through history and plot PAST detections (Blue)
        for coord in self.detection_history:
            folium.Marker(
                location=coord,
                tooltip="Human Detected",
                icon=folium.Icon(color="blue", icon="user", prefix='fa') # Blue 'User' Icon
            ).add_to(gps_map)

        # 2. Plot the LATEST detection (Red)
        folium.Marker(
            [self.latitude, self.longitude],
            tooltip="LATEST DETECTION",
            icon=folium.Icon(color="red", icon="warning-sign") # Red 'Warning' Icon
        ).add_to(gps_map)

        # Inject HTML directly
        data = gps_map.get_root().render()
        self.map_view.setHtml(data)

    def update_coords(self, lat, lon):
        # Check if the location has changed significantly (approx 11 meters)
        # This prevents stacking 100 markers on the exact same spot if the car is stopped
        if abs(self.latitude - lat) > 0.0001 or abs(self.longitude - lon) > 0.0001:
            
            # Add the OLD location to history before updating
            # We only add to history if we are moving to a NEW spot
            self.detection_history.append([self.latitude, self.longitude])
            
            # Update to new location
            self.latitude = lat
            self.longitude = lon
            
            self.coord_label.setText(f"Lat: {lat:.5f} | Lon: {lon:.5f}")
            self.generate_map()
            
        elif self.coord_label.text() == "Waiting for GPS...":
             # First update ever
             self.latitude = lat
             self.longitude = lon
             self.coord_label.setText(f"Lat: {lat:.5f} | Lon: {lon:.5f}")
             self.generate_map()


# ------------------ DETECTIONS WIDGET (FULL SCREEN) ------------------
# ------------------ CUSTOM IMAGE LABEL ------------------
# This custom class handles drawing the image safely without resizing loops
class ScalableImageLabel(QLabel):
    def __init__(self):
        super().__init__()
        # Important: This tells the layout "I don't care about size, just give me whatever space you have"
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.current_pixmap = None

    def set_image(self, pixmap):
        self.current_pixmap = pixmap
        self.update() # Trigger a safe repaint

    def paintEvent(self, event):
        if self.current_pixmap:
            painter = QPainter(self)
            # Scale the image to fit the current widget size, keeping aspect ratio
            # This happens purely visually, so it doesn't trigger a layout resize loop
            scaled_pix = self.current_pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            
            # Center the image in the black box
            x = (self.width() - scaled_pix.width()) // 2
            y = (self.height() - scaled_pix.height()) // 2
            painter.drawPixmap(x, y, scaled_pix)
        else:
            super().paintEvent(event)


# ------------------ DETECTIONS WIDGET (FIXED) ------------------
class DetectionsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Monitoring for Human Detection...")
        self.status_label.setStyleSheet("color: #00b4d8; font-size: 16px; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setMaximumHeight(50)
        layout.addWidget(self.status_label)

        # Use our new Custom Label instead of a standard QLabel
        self.image_label = ScalableImageLabel()
        self.image_label.setStyleSheet("border: 2px solid #005b8f; background-color: #000;")
        layout.addWidget(self.image_label)

        self.setLayout(layout)

    def update_image(self):
        with DATA_LOCK:
            if LATEST_DATA["image_updated"]:
                img_path = os.path.join("received_images", "detected.jpg")
                if os.path.exists(img_path):
                    # Load the image
                    pix = QPixmap(img_path)
                    
                    # Update our custom label
                    self.image_label.set_image(pix)
                    
                    self.status_label.setText(f"Human Detected! (Updated)")
                    LATEST_DATA["image_updated"] = False


# ------------------ MAIN WINDOW ------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IoT Dashboard - Autonomous Vehicle")
        self.setGeometry(100, 100, 1100, 700)

        main_layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        container.setStyleSheet("background-color: #001f33;") 

        title = QLabel("Autonomous Surveillance Dashboard")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("background-color: #002b45; color: white; padding: 15px;")
        main_layout.addWidget(title)

        body_layout = QHBoxLayout()
        main_layout.addLayout(body_layout)

        sidebar = QFrame()
        sidebar.setStyleSheet("background-color: #003f63;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignTop)

        self.buttons = []
        names = ["Live Detections", "GPS Map", "Local Camera"]
        
        for i, name in enumerate(names):
            btn = QPushButton(name)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #005b8f; color: white; border-radius: 5px; padding: 10px; font-size: 12px;
                }
                QPushButton:checked { background-color: #00b4d8; font-weight: bold; }
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda c, idx=i: self.switch_page(idx))
            sidebar_layout.addWidget(btn)
            self.buttons.append(btn)

        sidebar_layout.addStretch()
        body_layout.addWidget(sidebar, 1)

        self.stack = QStackedWidget()
        self.detect_widget = DetectionsWidget()
        self.gps_widget = GPSWidget()
        self.video_widget = VideoFeedWidget()

        self.stack.addWidget(self.detect_widget)
        self.stack.addWidget(self.gps_widget)
        self.stack.addWidget(self.video_widget)

        body_layout.addWidget(self.stack, 4)
        self.buttons[0].setChecked(True)

        self.system_timer = QTimer()
        self.system_timer.timeout.connect(self.sync_data)
        self.system_timer.start(500) 

    def switch_page(self, index):
        for btn in self.buttons:
            btn.setChecked(False)
        self.buttons[index].setChecked(True)
        self.stack.setCurrentIndex(index)

    def sync_data(self):
        current_lat, current_lon = 0, 0
        
        with DATA_LOCK:
            current_lat = LATEST_DATA["lat"]
            current_lon = LATEST_DATA["lon"]

        self.gps_widget.update_coords(current_lat, current_lon)
        self.detect_widget.update_image()


# ------------------ RUN APP ------------------
if __name__ == "__main__":
    server_thread = threading.Thread(target=run_flask_server)
    server_thread.daemon = True 
    server_thread.start()
    print(f" Server Thread Started. Listening on 0.0.0.0:5001")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
