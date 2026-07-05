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


def _make_line_mask(img: np.ndarray) -> np.ndarray:
    """创建轨迹线 HSV 掩码"""
    roi = img[FY:FY + FH, FX:FX + FW]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LINE_COLOUR_LOWER, LINE_COLOUR_UPPER)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return mask


def detect_trajectory(img: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """
    检测游戏轨迹线，返回 (launch_x, launch_y, dir_x, dir_y)。

    launch = 底部端点（发射点）
    dir = 从发射点指向顶部端点的方向向量

    Args:
        img: BGR 截图

    Returns:
        (lx, ly, dx, dy) 或 None
    """
    result = _find_best_line(img)
    if result is None:
        return None

    x1, y1, x2, y2 = result
    # 底部端点 = 发射点（y 较大的点）
    if y1 > y2:
        lx, ly, tx, ty = x1, y1, x2, y2
    else:
        lx, ly, tx, ty = x2, y2, x1, y1

    dx = tx - lx
    dy = ty - ly
    return (int(lx), int(ly), int(dx), int(dy))


def detect_launch_point(img: np.ndarray) -> Optional[Tuple[int, int]]:
    """
    检测小球发射点（只返回坐标）。

    Args:
        img: BGR 截图

    Returns:
        (x, y) 发射点坐标，或 None
    """
    traj = detect_trajectory(img)
    if traj is None:
        return None
    return (traj[0], traj[1])


def _find_best_line(img: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """找到最佳的轨迹线，返回绝对坐标 (x1,y1,x2,y2)"""
    mask = _make_line_mask(img)

    # 如果掩码中几乎没有白色像素，说明轨迹线不在画面上
    white_px = cv2.countNonZero(mask)
    if white_px < 200:  # 至少要有一定量的淡青色像素
        return None

    lines = cv2.HoughLinesP(
        mask, rho=1, theta=np.pi / 360,
        threshold=50, minLineLength=60, maxLineGap=30,  # 调高阈值减少噪声
    )
    if lines is None:
        return None

    MIN_SCORE = 0.35  # 低于此分数的认为是噪声
    best_line, best_score = None, -1
    grid_bottom = FY + FH

    for l in lines:
        x1, y1, x2, y2 = l
        dx, dy = x2 - x1, y2 - y1
        length = np.sqrt(dx * dx + dy * dy)
        if length < 40:
            continue

        # 排除水平/垂直线（轨迹线是斜的）
        horiz = abs(dx / max(length, 1))
        if horiz > 0.97 or horiz < 0.08:
            continue

        # 底部端点应该在网格下半部分
        bottom_y = max(y1, y2)
        if bottom_y < FY + FH * 0.35:
            continue

        # 评分
        length_score = min(length / 250, 1.0)
        bottom_score = (bottom_y - FY) / FH
        score = length_score * 0.5 + bottom_score * 0.5

        if score > best_score:
            best_score = score
            best_line = (x1 + FX, y1 + FY, x2 + FX, y2 + FY)

    # 分数不够 → 拒绝
    if best_score < MIN_SCORE:
        return None

    return best_line
