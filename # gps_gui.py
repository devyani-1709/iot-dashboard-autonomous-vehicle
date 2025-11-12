import sys
import cv2
import folium
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame
)
from PyQt5.QtCore import QTimer, Qt, QUrl
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView  # for showing map


# ------------------ VIDEO FEED WIDGET ------------------
class VideoFeedWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.label = QLabel("Starting Video Feed...")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Webcam feed (replace '0' with Pi camera stream URL later)
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
            scaled = qimg.scaled(900, 600, Qt.KeepAspectRatio)
            self.label.setPixmap(QPixmap.fromImage(scaled))

    def closeEvent(self, event):
        self.cap.release()


# ------------------ GPS MAP WIDGET ------------------
class GPSWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.map_view = QWebEngineView()
        self.coord_label = QLabel("")
        self.coord_label.setAlignment(Qt.AlignRight)
        self.coord_label.setStyleSheet("color: white; padding: 8px;")
        self.coord_label.setFont(QFont("Arial", 10, QFont.Bold))

        # 📍 Location: BITS Pilani Hyderabad Campus
        self.latitude, self.longitude = 17.5456, 78.5718
        gps_map = folium.Map(location=[self.latitude, self.longitude], zoom_start=16)
        folium.Marker(
            [self.latitude, self.longitude],
            tooltip="BITS Pilani Hyderabad Campus",
            popup="Rover Location"
        ).add_to(gps_map)
        gps_map.save("gps_map.html")

        self.map_view.setUrl(QUrl.fromLocalFile(f"{sys.path[0]}/gps_map.html"))

        layout.addWidget(self.map_view)
        layout.addWidget(self.coord_label)
        self.setLayout(layout)
        self.update_coords()

    def update_coords(self):
        self.coord_label.setText(
            f"Latitude: {self.latitude:.4f},  Longitude: {self.longitude:.4f}"
        )


# ------------------ MAIN WINDOW ------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IoT Dashboard for Autonomous Vehicle")
        self.setGeometry(100, 100, 1200, 700)

        # Main layout
        main_layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # --- Title Bar ---
        title_bar = QLabel("IoT Dashboard for Autonomous Vehicle")
        title_bar.setAlignment(Qt.AlignCenter)
        title_bar.setFont(QFont("Arial", 14, QFont.Bold))
        title_bar.setStyleSheet("background-color: #002b45; color: white; padding: 10px;")
        main_layout.addWidget(title_bar)

        # --- Sidebar + Main Area ---
        body_layout = QHBoxLayout()
        main_layout.addLayout(body_layout)

        # Sidebar
        sidebar = QFrame()
        sidebar.setStyleSheet("background-color: #003f63; border-right: 2px solid #001f33;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignTop)

        button_names = ["Main", "Map", "Camera Feed"]
        self.buttons = []

        for name in button_names:
            btn = QPushButton(name)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #005b8f;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    margin: 6px;
                    padding: 8px;
                }
                QPushButton:hover { background-color: #0077b6; }
                QPushButton:checked { background-color: #00b4d8; }
            """)
            btn.setCheckable(True)
            sidebar_layout.addWidget(btn)
            self.buttons.append(btn)
        sidebar_layout.addStretch()
        body_layout.addWidget(sidebar, 1)

        # Stacked pages
        self.stack = QStackedWidget()
        self.main_widget = QLabel("Welcome to the IoT Dashboard")
        self.main_widget.setAlignment(Qt.AlignCenter)
        self.main_widget.setStyleSheet("color: white; font-size: 16px;")
        self.gps_widget = GPSWidget()
        self.video_widget = VideoFeedWidget()

        self.stack.addWidget(self.main_widget)
        self.stack.addWidget(self.gps_widget)
        self.stack.addWidget(self.video_widget)
        self.stack.setStyleSheet("background-color: #001f33;")
        body_layout.addWidget(self.stack, 4)

        # Connect buttons
        for i, btn in enumerate(self.buttons):
            btn.clicked.connect(lambda checked, index=i: self.switch_page(index))

        self.buttons[0].setChecked(True)

    def switch_page(self, index):
        for b in self.buttons:
            b.setChecked(False)
        self.buttons[index].setChecked(True)
        self.stack.setCurrentIndex(index)


# ------------------ RUN APP ------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

