# Raspberry Pi security camera (YOLO + Supabase)

Practice project: run **YOLOv8** on a webcam feed, **record short clips** when a **person** is detected, **encode** them for the web with **FFmpeg**, and **upload** to **Supabase Storage** with a row in **Postgres** (`recordings`).

### Layout

| Path | Role |
|------|------|
| `run_camera.py` | Start the webcam app. |
| `security_camera/config.py` | Loads `.env`, builds the Supabase client. |
| `security_camera/pipeline.py` | OpenCV write → FFmpeg (H.264 + faststart) → Storage + `recordings` insert. |
| `security_camera/capture.py` | Main loop: YOLO, buffer, overlay, worker thread. |
| `examples/thread_queue.py` | Small producer/consumer queue demo. |

## What you need

- **Python 3.11+** (3.11 or 3.12 work well on a Pi; very new versions may lack wheels for some ML packages.)
- **Webcam** (USB camera as `/dev/video0` is typical) or a device OpenCV can open with `VideoCapture(0)`.
- **FFmpeg** on `PATH` (required for browser-friendly H.264 + faststart; without it, the app falls back to uploading the raw OpenCV file.)
- A **[Supabase](https://supabase.com)** project if you want uploads + database rows.

## Raspberry Pi setup

These steps assume **Raspberry Pi OS** (Debian-based) on a Pi with network access. Adjust if you use another OS.

### 1. System packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ffmpeg git
```

- **ffmpeg** — re-encodes clips so they play in browsers (`<video>`) and stream without a full download.
- **git** — clone this repo (or copy files over another way).

Optional: if OpenCV fails to open the camera, install V4L utilities and check the device:

```bash
sudo apt install -y v4l-utils
v4l2-ctl --list-devices
```

### 2. Python virtual environment

Using a venv avoids touching system Python packages.

```bash
cd /path/to/rpi-security-camera
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Note:** Installing **PyTorch** + **Ultralytics** on a Pi can take a long time and is heavy for the CPU. For a lighter device, consider a smaller workflow (e.g. skip torch in requirements and run only non-ML scripts), or run inference on a more powerful machine. For a typical Pi 4/5, `yolov8n` is the smallest reasonable default in this repo.

### 3. First run of the model

The first time you run the main script, **YOLO** may download **`yolov8n.pt`** into the project directory. Ensure the Pi has internet for that run, or copy the weights file manually.

### 4. Display (OpenCV window)

The capture app uses **`cv2.imshow`** fullscreen. You need a **desktop session** (monitor or VNC) and `DISPLAY` set, or adapt the script for headless use (e.g. remove `imshow` / use a virtual display). SSH without X forwarding will not show a window.

### 5. Environment variables

Copy `.env` from your secrets workflow (do **not** commit real keys). Create a file named **`.env`** in the project root with:

| Variable | Purpose |
|----------|---------|
| `SUPABASE_URL` | Project URL (Supabase **Settings → API**). |
| `SUPABASE_PUBLISHABLE_KEY` | Publishable / `anon` key for client-style access. |
| `SUPABASE_STORAGE_BUCKET` | Storage **bucket name** (create under **Storage** in the dashboard). |

### 6. Supabase dashboard

1. **Storage** — Create the bucket whose name matches `SUPABASE_STORAGE_BUCKET`. Add policies so your key can **upload** (and optionally **read**) objects; for public playback URLs, the bucket is often **public** or you use **signed URLs** instead of `get_public_url`.
2. **SQL** — Create the `recordings` table (see your schema) and **RLS** policies so **`anon`** can **`insert`** (and **`select`** if needed), or use the **service role** only on a trusted server.

Example policies depend on your security model; start from the [Supabase Flask quickstart](https://supabase.com/docs/guides/getting-started/quickstarts/flask) and [Storage docs](https://supabase.com/docs/guides/storage).

## Run

```bash
source .venv/bin/activate
python run_camera.py
```

Alternatively: `python -m security_camera.capture`

- Press **`q`** to quit.
- Each trigger records **150 frames** at **30 FPS** (~**5 seconds**), writes **`output.mp4`**, uploads to `clips/<uuid>.mp4`, and inserts **`recordings`** with **`video_url`**.

## Troubleshooting

| Issue | Suggestions |
|-------|-------------|
| Video plays after download but not in the browser | Ensure **FFmpeg** ran successfully (H.264 + `faststart`). Check bucket is **public** or use **signed URLs** for private buckets. |
| `pip install` fails building native wheels | Use **Python 3.11/3.12**, install build deps (`build-essential`, `python3-dev`), or accept prebuilt wheels from **piwheels** where available. |
| Camera open fails | Check permissions, cable, and index `0` vs `1` in `VideoCapture(0)`. |
| Slow inference | Lower `imgsz` in `model(...)`, use `yolov8n`, reduce resolution, or run on better hardware. |

## License

MIT — see [`LICENSE`](LICENSE).
