"""发射点检测模块

混合检测：HSV 颜色定位 + 膨胀连接断线 + 几何评分。
先用颜色筛选出可能是轨迹线的区域，再找线条。
"""

from typing import Optional, Tuple
import cv2
import numpy as np

from src.config import FX, FY, FW, FH

# 轨迹线颜色 — 淡青色 HSV 范围（放宽，配合膨胀使用）
LINE_HUE_LOWER = 70
LINE_HUE_UPPER = 130
LINE_SAT_LOWER = 5
LINE_SAT_UPPER = 180
LINE_VAL_LOWER = 100


def detect_trajectory(img: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    result = _find_best_line(img)
    if result is None:
        return None

    x1, y1, x2, y2 = result
    if y1 > y2:
        lx, ly, tx, ty = x1, y1, x2, y2
    else:
        lx, ly, tx, ty = x2, y2, x1, y1

    dx = tx - lx
    dy = ty - ly
    return (int(lx), int(ly), int(dx), int(dy))


def detect_launch_point(img: np.ndarray) -> Optional[Tuple[int, int]]:
    traj = detect_trajectory(img)
    if traj is None:
        return None
    return (traj[0], traj[1])


def _find_best_line(img: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    roi = img[FY:FY + FH, FX:FX + FW]

    # 1. HSV 颜色掩码：定位淡青色轨迹线
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv,
                       np.array([LINE_HUE_LOWER, LINE_SAT_LOWER, LINE_VAL_LOWER]),
                       np.array([LINE_HUE_UPPER, LINE_SAT_UPPER, 255]))

    # 2. 形态学闭运算：填虚线缺口，不膨胀整体
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    # 3. 统计颜色像素量
    color_px = cv2.countNonZero(mask)
    if color_px < 200:
        return None

    # 4. HoughLinesP 在颜色掩码上找线
    lines = cv2.HoughLinesP(
        mask, rho=1, theta=np.pi / 360,
        threshold=50, minLineLength=40, maxLineGap=30,
    )
    if lines is None:
        return None

    # lines 可能是 (N,4) 或 (N,1,4) 格式
    if len(lines.shape) == 3:
        lines = lines[:, 0, :]  # (N,1,4) → (N,4)

    # 5. 几何评分
    MIN_SCORE = 0.3
    best_line, best_score = None, -1

    for l in lines:
        x1, y1, x2, y2 = l
        length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        if length < 40:
            continue

        dx_f = x2 - x1

        # 排除水平/垂直线
        horiz = abs(dx_f / max(length, 1))
        if horiz > 0.95 or horiz < 0.08:
            continue

        max_y = max(y1, y2)
        min_y = min(y1, y2)

        # 至少一端在网格下半部
        if max_y < FH * 0.3:
            continue

        # 向上至少 50px
        if (max_y - min_y) < 50:
            continue

        # 评分
        length_score = min(length / 300, 1.0)
        bottom_score = max_y / FH
        upward_score = min((max_y - min_y) / 200, 1.0)
        score = length_score * 0.35 + bottom_score * 0.35 + upward_score * 0.3

        if score > best_score:
            best_score = score
            best_line = (int(x1 + FX), int(y1 + FY), int(x2 + FX), int(y2 + FY))

    if best_score < MIN_SCORE:
        return None
    return best_line
