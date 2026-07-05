"""物理引擎单元测试"""

import sys
sys.path.insert(0, "src")

from src.physics.trajectory import simulate, HIT_BLOCK, DROPPED, MAX_STEPS_REACHED
from src.config import FX, FY, FW, FH, BALL_RADIUS


def test_drop_straight_down():
    """垂直向下发射 → 直接底部掉落"""
    sx, sy = FX + FW // 2, FY + 5
    blocks = []
    waypoints, reason, col, row = simulate(sx, sy, 0, 1, blocks)
    assert reason == DROPPED, f"expected DROPPED, got {reason}"
    assert len(waypoints) >= 2


def test_bounce_off_top():
    """向上发射碰到上边界 → 反弹向下"""
    sx, sy = FX + FW // 2, FY + BALL_RADIUS + 30
    blocks = []
    waypoints, reason, col, row = simulate(sx, sy, 0, -1, blocks)
    assert reason == DROPPED, f"expected DROPPED, got {reason}"
    # y 坐标向下增大: 初始向上 → y 减小; 反弹后向下 → y 增大
    ys = [p[1] for p in waypoints]
    min_y = min(ys)
    min_idx = ys.index(min_y)
    # 最低点（反弹点）不在开头也不在结尾
    assert 0 < min_idx < len(ys) - 1, "应该先向上再向下，最低点应在中间"
    # 初始向上走: 第一个 waypoint y 大于第二个
    assert ys[0] > ys[1], "初始应向上（y 减小）"
    # 最终向下走: 最后两个点 y 递增
    assert ys[-1] > ys[-2], "最终应向下（y 增大）"
    # 反弹点应在顶部边界附近
    assert min_y <= FY + BALL_RADIUS + 5, f"反弹点应靠近顶部边界 (actual min_y={min_y}, FY={FY})"


def test_bounce_off_side():
    """45°射向左边界 → 反弹到右侧"""
    sx, sy = FX + 30, FY + FH - 50
    blocks = []
    waypoints, reason, col, row = simulate(sx, sy, -1, -1, blocks)
    assert reason == DROPPED
    # 检查 x 方向有变化：先向左到边界，反弹后向右
    xs = [p[0] for p in waypoints]
    min_x_idx = xs.index(min(xs))
    assert min_x_idx < len(xs) - 1, "应该有反弹后的点"
    assert xs[min_x_idx] <= FX + BALL_RADIUS + 2, "应该触达左边界（球边）"


def test_hit_block():
    """发射击中方块 → 反弹（不终止）"""
    sx, sy = FX + FW // 2, FY + FH - 50
    block = {"col": 3, "row": 3, "x": FX + 200, "y": FY + 200, "w": 106, "h": 105}
    waypoints, reason, col, row = simulate(sx, sy, 0, -1, [block])
    assert reason == DROPPED, f"expected DROPPED (ball bounces and continues), got {reason}"
    assert len(waypoints) > 50, "反弹后应该有足够多的路径点"
    # 验证路径经过了方块区域
    xs = [p[0] for p in waypoints]
    assert max(xs) >= FX + 200, "应该到达方块区域"
    # 验证路径在方块处有方向变化（反弹）
    dir_changes = 0
    for i in range(2, len(waypoints)):
        if (waypoints[i][1]-waypoints[i-1][1])*(waypoints[i-1][1]-waypoints[i-2][1]) < 0:
            dir_changes += 1
    assert dir_changes >= 1, "应该在方块处产生反弹"


def test_multiple_bounces():
    """多次反弹仍然正确终止"""
    sx, sy = FX + 10, FY + FH - 10
    blocks = []
    waypoints, reason, col, row = simulate(sx, sy, 1, -1, blocks)
    assert reason == DROPPED
    # 应该有至少 2 个路径段（至少一次反弹）
    assert len(waypoints) > 50, "多次反弹应该产生很多路径点"


def test_degenerate_vertical():
    """垂直向上发射 → 顶部反弹后底部掉落"""
    sx, sy = FX + FW // 2, FY + BALL_RADIUS + 10
    blocks = []
    waypoints, reason, col, row = simulate(sx, sy, 0, -1, blocks)
    assert reason == DROPPED


def test_degenerate_horizontal():
    """水平向右发射 → 右边界反弹（dy=0 无下落，触发最大步数终止）"""
    sx, sy = FX + 10, FY + FH - 10
    blocks = []
    waypoints, reason, col, row = simulate(sx, sy, 1, 0, blocks)
    # 纯水平运动不会下落，会在左右边界间无限反弹，最终达最大步数
    assert reason == MAX_STEPS_REACHED, f"expected MAX_STEPS_REACHED, got {reason}"
    # 应该触达右边界
    xs = [p[0] for p in waypoints]
    assert max(xs) >= FX + FW - BALL_RADIUS - 5
