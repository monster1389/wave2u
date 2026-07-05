"""发射点检测模块

HSV 颜色定位 + 低阈值 HoughLinesP + 亮度评分选线。
亮度评分让轨迹线（亮）从噪声线（暗）中脱颖而出。
"""

from typing import Optional, Tuple
import cv2
import numpy as np

from src.config import FX, FY, FW, FH

LINE_HUE_LOWER, LINE_HUE_UPPER = 70, 130
LINE_SAT_LOWER, LINE_SAT_UPPER = 5, 180
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
    return (int(lx), int(ly), int(tx - lx), int(ty - ly))


def detect_launch_point(img: np.ndarray) -> Optional[Tuple[int, int]]:
    traj = detect_trajectory(img)
    if traj is None:
        return None
    return (traj[0], traj[1])


def _find_best_line(img: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    roi = img[FY:FY + FH, FX:FX + FW]

    # 1. HSV 颜色掩码
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv,
        np.array([LINE_HUE_LOWER, LINE_SAT_LOWER, LINE_VAL_LOWER]),
        np.array([LINE_HUE_UPPER, LINE_SAT_UPPER, 255]))

    # 2. 形态学闭运算连接断线
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    if cv2.countNonZero(mask) < 200:
        return None

    # 3. 低阈值 HoughLinesP 捕获轨迹线碎片
    lines = cv2.HoughLinesP(
        mask, rho=1, theta=np.pi / 360,
        threshold=50, minLineLength=60, maxLineGap=30,
    )
    if lines is None:
        return None

    if len(lines.shape) == 3:
        lines = lines[:, 0, :]

    # 4. 灰度图用于亮度评分
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    MIN_SCORE = 0.3
    best_line, best_score = None, -1.0

    for l in lines:
        x1, y1, x2, y2 = l
        dx_f, dy_f = x2 - x1, y2 - y1
        length = np.sqrt(dx_f ** 2 + dy_f ** 2)
        if length < 50:
            continue

        # 排除水平/垂直线
        horiz = abs(dx_f / max(length, 1))
        if horiz > 0.95 or horiz < 0.06:
            continue

        max_y = max(y1, y2)
        min_y = min(y1, y2)

        if max_y < FH * 0.3:
            continue
        if (max_y - min_y) < 50:
            continue

        # 5. 亮度评分：沿线条采样平均亮度
        line_mask = np.zeros_like(gray)
        cv2.line(line_mask, (x1, y1), (x2, y2), 255, 3)
        mean_bright = cv2.mean(gray, mask=line_mask)[0]
        brightness_score = min(mean_bright / 200, 1.0)  # 亮度 > 200 满分

        # 综合评分
        length_score = min(length / 300, 1.0)
        bottom_score = max_y / FH
        upward_score = min((max_y - min_y) / 200, 1.0)
        score = (length_score * 0.20 + bottom_score * 0.20 +
                 upward_score * 0.15 + brightness_score * 0.45)

        if score > best_score:
            best_score = score
            best_line = (int(x1 + FX), int(y1 + FY), int(x2 + FX), int(y2 + FY))

    if best_score < MIN_SCORE:
        return None
    return best_line
