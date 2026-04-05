"""Encode clips for the web and upload to Supabase (Storage + recordings row)."""

import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from collections.abc import Callable

import cv2
import numpy as np

from security_camera import config

logger = logging.getLogger(__name__)

FINAL_VIDEO_PATH = "output.mp4"
CLIP_FRAMES = 150
FPS = 30.0


def encode_for_web(input_path: str, output_path: str) -> None:
    if not shutil.which("ffmpeg"):
        raise FileNotFoundError("ffmpeg not on PATH")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-movflags",
            "+faststart",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-an",
            output_path,
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def upload_clip(file_path: str, bucket: str) -> None:
    sb = config.supabase
    if not sb:
        return
    remote_path = f"clips/{uuid.uuid4().hex}.mp4"
    with open(file_path, "rb") as f:
        sb.storage.from_(bucket).upload(
            remote_path,
            f,
            file_options={"content-type": "video/mp4"},
        )
    video_url = sb.storage.from_(bucket).get_public_url(remote_path)
    sb.table("recordings").insert({"video_url": video_url}).execute()


def save_and_upload_video(
    frames: list[np.ndarray],
    width: int,
    height: int,
    *,
    on_complete: Callable[[], None],
) -> None:
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fd, raw_path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)
    try:
        out = cv2.VideoWriter(raw_path, fourcc, FPS, (width, height))
        for frame in frames:
            out.write(frame)
        out.release()

        try:
            encode_for_web(raw_path, FINAL_VIDEO_PATH)
        except (FileNotFoundError, subprocess.CalledProcessError):
            shutil.copyfile(raw_path, FINAL_VIDEO_PATH)

        bucket = os.environ.get("SUPABASE_STORAGE_BUCKET")
        if bucket and os.path.isfile(FINAL_VIDEO_PATH):
            try:
                upload_clip(FINAL_VIDEO_PATH, bucket)
            except Exception:
                logger.exception("Upload failed")
    finally:
        try:
            os.unlink(raw_path)
        except OSError:
            pass
        on_complete()
