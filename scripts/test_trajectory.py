"""
命令行小球轨迹模拟演示。

打印路径点和简易 ASCII 示意图，用于验证反弹物理逻辑。

Usage:
    python scripts/test_trajectory.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.physics.trajectory import simulate, HIT_BLOCK, DROPPED
from src.config import FX, FY, FW, FH


def print_ascii_grid(waypoints, blocks):
    """用 ASCII 打印网格和轨迹"""
    grid_w = 30
    grid_h = 20
    grid = [[" " for _ in range(grid_w)] for _ in range(grid_h)]

    # 网格边界
    for x in range(grid_w):
        grid[0][x] = "-"
        grid[grid_h - 1][x] = "-"
    for y in range(grid_h):
        grid[y][0] = "|"
        grid[y][grid_w - 1] = "|"

    # 方块
    for blk in blocks:
        bx = int((blk["x"] - FX) / FW * (grid_w - 4)) + 2
        by = int((blk["y"] - FY) / FH * (grid_h - 4)) + 2
        if 0 <= by < grid_h and 0 <= bx < grid_w:
            grid[by][bx] = "#"

    # 轨迹
    for i, (px, py) in enumerate(waypoints):
        gx = int((px - FX) / FW * (grid_w - 4)) + 2
        gy = int((py - FY) / FH * (grid_h - 4)) + 2
        if 0 <= gy < grid_h and 0 <= gx < grid_w:
            if i == 0:
                grid[gy][gx] = "S"
            elif i == len(waypoints) - 1:
                grid[gy][gx] = "E"
            elif grid[gy][gx] == " ":
                grid[gy][gx] = "."

    for row in grid:
        print("".join(row))


def main():
    print("=" * 50)
    print("NIKKE 轨迹模拟测试")
    print("=" * 50)

    # 测试 1：垂直向下（直接掉落）
    print("\n[测试 1] 垂直向下 → 底部掉落")
    blocks = []
    waypoints, reason, col, row = simulate(FX + FW // 2, FY + 5, 0, 1, blocks)
    print(f"  原因: {reason}, 路径点: {len(waypoints)}")
    print_ascii_grid(waypoints, blocks)

    # 测试 2：45°向右上 → 反弹
    print("\n[测试 2] 45°向右上 → 反弹")
    waypoints, reason, col, row = simulate(FX + 10, FY + FH - 10, 1, -1, blocks)
    print(f"  原因: {reason}, 路径点: {len(waypoints)}")

    # 测试 3：击中方块
    print("\n[测试 3] 击中方块")
    block = {"col": 3, "row": 3, "x": FX + 200, "y": FY + 200, "w": 106, "h": 105}
    waypoints, reason, col, row = simulate(FX + 10, FY + FH - 10, 0.2, -1, [block])
    print(f"  原因: {reason}, 击中: ({col},{row}), 路径点: {len(waypoints)}")
    print_ascii_grid(waypoints, [block])

    print("\n完成!")


if __name__ == "__main__":
    main()
