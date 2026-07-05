"""
Capture a full-screen screenshot (the NIKKE window should be visible).

This avoids all window-detection and DPI-scaling pitfalls — no need to find
the NIKKE window by title, no coordinate mismatches.  Just make sure the
NIKKE window is on screen before the countdown ends.

Usage:
    source .venv/Scripts/activate
    python scripts/screenshot_nikke.py
"""

import os
import sys
import time

import cv2
import numpy as np
import pyautogui

OUTPUT_DIR = "docs/images"
OUTPUT_FILENAME = "nikke_screenshot.png"


def capture_full_screen():
    """Capture the entire primary monitor and return a BGR numpy array."""
    print("Waiting 5 seconds — make sure the NIKKE window is visible on screen ...")
    for i in range(5, 0, -1):
        print(f"  {i} ...")
        time.sleep(1)

    print("Capturing full screen ...")
    screenshot = pyautogui.screenshot()  # full screen, no region
    frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    return frame


def main():
    frame = capture_full_screen()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    cv2.imwrite(out_path, frame)

    h, w = frame.shape[:2]
    print(f"Screenshot saved to {out_path}")
    print(f"Dimensions: {w}x{h}")


if __name__ == "__main__":
    main()
