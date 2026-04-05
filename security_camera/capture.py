"""Webcam loop: YOLO person detection, buffer 150 frames, save/upload in a worker thread."""

import logging
import threading

import cv2
import numpy as np
from ultralytics import YOLO

from security_camera import pipeline

logger = logging.getLogger(__name__)

CLIP_FRAMES = pipeline.CLIP_FRAMES
WINDOW_NAME = "YOLO Webcam"


def run() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    model = YOLO("yolov8n.pt")
    cap = cv2.VideoCapture(0)
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    recording_buffer: list[np.ndarray] = []
    saving_in_progress = False
    person_detected_recently = False
    save_thread: threading.Thread | None = None

    def after_save() -> None:
        nonlocal saving_in_progress, person_detected_recently
        saving_in_progress = False
        person_detected_recently = False

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Camera read failed")
                break

            results = model(frame, imgsz=160, verbose=False)
            detected_frame = results[0].plot()

            for cls in results[0].boxes.cls:
                if int(cls) == 0 and not person_detected_recently and not saving_in_progress:
                    person_detected_recently = True

            if (
                person_detected_recently
                and len(recording_buffer) < CLIP_FRAMES
                and not saving_in_progress
            ):
                recording_buffer.append(frame)

            if len(recording_buffer) >= CLIP_FRAMES and not saving_in_progress:
                batch = recording_buffer
                recording_buffer = []
                h, w = frame.shape[:2]
                saving_in_progress = True

                def work() -> None:
                    pipeline.save_and_upload_video(
                        batch, w, h, on_complete=after_save
                    )

                save_thread = threading.Thread(target=work)
                save_thread.start()

            if saving_in_progress:
                status = "SAVING..."
            elif person_detected_recently and len(recording_buffer) < CLIP_FRAMES:
                status = f"RECORDING {len(recording_buffer)}/{CLIP_FRAMES} FRAMES"
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

            cv2.imshow(WINDOW_NAME, detected_frame)
            if (cv2.waitKey(1) & 0xFF) == ord("q"):
                break
    finally:
        if save_thread is not None:
            save_thread.join()
        cap.release()
        cv2.destroyAllWindows()
