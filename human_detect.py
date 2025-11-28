from ultralytics import YOLO
import cv2

model_path = r"c:\IoT_Software\yolo11n.pt" 
model = YOLO(model_path)

# Initializing computer's webcam (index 0)
cap = cv2.VideoCapture(0)

print("Starting webcam... Press 'q' to quit.")

while True:
    # Read a frame from the webcam
    ret, frame = cap.read()
    if not ret:
        break

    # Running the model on the frame, looking only for class '0' (person)
    results = model.predict(frame, conf=0.5, classes=[0], verbose=False)
    # ----------------------------------------

    # Drawing the bounding boxes and labels onto the frame
    annotated_frame = results[0].plot()

    # Displaying the resulting frame in a window
    cv2.imshow("YOLO Human Detection Test", annotated_frame)

    # Exit the loop when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Releasing the webcam and closing all windows
cap.release()
cv2.destroyAllWindows()