"""发射点检测模块

利用游戏自带的淡青色轨迹线定位发射点。
"""

from typing import Optional, Tuple
import cv2
import numpy as np

from src.config import FX, FY, FW, FH

# 轨迹线颜色 — 淡青色 HSV 范围
LINE_COLOUR_LOWER = np.array([85, 15, 180])
LINE_COLOUR_UPPER = np.array([105, 100, 255])

# 已知锚点
START_PT = (893, 1054)
TARGET_PT = (1333, 467)


def _make_line_mask(img: np.ndarray) -> np.ndarray:
    """创建轨迹线 HSV 掩码"""
    roi = img[FY:FY + FH, FX:FX + FW]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LINE_COLOUR_LOWER, LINE_COLOUR_UPPER)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return mask


def detect_launch_point(img: np.ndarray) -> Optional[Tuple[int, int]]:
    """
    检测小球发射点。

    通过找到游戏自带的轨迹线，取其底部端点作为发射点。

    Args:
        img: BGR 截图

    Returns:
        (x, y) 发射点坐标，或 None（未检测到）
    """
    mask = _make_line_mask(img)

    lines = cv2.HoughLinesP(
        mask, rho=1, theta=np.pi / 360,
        threshold=30, minLineLength=40, maxLineGap=50,
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

        # 方向对齐
        dot = (dx * target_dx + dy * target_dy) / (length * target_len)
        angle_score = max(0, dot)

        # 接近锚点
        d_s = abs((y2 - y1) * (sx - FX - x1) - (x2 - x1) * (sy - FY - y1)) / length
        d_t = abs((y2 - y1) * (tx - FX - x1) - (x2 - x1) * (ty - FY - y1)) / length
        proximity = max(0, 1 - (d_s + d_t) / 200)

        score = angle_score * 0.4 + proximity * 0.6
        if score > best_score:
            best_score = score
            best_line = (x1 + FX, y1 + FY, x2 + FX, y2 + FY)

    if best_line is None:
        return None

    x1, y1, x2, y2 = best_line
    # 返回底部端点（y 较大的点）
    pt = (x1, y1) if y1 > y2 else (x2, y2)
    return (int(pt[0]), int(pt[1]))
