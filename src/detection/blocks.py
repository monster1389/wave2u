"""方块检测模块

全量法 + 帧差消除法。

首次检测：用边框边缘法找出初始方块。
增量更新：用帧差法检测方块消除（变化 > 30% 且非轨迹线干扰）。
"""

from typing import List, Optional
import cv2
import numpy as np

from src.config import FX, FY, FW, FH, GRID_COLS, GRID_ROWS

Block = dict  # {col, row, x, y, w, h}

# 帧差消除阈值
REMOVE_CHANGE_RATIO = 0.30   # 格子 30% 以上像素变化 → 可能被消除
CELL_CHANGE_THRESHOLD = 30


def detect_blocks(img: np.ndarray,
                  prev_img: Optional[np.ndarray] = None,
                  prev_blocks: Optional[List[Block]] = None,
                  force_full: bool = False,
                  traj_line: Optional[tuple] = None,
                  ) -> List[Block]:
    """
    Args:
        traj_line: (lx, ly, dx, dy) 当前轨迹线，用于排除干扰
    """
    if prev_img is None or prev_blocks is None or force_full:
        return _full_detect(img)
    return _diff_update(img, prev_img, prev_blocks, traj_line)


def _full_detect(img: np.ndarray) -> List[Block]:
    """边框边缘法检测初始方块"""
    roi = img[FY:FY + FH, FX:FX + FW]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 30, 100)

    cell_w = FW / GRID_COLS
    cell_h = FH / GRID_ROWS
    BORDER_INNER, BORDER_OUTER = 3, 20

    cells = []
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cx = int(col * cell_w); cy = int(row * cell_h)
            cw = max(int(cell_w), 1); ch = max(int(cell_h), 1)
            cell_edges = edges[cy:cy + ch, cx:cx + cw]

            # 边框环形掩码
            mask = np.zeros((ch, cw), dtype=np.uint8)
            cv2.rectangle(mask, (BORDER_INNER, BORDER_INNER),
                          (cw - BORDER_INNER - 1, ch - BORDER_INNER - 1), 255, -1)
            cv2.rectangle(mask, (BORDER_OUTER, BORDER_OUTER),
                          (cw - BORDER_OUTER - 1, ch - BORDER_OUTER - 1), 0, -1)

            ring = cv2.bitwise_and(cell_edges, cell_edges, mask=mask)
            ring_area = cv2.countNonZero(mask)
            edge_ratio = cv2.countNonZero(ring) / ring_area if ring_area > 0 else 0
            score = round(edge_ratio * 1000, 1)

            cells.append({"col": col + 1, "row": row + 1,
                          "x": cx + FX, "y": cy + FY,
                          "w": cw, "h": ch, "score": score})

    # 自适应阈值
    scores = sorted([c["score"] for c in cells], reverse=True)
    max_drop, threshold = 0, 4.0
    for i in range(1, len(scores)):
        drop = scores[i - 1] - scores[i]
        if drop > max_drop:
            max_drop, threshold = drop, (scores[i - 1] + scores[i]) / 2
    if max_drop < 1:
        threshold = 4.0

    blocks = [c for c in cells if c["score"] > threshold]
    blocks.sort(key=lambda b: (b["row"], b["col"]))
    return blocks


def _diff_update(img: np.ndarray, prev_img: np.ndarray,
                 prev_blocks: List[Block],
                 traj_line: Optional[tuple] = None) -> List[Block]:
    """帧差法检测方块消除"""
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
        cw, ch = max(int(cell_w), 1), max(int(cell_h), 1)

        cell_motion = motion[cy:cy + ch, cx:cx + cw]
        change_ratio = cv2.countNonZero(cell_motion) / (cw * ch) if cw * ch > 0 else 0

        # 只有变化超过 30% 才判定为消除
        if change_ratio < REMOVE_CHANGE_RATIO:
            updated.append(blk)

    return updated
