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
    """用格子四周的边缘检测方块：方块有清晰边框，空格没有"""
    roi = img[FY:FY + FH, FX:FX + FW]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # 全局 Canny 边缘检测
    edges = cv2.Canny(gray, 30, 100)

    cell_w = FW / GRID_COLS
    cell_h = FH / GRID_ROWS
    BORDER_INNER = 4    # 边框内缘（px，从格子边缘向内）
    BORDER_OUTER = 16   # 边框外缘

    cells = []
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cx = int(col * cell_w)
            cy = int(row * cell_h)
            cw = max(int(cell_w), 1)
            ch = max(int(cell_h), 1)

            cell_edges = edges[cy:cy + ch, cx:cx + cw]

            # 创建边框环形掩码（格子内侧 BORDER_INNER 到 BORDER_OUTER 像素的环）
            border_mask = np.zeros((ch, cw), dtype=np.uint8)
            cv2.rectangle(border_mask,
                          (BORDER_INNER, BORDER_INNER),
                          (cw - BORDER_INNER - 1, ch - BORDER_INNER - 1), 255, -1)
            cv2.rectangle(border_mask,
                          (BORDER_OUTER, BORDER_OUTER),
                          (cw - BORDER_OUTER - 1, ch - BORDER_OUTER - 1), 0, -1)

            # 环内的边缘像素
            ring_edges = cv2.bitwise_and(cell_edges, cell_edges, mask=border_mask)
            ring_edge_count = cv2.countNonZero(ring_edges)
            ring_area = cv2.countNonZero(border_mask)
            edge_ratio = ring_edge_count / ring_area if ring_area > 0 else 0

            score = round(edge_ratio * 1000, 1)  # 放大分数

            cells.append({
                "col": col + 1,
                "row": row + 1,
                "x": cx + FX,
                "y": cy + FY,
                "w": cw,
                "h": ch,
                "score": score,
            })

    # 自适应阈值：找显著断层
    scores = sorted([c["score"] for c in cells], reverse=True)
    max_drop = 0
    threshold = 10.0
    for i in range(1, len(scores)):
        drop = scores[i - 1] - scores[i]
        if drop > max_drop:
            max_drop = drop
            threshold = (scores[i - 1] + scores[i]) / 2
    if max_drop < 3:
        threshold = 10.0

    blocks = [c for c in cells if c["score"] > threshold]
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
