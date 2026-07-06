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
                  ) -> List[Block]:
    if prev_img is None or prev_blocks is None or force_full:
        return _full_detect(img, prev_blocks)
    return _diff_update(img, prev_img, prev_blocks)


def _full_detect(img: np.ndarray,
                 prev_blocks: Optional[List[Block]] = None
                 ) -> List[Block]:
    """多尺度方差 + Sobel 梯度 + 灰度标准差，带滞后滤波"""
    roi = img[FY:FY + FH, FX:FX + FW]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    var_map = multi_scale_variance(gray, [7, 15, 25])
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    mag_map = np.sqrt(gx * gx + gy * gy)

    cell_w = FW / GRID_COLS
    cell_h = FH / GRID_ROWS

    # 当前帧的原始检测
    raw_blocks = []
    raw_empty = []
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cx = int(col * cell_w); cy = int(row * cell_h)
            cw = max(int(cell_w), 1); ch = max(int(cell_h), 1)
            var = np.mean(var_map[cy:cy + ch, cx:cx + cw])
            edge = np.mean(mag_map[cy:cy + ch, cx:cx + cw])
            std = np.std(gray[cy:cy + ch, cx:cx + cw])
            score = var * 1.0 + edge * 0.02 + std * 0.5
            detected = score > 40

            cell = {"col": col + 1, "row": row + 1,
                    "x": cx + FX, "y": cy + FY,
                    "w": cw, "h": ch, "score": round(score, 1)}
            if detected:
                raw_blocks.append(cell)
            else:
                raw_empty.append(cell)

    # 滞后滤波：没有 prev_blocks 时直接用原始检测
    if prev_blocks is None:
        raw_blocks.sort(key=lambda b: (b["row"], b["col"]))
        return raw_blocks

    # 有 prev_blocks 时：当前有方块 → 保留；当前无方块 → 延迟 3 帧才移除
    prev_set = {(b["col"], b["row"]) for b in prev_blocks}
    raw_set = {(b["col"], b["row"]) for b in raw_blocks}

    # 初始化持久计数器（存储在函数属性中）
    if not hasattr(_full_detect, "_persist"):
        _full_detect._persist = {}

    persist = _full_detect._persist
    result = []

    for blk in prev_blocks:
        key = (blk["col"], blk["row"])
        if key in raw_set:
            # 连续检测到 → 保留
            persist[key] = 0
            result.append(blk)
        else:
            # 当前帧没检测到 → 计数器+1
            persist[key] = persist.get(key, 0) + 1
            if persist[key] < 3:  # 连续 3 帧没检测到才移除
                result.append(blk)
            else:
                persist.pop(key, None)

    result.sort(key=lambda b: (b["row"], b["col"]))
    return result


def multi_scale_variance(gray: np.ndarray, windows: list[int]) -> np.ndarray:
    acc = np.zeros_like(gray, dtype=np.float32)
    for ws in windows:
        mean = cv2.boxFilter(gray.astype(np.float32), -1, (ws, ws))
        sq_mean = cv2.boxFilter(gray.astype(np.float32) ** 2, -1, (ws, ws))
        acc += np.sqrt(np.maximum(0, sq_mean - mean * mean))
    return acc / len(windows)


def _diff_update(img: np.ndarray, prev_img: np.ndarray,
                 prev_blocks: List[Block]) -> List[Block]:
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
