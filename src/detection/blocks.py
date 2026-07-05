"""方块检测模块

首次检测用全 CV（基准），之后用帧差法只检测变化。
静态元素完全稳定，只在方块被消除时才更新。
"""

from typing import List, Optional
import cv2
import numpy as np

from src.config import FX, FY, FW, FH, GRID_COLS, GRID_ROWS

# CV 检测权重（首次基准用）
W_VARIANCE = 1.0
W_EDGE = 0.02
W_STD = 0.5
SCORE_THRESHOLD = 50

Block = dict  # {col, row, x, y, w, h}

# 每格像素变化阈值
CELL_CHANGE_THRESHOLD = 30   # 像素值变化 > 此值才算变化
CELL_CHANGE_RATIO = 0.15     # 格子中至少 15% 的像素变化了才算被消除


def detect_blocks(img: np.ndarray,
                  prev_img: Optional[np.ndarray] = None,
                  prev_blocks: Optional[List[Block]] = None,
                  force_full: bool = False
                  ) -> List[Block]:
    """
    检测方块。

    Args:
        img: 当前帧 BGR 截图
        prev_img: 上一帧截图（帧差用），None = 首次检测
        prev_blocks: 上次检测的方块列表（增量更新用）
        force_full: 强制全 CV 检测

    Returns:
        方块列表 [{col, row, x, y, w, h}, ...]
    """
    # 首次检测或强制全检测
    if prev_img is None or prev_blocks is None or force_full:
        return _full_detect(img)

    # 帧差法增量更新
    return _diff_update(img, prev_img, prev_blocks)


def _full_detect(img: np.ndarray) -> List[Block]:
    """全 CV 检测（与原有逻辑一致）"""
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
    # 如果硬阈值没找到方块，尝试自适应阈值找分数断层
    if len(blocks) == 0:
        scores = sorted([c["score"] for c in cells], reverse=True)
        # 找最大分数下降点
        max_drop = 0
        best_thresh = SCORE_THRESHOLD
        for i in range(1, len(scores)):
            drop = scores[i-1] - scores[i]
            if drop > max_drop:
                max_drop = drop
                best_thresh = (scores[i-1] + scores[i]) / 2
        if max_drop > 5:  # 有显著断层
            blocks = [c for c in cells if c["score"] > best_thresh]
    blocks.sort(key=lambda b: (b["row"], b["col"]))
    return blocks


def _diff_update(img: np.ndarray, prev_img: np.ndarray,
                 prev_blocks: List[Block]) -> List[Block]:
    """帧差法更新方块状态"""
    roi_curr = img[FY:FY + FH, FX:FX + FW]
    roi_prev = prev_img[FY:FY + FH, FX:FX + FW]

    # 帧差
    diff = cv2.absdiff(roi_curr, roi_prev)
    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, motion = cv2.threshold(gray_diff, CELL_CHANGE_THRESHOLD, 255, cv2.THRESH_BINARY)

    cell_w = FW / GRID_COLS
    cell_h = FH / GRID_ROWS
    updated = []

    for blk in prev_blocks:
        # 计算该格子区域在帧差图中的变化比例
        cx = int((blk["col"] - 1) * cell_w)
        cy = int((blk["row"] - 1) * cell_h)
        cw = max(int(cell_w), 1)
        ch = max(int(cell_h), 1)

        cell_motion = motion[cy:cy + ch, cx:cx + cw]
        changed_px = cv2.countNonZero(cell_motion)
        total_px = cw * ch
        change_ratio = changed_px / total_px if total_px > 0 else 0

        if change_ratio < CELL_CHANGE_RATIO:
            # 变化不显著 → 方块还在
            updated.append(blk)
        # 变化显著 → 方块被消除 → 不加入列表

    return updated


def multi_scale_variance(gray: np.ndarray, windows: list[int]) -> np.ndarray:
    """多窗口局部标准差"""
    acc = np.zeros_like(gray, dtype=np.float32)
    for ws in windows:
        mean = cv2.boxFilter(gray.astype(np.float32), -1, (ws, ws))
        sq_mean = cv2.boxFilter(gray.astype(np.float32) ** 2, -1, (ws, ws))
        acc += np.sqrt(np.maximum(0, sq_mean - mean * mean))
    return acc / len(windows)


def score_cell(gray, var_map, mag_map, x, y, w, h) -> float:
    """单元格评分"""
    var = np.mean(var_map[y:y + h, x:x + w])
    edge = np.mean(mag_map[y:y + h, x:x + w])
    std = np.std(gray[y:y + h, x:x + w])
    return var * W_VARIANCE + edge * W_EDGE + std * W_STD
