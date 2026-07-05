"""方块检测模块

Otsu 二值化法：方块有角色图像（前景），空格只有背景。
Otsu 自适应阈值分离前景/背景，方块的前景比例在合理范围内。
"""

from typing import List, Optional
import cv2
import numpy as np

from src.config import FX, FY, FW, FH, GRID_COLS, GRID_ROWS

Block = dict  # {col, row, x, y, w, h}

CELL_CHANGE_THRESHOLD = 30
CELL_CHANGE_RATIO = 0.15


def detect_blocks(img: np.ndarray,
                  prev_img: Optional[np.ndarray] = None,
                  prev_blocks: Optional[List[Block]] = None,
                  force_full: bool = False
                  ) -> List[Block]:
    if prev_img is None or prev_blocks is None or force_full:
        return _full_detect(img)
    return _diff_update(img, prev_img, prev_blocks)


def _full_detect(img: np.ndarray) -> List[Block]:
    """Otsu 二值化：方块有前景内容，空格只有背景"""
    roi = img[FY:FY + FH, FX:FX + FW]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    cell_w = FW / GRID_COLS
    cell_h = FH / GRID_ROWS

    cells = []
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cx = int(col * cell_w)
            cy = int(row * cell_h)
            cw = max(int(cell_w), 1)
            ch = max(int(cell_h), 1)

            cell_gray = gray[cy:cy + ch, cx:cx + cw]

            # Otsu 自适应二值化
            _, thresh = cv2.threshold(cell_gray, 0, 255,
                                      cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # 去除小连通域（网格线、噪声）
            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
                thresh, 8, cv2.CV_32S)
            clean = np.zeros_like(thresh)
            fg_px = 0
            for i in range(1, num_labels):
                area = stats[i, cv2.CC_STAT_AREA]
                if area >= 60:  # 面积≥60像素才算
                    clean[labels == i] = 255
                    fg_px += area

            ratio = fg_px / (cw * ch) * 100

            cells.append({
                "col": col + 1,
                "row": row + 1,
                "x": cx + FX,
                "y": cy + FY,
                "w": cw,
                "h": ch,
                "score": round(ratio, 1),
            })

    # 方块的前景比例在 15%-80% 之间（角色覆盖部分格子）
    # 空格要么几乎全黑（<5%），要么几乎全白（>90%）
    blocks = [c for c in cells if 15 < c["score"] < 80]
    blocks.sort(key=lambda b: (b["row"], b["col"]))
    return blocks


def _diff_update(img: np.ndarray, prev_img: np.ndarray,
                 prev_blocks: List[Block]) -> List[Block]:
    roi_curr = img[FY:FY + FH, FX:FX + FW]
    roi_prev = prev_img[FY:FY + FH, FX:FX + FW]

    diff = cv2.absdiff(roi_curr, roi_prev)
    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, motion = cv2.threshold(gray_diff, CELL_CHANGE_THRESHOLD, 255, cv2.THRESH_BINARY)

    cell_w = FW / GRID_COLS
    cell_h = FH / GRID_ROWS
    updated = []

    for blk in prev_blocks:
        cx = int((blk["col"] - 1) * cell_w)
        cy = int((blk["row"] - 1) * cell_h)
        cw = max(int(cell_w), 1)
        ch = max(int(cell_h), 1)

        cell_motion = motion[cy:cy + ch, cx:cx + cw]
        changed_px = cv2.countNonZero(cell_motion)
        change_ratio = changed_px / (cw * ch) if cw * ch > 0 else 0

        if change_ratio < CELL_CHANGE_RATIO:
            updated.append(blk)

    return updated
