# wave2u — NIKKE game automation / CV exploration

Python-based computer-vision project for automating analysis of the mobile game
Goddess of Victory: NIKKE.  Currently in exploration phase — no app skeleton yet.

## Project

- **Stack:** Python 3.12, OpenCV (`cv2`), `pyautogui`, `pygetwindow`, `numpy`, `Pillow`
- **Entry scripts:** `scripts/screenshot_nikke.py`, `scripts/detect_blocks.py`,
  `scripts/find_yellow_annotation.py`
- **Venv:** `.venv/` (activate with `source .venv/Scripts/activate`)

## Commands

```bash
source .venv/Scripts/activate
pip install -r requirements.txt   # install deps
python scripts/screenshot_nikke.py      # capture nikke screenshot
python scripts/detect_blocks.py         # detect blocks in 6x8 grid
python scripts/find_yellow_annotation.py  # find trajectory line + impact circle
```

No build / test / lint commands yet (project is pre-initialisation).

## Architecture

```
scripts/
  screenshot_nikke.py         — full-screen capture with 5s countdown
  detect_blocks.py            — 6×8 grid block detection (score > 50)
  find_yellow_annotation.py   — trajectory line + impact circle detection
docs/images/                  — screenshots and annotated results
```

Three standalone scripts that form a pipeline: capture → detect blocks → find
trajectory.  All CV logic lives in the scripts; no shared library yet.

## Conventions

- **Imports:** `cv2`, `numpy as np`, `pyautogui` — standard OpenCV stack.
- **Coordinate system:** OpenCV BGR (not RGB).  HSV for colour-based masking.
- **Grid:** 6 cols × 8 rows, defined by `FX=800, FY=210, FW=637, FH=845`.
- **Block detection:** Multi-scale local variance + Sobel gradient + gray std,
  thresholded at score > 50.
- **Line detection:** `HoughLinesP` with direction + proximity scoring against
  known anchor points.
- **Circle detection:** `HoughCircles` with colour (pale cyan/yellow) + position
  scoring.
- **Config constants** live at the top of each script in a `# ── config ──` section.
- **No tests yet** — scripts are run manually and verified against annotated
  output images in `docs/images/result_*.png`.

## Notes

- `.superpowers/` and `docs/superpowers/` directories contain brainstorming
  drafts and visual companion files — **do NOT commit them** to git.
- Brainstorming / spec docs are written in Chinese.
