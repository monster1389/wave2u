"""发射点检测模块

帧差法：减去上一帧消除所有静态元素（网格、方块），
只保留轨迹线（动态出现的东西）供 HoughLinesP 检测。

不依赖颜色、不依赖边缘方向，只看「变化」。
"""

from typing import Optional, Tuple
import cv2
import numpy as np

from src.config import FX, FY, FW, FH


def detect_trajectory(img: np.ndarray,
                      prev_img: Optional[np.ndarray] = None
                      ) -> Optional[Tuple[int, int, int, int]]:
    """
    检测游戏轨迹线。

    如果有 prev_img，用帧差法消除静态噪声；
    如果没有，回退到颜色掩码。

    Returns:
        (lx, ly, dx, dy) 发射点坐标和方向向量
    """
    result = _find_best_line(img, prev_img)
    if result is None:
        return None
    x1, y1, x2, y2 = result
    if y1 > y2:
        lx, ly, tx, ty = x1, y1, x2, y2
    else:
        lx, ly, tx, ty = x2, y2, x1, y1
    return (int(lx), int(ly), int(tx - lx), int(ty - ly))


def detect_launch_point(img: np.ndarray,
                        prev_img: Optional[np.ndarray] = None
                        ) -> Optional[Tuple[int, int]]:
    traj = detect_trajectory(img, prev_img)
    if traj is None:
        return None
    return (traj[0], traj[1])


def _find_best_line(img: np.ndarray,
                    prev_img: Optional[np.ndarray] = None
                    ) -> Optional[Tuple[int, int, int, int]]:
    """
    用帧差法找轨迹线。

    1. 如果有 prev_img：diff = absdiff(current, previous)
       diff 中只有动态元素（轨迹线），静态背景 ≈ 0
    2. 如果没有 prev_img：用 HSV 颜色掩码作为 fallback
    3. 在 diff 上跑边缘检测 + HoughLinesP
    """
    roi_curr = img[FY:FY + FH, FX:FX + FW]

    if prev_img is not None:
        roi_prev = prev_img[FY:FY + FH, FX:FX + FW]
        # 帧差：当前帧 - 上一帧
        diff = cv2.absdiff(roi_curr, roi_prev)
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        # 阈值化：只保留显著变化
        _, motion = cv2.threshold(gray_diff, 40, 255, cv2.THRESH_BINARY)
        # 形态学开运算去噪声
        motion = cv2.morphologyEx(motion, cv2.MORPH_OPEN,
                                  np.ones((3, 3), np.uint8), iterations=1)
        source = motion
    else:
        # fallback: HSV 颜色掩码
        hsv = cv2.cvtColor(roi_curr, cv2.COLOR_BGR2HSV)
        source = cv2.inRange(hsv,
            np.array([70, 5, 100]), np.array([130, 180, 255]))

    motion_px = cv2.countNonZero(source)
    if motion_px < 150:
        return None

    # 边缘检测 + HoughLinesP
    edges = cv2.Canny(source, 40, 100)
    lines = cv2.HoughLinesP(
        edges, rho=1, theta=np.pi / 360,
        threshold=60, minLineLength=80, maxLineGap=30,
    )
    if lines is None:
        return None

    if len(lines.shape) == 3:
        lines = lines[:, 0, :]

    MIN_SCORE = 0.35
    best_line, best_score = None, -1.0

    for l in lines:
        x1, y1, x2, y2 = l
        dx_f, dy_f = x2 - x1, y2 - y1
        length = np.sqrt(dx_f ** 2 + dy_f ** 2)
        if length < 60:
            continue

        # 排除水平/垂直线
        horiz = abs(dx_f / max(length, 1))
        if horiz > 0.95 or horiz < 0.06:
            continue

        max_y = max(y1, y2)
        min_y = min(y1, y2)

        # 至少一端在网格下半部
        if max_y < FH * 0.3:
            continue
        # 向上至少 50px
        if (max_y - min_y) < 50:
            continue

        # 评分（帧差法噪声极少，简单评分就够了）
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
