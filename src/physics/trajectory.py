"""小球轨迹模拟：逐步射线投射 + 边界反射 + 方块弹射"""

from typing import List, Tuple, Optional
from src.config import FX, FY, FW, FH, STEP_SIZE, MAX_STEPS, BALL_RADIUS

HIT_BLOCK = "HIT_BLOCK"
DROPPED = "DROPPED"
MAX_STEPS_REACHED = "MAX_STEPS"

Waypoint = Tuple[int, int]
Block = dict  # {col, row, x, y, w, h}


def normalize(dx: float, dy: float) -> Tuple[float, float]:
    length = (dx * dx + dy * dy) ** 0.5
    if length == 0:
        return (0.0, 1.0)
    return (dx / length, dy / length)


def simulate(
    sx: int, sy: int,
    dx: float, dy: float,
    blocks: List[Block],
) -> Tuple[List[Waypoint], str, Optional[int], Optional[int]]:
    dir_x, dir_y = normalize(dx, dy)
    px, py = float(sx), float(sy)
    waypoints: List[Waypoint] = [(int(px), int(py))]
    hit_count = {}  # (col,row) → hit count (保留给后续血量用)

    top = FY + BALL_RADIUS
    left = FX + BALL_RADIUS
    right = FX + FW - BALL_RADIUS
    bottom = FY + FH

    for _ in range(MAX_STEPS):
        # 记录碰撞前位置（用于判断从哪个方向撞上）
        px_prev, py_prev = px, py
        px += dir_x * STEP_SIZE
        py += dir_y * STEP_SIZE

        # 底部掉落
        if py >= bottom:
            waypoints.append((int(px), int(min(py, bottom))))
            return (waypoints, DROPPED, None, None)

        # 方块碰撞（先于边界检测，让球在边界附近碰到方块时正确处理）
        block_hit = False
        for blk in blocks:
            bx, by = blk["x"], blk["y"]
            bw, bh = blk["w"], blk["h"]
            if not (px + BALL_RADIUS >= bx and px - BALL_RADIUS <= bx + bw and
                    py + BALL_RADIUS >= by and py - BALL_RADIUS <= by + bh):
                continue

            # 计算各方向穿透距离，角碰撞时只反射穿透更大的轴
            pen_x = 0
            if px_prev + BALL_RADIUS <= bx:  # 从左边来
                pen_x = (px + BALL_RADIUS) - bx
            elif px_prev - BALL_RADIUS >= bx + bw:  # 从右边来
                pen_x = (bx + bw) - (px - BALL_RADIUS)

            pen_y = 0
            if py_prev + BALL_RADIUS <= by:  # 从上面来
                pen_y = (py + BALL_RADIUS) - by
            elif py_prev - BALL_RADIUS >= by + bh:  # 从下面来
                pen_y = (by + bh) - (py - BALL_RADIUS)

            # 穿透更大的轴决定反射方向
            if abs(pen_x) >= abs(pen_y):
                if px_prev + BALL_RADIUS <= bx:
                    px = bx - BALL_RADIUS - 1
                    dir_x = -dir_x
                elif px_prev - BALL_RADIUS >= bx + bw:
                    px = bx + bw + BALL_RADIUS + 1
                    dir_x = -dir_x
            else:
                if py_prev + BALL_RADIUS <= by:
                    py = by - BALL_RADIUS - 1
                    dir_y = -dir_y
                elif py_prev - BALL_RADIUS >= by + bh:
                    py = by + bh + BALL_RADIUS + 1
                    dir_y = -dir_y

            block_hit = True
            break  # 一次只处理一个方块

        if block_hit:
            # 不在这里记录路径点（避免零长度线段），
            # 让下一轮迭代自然产生新方向的第一个点
            continue

        # 上边界反射
        if py <= top:
            py = top + 1
            dir_y = -dir_y
            waypoints.append((int(px), int(py)))
            continue

        # 左边界反射
        if px <= left:
            px = left + 1
            dir_x = -dir_x
            waypoints.append((int(px), int(py)))
            continue

        # 右边界反射
        if px >= right:
            px = right - 1
            dir_x = -dir_x
            waypoints.append((int(px), int(py)))
            continue

        # 正常路径点
        waypoints.append((int(px), int(py)))

    return (waypoints, MAX_STEPS_REACHED, None, None)
