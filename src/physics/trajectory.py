"""小球轨迹模拟：逐步射线投射 + 边界反射"""

from typing import List, Tuple, Optional
from src.config import FX, FY, FW, FH, STEP_SIZE, MAX_STEPS, BALL_RADIUS

# 终止原因枚举
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
    """
    模拟小球轨迹（考虑小球半径带来的碰撞偏移）。

    碰撞检测使用球心坐标，但边界/方块碰撞面偏移 BALL_RADIUS 像素。
    """
    dir_x, dir_y = normalize(dx, dy)
    px, py = float(sx), float(sy)
    waypoints: List[Waypoint] = [(int(px), int(py))]
    hit_col: Optional[int] = None
    hit_row: Optional[int] = None

    # 考虑半径的有效边界
    top = FY + BALL_RADIUS
    left = FX + BALL_RADIUS
    right = FX + FW - BALL_RADIUS
    bottom = FY + FH

    for _ in range(MAX_STEPS):
        px += dir_x * STEP_SIZE
        py += dir_y * STEP_SIZE

        # 底部掉落（球心超出底部）
        if py >= bottom:
            waypoints.append((int(px), int(min(py, bottom))))
            return (waypoints, DROPPED, None, None)

        # 上边界反射（球边触顶）
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

        # 方块碰撞（考虑球半径：球边界碰方块边界）
        for blk in blocks:
            bx, by = blk["x"], blk["y"]
            bw, bh = blk["w"], blk["h"]
            # 球边与方块边的碰撞检测
            if (px + BALL_RADIUS >= bx and px - BALL_RADIUS <= bx + bw and
                py + BALL_RADIUS >= by and py - BALL_RADIUS <= by + bh):
                waypoints.append((int(px), int(py)))
                hit_col, hit_row = blk["col"], blk["row"]
                return (waypoints, HIT_BLOCK, hit_col, hit_row)

        # 正常路径点
        waypoints.append((int(px), int(py)))

    return (waypoints, MAX_STEPS_REACHED, None, None)
