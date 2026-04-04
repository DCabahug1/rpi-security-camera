# Import the YOLO class from the Ultralytics package.
from ultralytics import YOLO
import cv2  # Import OpenCV so we can read frames from the webcam.

model = YOLO("yolov8n.pt")  # Load the pretrained YOLOv8 nano model.

cap = cv2.VideoCapture(0)  # Open the default webcam.

cv2.namedWindow("YOLO Webcam", cv2.WINDOW_NORMAL)
cv2.setWindowProperty(
    "YOLO Webcam", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

counter = 0
boxes = None

while True:  # Keep reading frames until we quit.
    ret, frame = cap.read()  # Read one frame from the webcam.

    if not ret:  # Stop if the camera failed to provide a frame.
        print("Failed to grab frame")
        break

    if counter == 10:
        result = model(frame)[0]

        boxes = result.boxes
        counter = 0

    if boxes is not None:
        for i in range(len(boxes)):
            x1, y1, x2, y2 = boxes.xyxy[i].tolist()
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            cls_id = int(boxes.cls[i])
            cls_name = model.names[cls_id]

            confidence = float(boxes.conf[i])
            confidence = f"{confidence:.2f}"

            cv2.putText(frame, f"{cls_name} {confidence}", (x1, y1),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

    counter += 1

    cv2.imshow("YOLO Webcam", frame)

    key = cv2.waitKey(1) & 0xFF  # Check whether a key was pressed.
    if key == ord("q"):  # Quit when q is pressed.
        break

cap.release()  # Release the webcam.
cv2.destroyAllWindows()  # Close all OpenCV windows.
