"""方块检测模块

颜色法检测：方块是高饱和度青色，背景/空格是低饱和度。
不依赖纹理/边缘，只依赖颜色饱和度差异。
"""

from typing import List, Optional
import cv2
import numpy as np

from src.config import FX, FY, FW, FH, GRID_COLS, GRID_ROWS

Block = dict  # {col, row, x, y, w, h}

# 每格像素变化阈值
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
    """用颜色方差检测方块：方块有多个颜色（角色头像），空格颜色单一"""
    roi = img[FY:FY + FH, FX:FX + FW]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    cell_w = FW / GRID_COLS
    cell_h = FH / GRID_ROWS

    cells = []
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cx = int(col * cell_w)
            cy = int(row * cell_h)
            cw = max(int(cell_w), 1)
            ch = max(int(cell_h), 1)

            cell_hsv = hsv[cy:cy + ch, cx:cx + cw]

            # 颜色方差：方块有多个颜色 → 高方差
            h_std = float(np.std(cell_hsv[:, :, 0]))
            s_std = float(np.std(cell_hsv[:, :, 1]))
            v_std = float(np.std(cell_hsv[:, :, 2]))
            # 综合评分：H 方差权重最高（颜色多样性）
            score = h_std * 2.0 + s_std * 0.5 + v_std * 0.3

            cells.append({
                "col": col + 1,
                "row": row + 1,
                "x": cx + FX,
                "y": cy + FY,
                "w": cw,
                "h": ch,
                "score": round(score, 1),
            })

    # 自适应阈值：找分数断层
    scores = sorted([c["score"] for c in cells], reverse=True)
    max_drop = 0
    threshold = 12.0
    for i in range(1, len(scores)):
        drop = scores[i - 1] - scores[i]
        if drop > max_drop:
            max_drop = drop
            threshold = (scores[i - 1] + scores[i]) / 2
    if max_drop < 3:
        threshold = 12.0  # 没有显著断层时用默认值

    blocks = [c for c in cells if c["score"] > threshold]
    blocks.sort(key=lambda b: (b["row"], b["col"]))
    return blocks


def _diff_update(img: np.ndarray, prev_img: np.ndarray,
                 prev_blocks: List[Block]) -> List[Block]:
    """帧差法更新方块状态"""
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
