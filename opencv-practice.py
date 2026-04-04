# Import the YOLO class from the Ultralytics package.
from ultralytics import YOLO
import cv2  # Import OpenCV so we can read frames from the webcam.
import threading
import numpy as np

model = YOLO("yolov8n.pt")  # Load the pretrained YOLO nano model.

cap = cv2.VideoCapture(0)  # Open the default webcam.

cv2.namedWindow("YOLO Webcam", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("YOLO Webcam", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

CLIP_FRAMES = 150  # 5 s at 30 fps

recording_buffer: list[np.ndarray] = []
saving_in_progress: bool = False
person_detected_recently: bool = False
save_thread: threading.Thread | None = None


def save_and_upload_video(frames: list[np.ndarray], width: int, height: int) -> None:
    global saving_in_progress
    global person_detected_recently

    fps = 30.0
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter("output.mp4", fourcc, fps, (width, height))

    for frame in frames:
        out.write(frame)

    out.release()

    saving_in_progress = False
    person_detected_recently = False


while True:  # Keep reading frames until we quit.
    ret, frame = cap.read()  # Read one frame from the webcam.

    if not ret:  # Stop if the camera failed to provide a frame.
        print("Failed to grab frame")
        break

    results = model(frame, imgsz=160, verbose=False)

    detected_frame = results[0].plot()

    for cls in results[0].boxes.cls:
        if int(cls) == 0 and not person_detected_recently and not saving_in_progress:
            person_detected_recently = True

    if person_detected_recently and len(recording_buffer) < CLIP_FRAMES and not saving_in_progress:
        recording_buffer.append(frame)

    if len(recording_buffer) >= CLIP_FRAMES and not saving_in_progress:
        batch = recording_buffer
        recording_buffer = []
        h, w = frame.shape[:2]
        saving_in_progress = True
        save_thread = threading.Thread(
            target=save_and_upload_video, args=(batch, w, h)
        )
        save_thread.start()

    if saving_in_progress:
        status = "SAVING..."
    elif person_detected_recently and len(recording_buffer) < CLIP_FRAMES:
        status = f"RECORDING {len(recording_buffer)}/{CLIP_FRAMES}"
    else:
        status = ""

    if status:
        cv2.putText(
            detected_frame,
            status,
            (24, 48),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )

    cv2.imshow("YOLO Webcam", detected_frame)

    key = cv2.waitKey(1) & 0xFF  # Check whether a key was pressed.
    if key == ord("q"):  # Quit when q is pressed.
        break

if save_thread is not None:
    save_thread.join()

cap.release()  # Release the webcam.
cv2.destroyAllWindows()  # Close all OpenCV windows.
