#!/bin/bash
cd /home/dcabahug1/Github/rpi-security-camera || exit 1
source .venv/bin/activate
python -m pip install -r requirements.txt
python opencv-practice.py