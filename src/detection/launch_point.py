"""发射点检测模块

先用边缘检测找网格内所有线条，再用特征评分识别轨迹线。
不依赖颜色，只依赖"轨迹线是一条斜线，从网格底部发出"这个几何特征。
"""

from typing import Optional, Tuple
import cv2
import numpy as np

from src.config import FX, FY, FW, FH


def detect_trajectory(img: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """
    检测游戏轨迹线，返回 (launch_x, launch_y, dir_x, dir_y)。

    使用边缘检测 + 线条特征评分，不依赖颜色。

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
    """检测小球发射点（只返回坐标）"""
    traj = detect_trajectory(img)
    if traj is None:
        return None
    return (traj[0], traj[1])


def _find_best_line(img: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """用边缘检测找网格内最像轨迹线的线条"""
    roi = img[FY:FY + FH, FX:FX + FW]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # 边缘检测
    edges = cv2.Canny(gray, 30, 100)

    # 统计边缘像素数，太少说明网格内没有显著线条
    edge_px = cv2.countNonZero(edges)
    if edge_px < 100:
        return None

    # 霍夫变换找直线
    lines = cv2.HoughLinesP(
        edges, rho=1, theta=np.pi / 360,
        threshold=40, minLineLength=50, maxLineGap=20,
    )
    if lines is None:
        return None

    MIN_SCORE = 0.3
    best_line, best_score = None, -1
    grid_bottom = FY + FH
    grid_center_x = FX + FW // 2

    for l in lines:
        x1, y1, x2, y2 = l
        length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        if length < 30:
            continue

        # 方向向量
        dx_f, dy_f = x2 - x1, y2 - y1

        # 排除水平/垂直线
        horiz = abs(dx_f / max(length, 1))
        if horiz > 0.95 or horiz < 0.10:
            continue

        # 轨迹线从网格底部发出：至少一个端点在网格下半部
        max_y = max(y1, y2)
        min_y = min(y1, y2)
        if max_y < FH * 0.3:  # 两个端点都在上半部 → 不是
            continue

        # 轨迹线朝上：顶部端点比底部端点至少高 50px
        top_y = min_y
        if (max_y - top_y) < 50:
            continue

        # 评分：线越长越好，底部越靠下越好，向上幅度越大越好
        length_score = min(length / 300, 1.0)
        bottom_score = max_y / FH
        upward_score = min((max_y - top_y) / 200, 1.0)
        score = length_score * 0.35 + bottom_score * 0.35 + upward_score * 0.3

        if score > best_score:
            best_score = score
            best_line = (x1 + FX, y1 + FY, x2 + FX, y2 + FY)

    if best_score < MIN_SCORE:
        return None
    return best_line
