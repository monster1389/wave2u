"""方块检测模块

从 scripts/detect_blocks.py 提取核心逻辑，
输入截图 → 输出方块列表。
"""

from typing import List
import cv2
import numpy as np

from src.config import FX, FY, FW, FH, GRID_COLS, GRID_ROWS

# 检测权重（与 detect_blocks.py 一致）
W_VARIANCE = 1.0
W_EDGE = 0.02
W_STD = 0.5
SCORE_THRESHOLD = 50

Block = dict  # {col, row, x, y, w, h}


def multi_scale_variance(gray: np.ndarray, windows: list[int]) -> np.ndarray:
    """多窗口局部标准差"""
    acc = np.zeros_like(gray, dtype=np.float32)
    for ws in windows:
        mean = cv2.boxFilter(gray.astype(np.float32), -1, (ws, ws))
        sq_mean = cv2.boxFilter(gray.astype(np.float32) ** 2, -1, (ws, ws))
        acc += np.sqrt(np.maximum(0, sq_mean - mean * mean))
    return acc / len(windows)


def score_cell(gray, var_map, mag_map, x, y, w, h) -> float:
    """单元格评分（分数越高越可能有方块）"""
    var = np.mean(var_map[y:y + h, x:x + w])
    edge = np.mean(mag_map[y:y + h, x:x + w])
    std = np.std(gray[y:y + h, x:x + w])
    return var * W_VARIANCE + edge * W_EDGE + std * W_STD


def detect_blocks(img: np.ndarray) -> List[Block]:
    """
    检测网格中的方块。

    Args:
        img: BGR 截图（numpy 数组）

    Returns:
        方块列表 [{col, row, x, y, w, h}, ...]
        按 (row, col) 排序
    """
    roi = img[FY:FY + FH, FX:FX + FW]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    var_map = multi_scale_variance(gray, [7, 15, 25])
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    mag_map = np.sqrt(gx * gx + gy * gy)

    cell_w = FW / GRID_COLS
    cell_h = FH / GRID_ROWS

    cells = []
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cx = int(col * cell_w)
            cy = int(row * cell_h)
            cw = max(int(cell_w), 1)
            ch = max(int(cell_h), 1)
            s = score_cell(gray, var_map, mag_map, cx, cy, cw, ch)
            cells.append({
                "col": col + 1,
                "row": row + 1,
                "x": cx + FX,
                "y": cy + FY,
                "w": cw,
                "h": ch,
                "score": round(s, 1),
            })

    blocks = [c for c in cells if c["score"] > SCORE_THRESHOLD]
    blocks.sort(key=lambda b: (b["row"], b["col"]))
    return blocks
