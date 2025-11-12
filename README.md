IoT Dashboard for Autonomous Vehicle -

This project is a web-based dashboard for monitoring and testing the autonomous vehicle system.
It allows users to visualize live map data, monitor coordinates, and eventually integrate with the vehicle’s video feed systems.

How to Run the IoT Dashboard GUI -
1. Install Python :
Make sure Python 3.x is installed. 

2. Install Required Libraries :
Open a terminal or command prompt and run:
pip install pyqt5 pyqtwebengine opencv-python folium

Note: PyQt5 is for the GUI, PyQtWebEngine is for displaying the map, opencv-python is for the camera feed, and folium is for the GPS map.

3. Clone the Repository :

git clone <your-repo-url>

cd <your-repo-folder>

4. Run the GUI :
python main_gui.py

The main window will open showing:
Main page – Dashboard welcome screen
Map page – GPS location on a map
Camera Feed page – Live webcam feed (replace with your Pi camera URL if needed)

5. Notes
Make sure your webcam is connected for the video feed.
The GPS map uses static coordinates by default; you can update self.latitude and self.longitude in GPSWidget for your location.

