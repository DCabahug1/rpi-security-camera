# Import the YOLO class from the Ultralytics package.
from ultralytics import YOLO
import cv2  # Import OpenCV so we can read frames from the webcam.
import threading
import numpy as np
import os
import time
import uuid
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

_supabase_url = os.environ.get("SUPABASE_URL")
_supabase_key = os.environ.get("SUPABASE_PUBLISHABLE_KEY")
supabase: Client | None
if _supabase_url and _supabase_key:
    supabase = create_client(_supabase_url, _supabase_key)
else:
    supabase = None

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

    upload_video("output.mp4")

    saving_in_progress = False
    person_detected_recently = False


def upload_video(file_path: str) -> None:
    """Upload a local file to Supabase Storage (bucket from SUPABASE_STORAGE_BUCKET)."""
    if supabase is None:
        print("Supabase client not configured (set SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY).")
        return
    bucket = os.environ.get("SUPABASE_STORAGE_BUCKET")
    if not bucket:
        print("SUPABASE_STORAGE_BUCKET not set; skip upload.")
        return
    if not os.path.isfile(file_path):
        print(f"Upload skipped; missing file: {file_path}")
        return
    remote_path = f"clips/{uuid.uuid4().hex}.mp4"
    try:
        with open(file_path, "rb") as f:
            supabase.storage.from_(bucket).upload(
                remote_path,
                f,
                file_options={"content-type": "video/mp4"},
            )
        video_url = supabase.storage.from_(bucket).get_public_url(remote_path)
        supabase.table("recordings").insert({"video_url": video_url}).execute()
        print(f"Uploaded video to {bucket}/{remote_path}; saved recording row.")
    except Exception as exc:
        print(f"Upload failed: {exc}")


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
