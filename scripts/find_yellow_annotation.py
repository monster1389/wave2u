"""
NIKKE breakout trajectory analysis.

In the game a ball travels along a slanted trajectory line (pale cyan) and
hits a block.  A bright-yellow circle marks the predicted impact position.

This script finds:
  1. The trajectory line inside the 6×8 grid
  2. The first block the line hits (traced from bottom upward)
  3. The bright-yellow circle at the impact point

Usage:
    source .venv/Scripts/activate
    python scripts/find_yellow_annotation.py
"""

import os
import sys

import cv2
import numpy as np

# Ensure we can import sibling modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── config ──────────────────────────────────────────────────────────────

INPUT_IMAGE = "docs/images/nikke_screenshot.png"
OUTPUT_IMAGE = "docs/images/result_yellow_annotation.png"

# Grid frame (same as detect_blocks.py)
FX, FY, FW, FH = 800, 210, 637, 845
GRID_COLS, GRID_ROWS = 6, 8

# Trajectory line colour — pale cyan, roughly RGB(205, 243, 247)
LINE_COLOUR = {"lower": np.array([85, 15, 180]), "upper": np.array([105, 100, 255])}

# Impact circle colour — bright yellow
# Impact circle colour — very pale yellow, roughly RGB(253, 254, 231)
# HSV(31, 23, 254) — low saturation, bright
CIRCLE_COLOUR = {"lower": np.array([20, 0, 200]), "upper": np.array([45, 80, 255])}

# Expected trajectory anchors
START_PT = (893, 1054)   # bottom of grid
TARGET_PT = (1333, 467)  # inside cell (6, 3)


# ── grid helpers ────────────────────────────────────────────────────────

def cell_bbox(col, row):
    """Return (x, y, w, h) for grid cell (col, row), 1-based."""
    cell_w = FW / GRID_COLS
    cell_h = FH / GRID_ROWS
    return (
        FX + int((col - 1) * cell_w),
        FY + int((row - 1) * cell_h),
        max(int(cell_w), 1),
        max(int(cell_h), 1),
    )


def point_to_cell(px, py):
    """Return (col, row) of the cell containing (px, py), or None."""
    if not (FX <= px < FX + FW and FY <= py < FY + FH):
        return None
    cell_w = FW / GRID_COLS
    cell_h = FH / GRID_ROWS
    col = int((px - FX) / cell_w) + 1
    row = int((py - FY) / cell_h) + 1
    return (min(col, GRID_COLS), min(row, GRID_ROWS))


# ── colour masks ────────────────────────────────────────────────────────

def make_mask(img, lower, upper):
    """Return HSV mask for the given range, restricted to the grid area."""
    roi = img[FY:FY + FH, FX:FX + FW]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return mask


# ── 1. trajectory line ─────────────────────────────────────────────────

def find_trajectory_line(img):
    """Find the slanted trajectory line.  Returns (x1,y1,x2,y2) endpoints."""
    mask = make_mask(img, LINE_COLOUR["lower"], LINE_COLOUR["upper"])

    lines = cv2.HoughLinesP(
        mask, rho=1, theta=np.pi / 360,
        threshold=30, minLineLength=40, maxLineGap=50
    )
    if lines is None:
        return None

    sx, sy = START_PT
    tx, ty = TARGET_PT
    target_dx, target_dy = tx - sx, ty - sy
    target_len = np.sqrt(target_dx ** 2 + target_dy ** 2)

    best_line, best_score = None, -1
    for l in lines:
        x1, y1, x2, y2 = l
        dx, dy = x2 - x1, y2 - y1
        length = np.sqrt(dx * dx + dy * dy)
        if length < 20:
            continue

        # Direction alignment
        dot = (dx * target_dx + dy * target_dy) / (length * target_len)
        angle_score = max(0, dot)

        # Proximity to start / target
        d_s = abs((y2 - y1) * (sx - FX - x1) - (x2 - x1) * (sy - FY - y1)) / length
        d_t = abs((y2 - y1) * (tx - FX - x1) - (x2 - x1) * (ty - FY - y1)) / length
        proximity = max(0, 1 - (d_s + d_t) / 200)

        score = angle_score * 0.4 + proximity * 0.6
        if score > best_score:
            best_score = score
            best_line = (x1 + FX, y1 + FY, x2 + FX, y2 + FY)

    return best_line


def line_y_at(x1, y1, x2, y2, test_y):
    """Return the x coordinate on the line at a given y, or None."""
    dy = y2 - y1
    if dy == 0:
        return None
    t = (test_y - y1) / dy
    x = x1 + t * (x2 - x1)
    return x


# ── 2. first intersected block (trace from bottom) ─────────────────────

def first_hit_cell(x1, y1, x2, y2, blocks):
    """
    Walk the extended trajectory line from grid bottom upward and return
    the (col, row) of the first *existing* block the ball hits.
    Only cells with a detected block (score > 50) count.
    """
    if x1 is None or not blocks:
        return None

    dy = y2 - y1
    if dy == 0:
        return None

    # Line parameters: x = a*y + b
    a = (x2 - x1) / dy
    b = x1 - a * y1

    # Walk from grid bottom upward
    cell_h = FH / GRID_ROWS
    step = cell_h / 4

    for test_y in np.arange(FY + FH, FY, -step):
        x_on = a * test_y + b
        if not (FX <= x_on <= FX + FW):
            continue
        cell = point_to_cell(x_on, test_y)
        if cell is None:
            continue
        # Check if this cell has a block
        for blk in blocks:
            if blk[0] == cell[0] and blk[1] == cell[1]:
                return cell  # first existing block along the path

    return None


# ── 3. bright-yellow impact circle ──────────────────────────────────────

def find_impact_circle(img, line_endpoint, hit_cell):
    """
    Find the pale-cyan impact circle using Hough circle detection.
    The circle marks where the ball hits the block — located at the
    uppermost point of the trajectory line (the line endpoint).
    """
    if line_endpoint is None or hit_cell is None:
        return None

    lx, ly = line_endpoint
    cx_c, cy_c, cw, ch = cell_bbox(*hit_cell)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    circles = cv2.HoughCircles(
        gray, cv2.HOUGH_GRADIENT, dp=1.0, minDist=8,
        param1=15, param2=5, minRadius=8, maxRadius=30
    )

    if circles is None:
        return None

    circles = np.round(circles[0, :]).astype(int)

    best, best_score = None, -1
    for (x, y, r) in circles:
        if r < 12 or r > 26:
            continue

        # Must be near the hit cell area
        if not (cx_c - 100 <= x <= cx_c + cw + 100 and
                cy_c - 100 <= y <= cy_c + ch + 100):
            continue

        # Colour: pale cyan/teal (H 70-100, low S) OR pale yellow (H 20-45, low S)
        h_v = int(hsv[y, x, 0])
        s_v = int(hsv[y, x, 1])
        is_pale_cyan = 70 <= h_v <= 100 and s_v < 70
        is_pale_yellow = 20 <= h_v <= 45 and s_v < 70
        if not (is_pale_cyan or is_pale_yellow):
            continue

        # Score: close to line endpoint, moderate radius, good colour
        dist_to_end = np.sqrt((x - lx) ** 2 + (y - ly) ** 2)
        r_score = 1.0 - abs(r - 19) / 12  # peak at r=19
        colour_score = 1.0 if is_pale_cyan else 0.5

        score = (1 / (dist_to_end + 3)) * 0.4 + r_score * 0.3 + colour_score * 0.3

        if score > best_score:
            best_score = score
            best = ((x, y), r)

    return best


# ── main ────────────────────────────────────────────────────────────────


def main():
    img = cv2.imread(INPUT_IMAGE)
    if img is None:
        raise FileNotFoundError(f"Cannot read {INPUT_IMAGE}")

    h, w = img.shape[:2]
    print(f"Input: {INPUT_IMAGE}  ({w}x{h})")
    print(f"Grid: ({FX},{FY}) → ({FX+FW},{FY+FH}) = {FW}x{FH}, {GRID_COLS}×{GRID_ROWS}")

    # ── 1. trajectory line ──
    line = find_trajectory_line(img)
    if line:
        x1, y1, x2, y2 = line
        print(f"\n[Line] ({x1},{y1}) → ({x2},{y2})")

        # Extend to grid edges
        dy = y2 - y1
        if dy != 0:
            for test_y in (FY + FH, FY):
                x_on = line_y_at(x1, y1, x2, y2, test_y)
                if x_on is not None and FX <= x_on <= FX + FW:
                    print(f"  Extends to y={test_y}: x≈{x_on:.0f}")
                    break
    else:
        print("\n[Line] Not found")

    # ── 2. detect existing blocks ──
    # Inline block detection (score > 50)
    from detect_blocks import multi_scale_variance, score_cell
    roi = img[FY:FY + FH, FX:FX + FW]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    var_map = multi_scale_variance(gray, [7, 15, 25])
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    mag = np.sqrt(gx * gx + gy * gy)
    cell_w = FW / GRID_COLS
    cell_h = FH / GRID_ROWS
    all_cells = []
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cx, cy = int(col * cell_w), int(row * cell_h)
            cw, ch = max(int(cell_w), 1), max(int(cell_h), 1)
            s = score_cell(gray, var_map, mag, cx, cy, cw, ch)
            all_cells.append((col + 1, row + 1, cx + FX, cy + FY, cw, ch, round(s, 1)))
    blocks = [c for c in all_cells if c[6] > 50]
    blocks.sort(key=lambda b: (b[1], b[0]))
    if blocks:
        print(f"\n[Blocks] {len(blocks)} found:")
        for b in blocks:
            print(f"  ({b[0]},{b[1]}) score={b[6]}")
    else:
        print("\n[Blocks] None detected")

    # ── 3. first hit cell ──
    hit_cell = first_hit_cell(*line, blocks) if line else None
    if hit_cell:
        print(f"[Hit block] ({hit_cell[0]},{hit_cell[1]})")
    else:
        print("[Hit block] No intersection")

    # ── 3. impact circle ──
    # Line endpoint (topmost point = impact location)
    line_end = None
    if line:
        x1, y1, x2, y2 = line
        line_end = (x2, y2) if y2 < y1 else (x1, y1)

    circle = find_impact_circle(img, line_end, hit_cell)
    if circle:
        (cx, cy), radius = circle
        print(f"[Circle] center=({cx},{cy}) radius={radius}")
    else:
        print("[Circle] Not found")

    # ── draw ──
    annotated = img.copy()
    cv2.rectangle(annotated, (FX, FY), (FX + FW, FY + FH), (0, 0, 255), 2)

    if line:
        x1, y1, x2, y2 = line
        cv2.line(annotated, (x1, y1), (x2, y2), (0, 255, 255), 3)

    if hit_cell:
        hx, hy, hw, hh = cell_bbox(*hit_cell)
        cv2.rectangle(annotated, (hx, hy), (hx + hw, hy + hh), (0, 255, 0), 3)
        cv2.putText(annotated, f"HIT ({hit_cell[0]},{hit_cell[1]})",
                    (hx + 5, hy + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    if circle:
        (cx, cy), radius = circle
        cv2.circle(annotated, (cx, cy), radius, (0, 255, 255), 2)
        cv2.circle(annotated, (cx, cy), 4, (0, 255, 255), -1)
        cv2.putText(annotated, "IMPACT", (cx - 30, cy - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

    os.makedirs(os.path.dirname(OUTPUT_IMAGE) or ".", exist_ok=True)
    cv2.imwrite(OUTPUT_IMAGE, annotated)
    print(f"\nSaved: {OUTPUT_IMAGE}")


if __name__ == "__main__":
    main()
