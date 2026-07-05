"""小球轨迹模拟：逐步射线投射 + 边界反射"""

from typing import List, Tuple, Optional
from src.config import FX, FY, FW, FH, STEP_SIZE, MAX_STEPS

# 终止原因枚举
HIT_BLOCK = "HIT_BLOCK"
DROPPED = "DROPPED"
MAX_STEPS_REACHED = "MAX_STEPS"

# 路径点：(x, y)
Waypoint = Tuple[int, int]

# 方块描述
Block = dict  # {col, row, x, y, w, h}


def normalize(dx: float, dy: float) -> Tuple[float, float]:
    """归一化方向向量"""
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
    模拟小球轨迹。

    Args:
        sx, sy: 发射点坐标
        dx, dy: 方向向量（未归一化也可）
        blocks: 方块列表 [{col, row, x, y, w, h}, ...]

    Returns:
        (waypoints, reason, hit_col, hit_row)
        waypoints: 路径点列表 [(x1,y1), (x2,y2), ...]
        reason: 终止原因 HIT_BLOCK | DROPPED | MAX_STEPS_REACHED
        hit_col, hit_row: 击中方块的网格坐标（HIT_BLOCK 时有效）
    """
    dir_x, dir_y = normalize(dx, dy)
    px, py = float(sx), float(sy)
    waypoints: List[Waypoint] = [(int(px), int(py))]
    hit_col: Optional[int] = None
    hit_row: Optional[int] = None

    for _ in range(MAX_STEPS):
        px += dir_x * STEP_SIZE
        py += dir_y * STEP_SIZE

        # 底部掉落
        if py >= FY + FH:
            waypoints.append((int(px), int(min(py, FY + FH))))
            return (waypoints, DROPPED, None, None)

        # 上边界反射
        if py <= FY:
            py = FY + 1  # 拉回边界内侧
            dir_y = -dir_y
            waypoints.append((int(px), int(py)))
            continue

        # 左边界反射
        if px <= FX:
            px = FX + 1
            dir_x = -dir_x
            waypoints.append((int(px), int(py)))
            continue

        # 右边界反射
        if px >= FX + FW:
            px = FX + FW - 1
            dir_x = -dir_x
            waypoints.append((int(px), int(py)))
            continue

        # 方块碰撞检测
        for blk in blocks:
            bx, by = blk["x"], blk["y"]
            bw, bh = blk["w"], blk["h"]
            if bx <= px <= bx + bw and by <= py <= by + bh:
                waypoints.append((int(px), int(py)))
                hit_col, hit_row = blk["col"], blk["row"]
                return (waypoints, HIT_BLOCK, hit_col, hit_row)

        # 正常路径点
        waypoints.append((int(px), int(py)))

    return (waypoints, MAX_STEPS_REACHED, None, None)
