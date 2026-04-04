# Import the YOLO class from the Ultralytics package.
from ultralytics import YOLO
import cv2  # Import OpenCV so we can read frames from the webcam.

model = YOLO("yolov8n.pt")  # Load the pretrained YOLOv8 nano model.

cap = cv2.VideoCapture(0)  # Open the default webcam.

cv2.namedWindow("YOLO Webcam", cv2.WINDOW_NORMAL)
cv2.setWindowProperty(
    "YOLO Webcam", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

while True:  # Keep reading frames until we quit.
    ret, frame = cap.read()  # Read one frame from the webcam.

    if not ret:  # Stop if the camera failed to provide a frame.
        print("Failed to grab frame")
        break

    # results = model(frame, imgsz=320)
    results = model(frame, imgsz=160)

    frame = results[0].plot()

    cv2.imshow("YOLO Webcam", frame)

    key = cv2.waitKey(1) & 0xFF  # Check whether a key was pressed.
    if key == ord("q"):  # Quit when q is pressed.
        break

cap.release()  # Release the webcam.
cv2.destroyAllWindows()  # Close all OpenCV windows.
