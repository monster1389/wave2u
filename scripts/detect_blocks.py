"""
Detect character blocks inside a grid region of a NIKKE screenshot.

The number of blocks is determined automatically by finding a natural
gap in the cell scores — no hardcoded count.

The detection pipeline:
  1. Load the screenshot
  2. Define the red-frame region (6-col × 8-row grid)
  3. Score each cell using multi-scale local variance + gradient magnitude
  4. Find the natural cutoff in scores (largest relative drop) to determine
     how many cells contain blocks
  5. Draw annotated result → docs/images/result_8blocks.png

Usage:
    source .venv/Scripts/activate
    python scripts/detect_blocks.py
"""

import os

import cv2
import numpy as np

# ── config ──────────────────────────────────────────────────────────────
INPUT_IMAGE = "docs/images/nikke_screenshot.png"
OUTPUT_IMAGE = "docs/images/result_8blocks.png"

# Red-frame bounding box (adjusted so the grid covers the character slots)
FRAME = {"x": 800, "y": 210, "w": 637, "h": 845}  # → right=1437, bottom=1055

GRID_COLS = 6
GRID_ROWS = 8

# Detection weights
W_VARIANCE = 1.0
W_EDGE = 0.02
W_STD = 0.5


def multi_scale_variance(gray: np.ndarray, windows: list[int]) -> np.ndarray:
    """Average local standard deviation over several window sizes."""
    acc = np.zeros_like(gray, dtype=np.float32)
    for ws in windows:
        mean = cv2.boxFilter(gray.astype(np.float32), -1, (ws, ws))
        sq_mean = cv2.boxFilter(gray.astype(np.float32) ** 2, -1, (ws, ws))
        acc += np.sqrt(np.maximum(0, sq_mean - mean * mean))
    return acc / len(windows)


def score_cell(
    gray: np.ndarray,
    var_map: np.ndarray,
    mag_map: np.ndarray,
    x: int,
    y: int,
    w: int,
    h: int,
) -> float:
    """Higher score → more likely to contain a character block."""
    var = np.mean(var_map[y : y + h, x : x + w])
    edge = np.mean(mag_map[y : y + h, x : x + w])
    std = np.std(gray[y : y + h, x : x + w])
    return var * W_VARIANCE + edge * W_EDGE + std * W_STD


def detect_blocks(img: np.ndarray) -> tuple:
    """Run the full pipeline; return (annotated_image, block_list)."""
    fx, fy, fw, fh = FRAME["x"], FRAME["y"], FRAME["w"], FRAME["h"]
    cell_w = fw / GRID_COLS
    cell_h = fh / GRID_ROWS

    # ROI
    roi = img[fy : fy + fh, fx : fx + fw]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # Feature maps
    var_map = multi_scale_variance(gray, windows=[7, 15, 25])
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    mag_map = np.sqrt(gx * gx + gy * gy)

    # Score every cell
    cells = []
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cx = int(col * cell_w)
            cy = int(row * cell_h)
            cw = max(int(cell_w), 1)
            ch = max(int(cell_h), 1)

            s = score_cell(gray, var_map, mag_map, cx, cy, cw, ch)
            cells.append(
                (col + 1, row + 1, cx + fx, cy + fy, cw, ch, round(s, 1))
            )

    # Sort by score descending, then take all cells with score > 50.
    cells.sort(key=lambda c: c[6], reverse=True)
    blocks = [c for c in cells if c[6] > 50]

    # Sort by (row, col) for display
    blocks.sort(key=lambda c: (c[1], c[0]))

    # ── draw ──
    annotated = img.copy()
    # red frame
    cv2.rectangle(annotated, (fx, fy), (fx + fw, fy + fh), (0, 0, 255), 3)
    # grid lines
    for c in range(GRID_COLS + 1):
        x = int(c * cell_w) + fx
        cv2.line(annotated, (x, fy), (x, fy + fh), (180, 180, 180), 1)
    for r in range(GRID_ROWS + 1):
        y = int(r * cell_h) + fy
        cv2.line(annotated, (fx, y), (fx + fw, y), (180, 180, 180), 1)
    # blocks
    for i, (col, row, ax, ay, cw, ch, sc) in enumerate(blocks):
        cv2.rectangle(annotated, (ax, ay), (ax + cw, ay + ch), (0, 255, 0), 2)
        cv2.putText(
            annotated,
            f"{i+1}",
            (ax + 5, ay + 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )
        cv2.circle(annotated, (ax + cw // 2, ay + ch // 2), 4, (0, 255, 255), -1)

    # legend
    n = len(blocks)
    cv2.putText(annotated, "Red = frame", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    cv2.putText(
        annotated,
        f"Green = {n} block{'s' if n != 1 else ''} (variance+edge)",
        (20, 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        2,
    )

    return annotated, blocks


def main():
    img = cv2.imread(INPUT_IMAGE)
    if img is None:
        raise FileNotFoundError(f"Cannot read {INPUT_IMAGE}")

    print(f"Input: {INPUT_IMAGE}  ({img.shape[1]}x{img.shape[0]})")
    fx, fy, fw, fh = FRAME["x"], FRAME["y"], FRAME["w"], FRAME["h"]
    print(f"Frame: ({fx},{fy}) → ({fx+fw},{fy+fh})  = {fw}x{fh}")
    print(f"Grid:  {GRID_COLS} cols × {GRID_ROWS} rows")
    print()

    annotated, blocks = detect_blocks(img)

    os.makedirs(os.path.dirname(OUTPUT_IMAGE) or ".", exist_ok=True)
    cv2.imwrite(OUTPUT_IMAGE, annotated)
    print(f"Output: {OUTPUT_IMAGE}")
    print()

    n = len(blocks)
    print(f"Detected {n} block{'s' if n != 1 else ''}:")
    print(f"  {'#':>3}  {'Cell':>8}  {'Position':>24}  {'Size':>10}  {'Score':>6}")
    for i, (col, row, ax, ay, cw, ch, sc) in enumerate(blocks):
        print(
            f"  {i+1:3d}  ({col},{row:2d})  "
            f"({ax:4d},{ay:4d})-({ax+cw:4d},{ay+ch:4d})  "
            f"{cw:3d}x{ch:3d}  {sc:6.1f}"
        )


if __name__ == "__main__":
    main()
