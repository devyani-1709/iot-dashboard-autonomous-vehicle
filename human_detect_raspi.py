from ultralytics import YOLO
import cv2
from picamera2 import Picamera2  # Import PiCamera library
import time
import random                     # For fake GPS data


model_path = "yolo11n.pt"  # Assumes "yolo11n.pt" is in the same folder
model = YOLO(model_path)

# --- INITIALIZE PICAMERA ---
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (320, 240), "format": "RGB888"})
picam2.configure(config)
picam2.start()
time.sleep(1)  # Give the camera time to warm up
print("Starting PiCamera (320x240, 3-channel)... Press 'q' to quit.")
while True:
    # --- FAKE GPS DATA ---
    # In a real system, you would read this from your GPS module
    fake_lat = 12.9716 + (random.random() - 0.5) * 0.001
    fake_lon = 77.5946 + (random.random() - 0.5) * 0.001
    # ---------------------

    # Read a frame from the PiCamera. This frame is a 3-channel RGB numpy array.
    frame = picam2.capture_array()

    # --- THIS IS THE HUMAN DETECTION PART ---
    # Run the model on the frame, looking only for class '0' (person)
    # The 'frame' is already in the correct RGB format.
    results = model.predict(frame, conf=0.5, classes=[0], verbose=False)
    # ----------------------------------------

    # --- CHECK FOR DETECTIONS & LOG GPS ---
    if results[0].boxes:  # Check if any 'person' was detected
        # This is where you would fuse GPS data and send an MQTT packet
        print(f"PERSON DETECTED at [Lat: {fake_lat:.6f}, Lon: {fake_lon:.6f}]")
    # --------------------------------------

    # Draw the bounding boxes and labels onto the frame
    # results[0].plot() returns an RGB image with annotations
    annotated_frame_rgb = results[0].plot()

    # Convert the RGB frame to BGR for OpenCV's 'imshow'
    # cv2.imshow() expects BGR format, not RGB.
    annotated_frame_bgr = cv2.cvtColor(annotated_frame_rgb, cv2.COLOR_RGB2BGR)

    # --- Display the resulting frame ---
    # NOTE: This window will only appear if you are on the
    # Raspberry Pi's desktop (e.g., VNC or with a monitor).
    cv2.imshow("YOLO Human Detection (Pi)", annotated_frame_bgr)

    # Exit the loop when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close all windows
picam2.stop()
cv2.destroyAllWindows()
print("Script finished.")