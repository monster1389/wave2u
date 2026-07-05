"""
调试：检测游戏轨迹线并保存标注截图。

运行后打开 docs/images/debug_trajectory.png 查看检测结果。

运行：
    .venv/Scripts/python scripts/debug_trajectory.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
import numpy as np
import pyautogui

from src.detection.launch_point import detect_trajectory, _find_best_line, _make_line_mask
from src.config import FX, FY, FW, FH


def main():
    print("=" * 50)
    print("轨迹线检测调试")
    print("=" * 50)

    # 1. 截图
    print("\n[1] 截图...")
    s = pyautogui.screenshot()
    frame = cv2.cvtColor(np.array(s), cv2.COLOR_RGB2BGR)
    print(f"    分辨率: {frame.shape[1]}x{frame.shape[0]}")

    # 2. 画网格参考框
    debug = frame.copy()
    cv2.rectangle(debug, (FX, FY), (FX + FW, FY + FH), (0, 0, 255), 2)

    # 3. 显示 HSV 掩码（看颜色范围是否匹配）
    mask = _make_line_mask(frame)
    # 把掩码转成彩色以便保存
    mask_color = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    cv2.imwrite("docs/images/debug_mask.png", mask_color)
    print(f"    HSV 掩码已保存: docs/images/debug_mask.png")
    white_px = cv2.countNonZero(mask)
    print(f"    掩码中白色像素: {white_px} (越大说明颜色匹配越多)")

    # 4. 运行检测
    print("\n[2] 检测轨迹线...")
    traj = detect_trajectory(frame)
    if traj:
        lx, ly, dx, dy = traj
        print(f"    发射点: ({lx}, {ly})")
        print(f"    方向: ({dx}, {dy})")
        tx, ty = lx + dx, ly + dy
        print(f"    顶部端点: ({tx}, {ty})")

        # 画检测到的轨迹线（青色）
        cv2.line(debug, (lx, ly), (tx, ty), (0, 255, 255), 4)
        # 画发射点（黄色圆）
        cv2.circle(debug, (lx, ly), 8, (0, 255, 255), -1)
        # 画顶部端点（品红圆）
        cv2.circle(debug, (tx, ty), 6, (255, 0, 255), -1)

        cv2.putText(debug, f"发射点 ({lx},{ly})", (lx + 10, ly - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        cv2.putText(debug, f"方向 ({dx},{dy})", (tx + 10, ty - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
    else:
        print("    未检测到轨迹线")
        cv2.putText(debug, "未检测到轨迹线", (100, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # 5. 画出所有 HoughLinesP 检测到的线段（灰色，用于调试）
    lines = cv2.HoughLinesP(
        mask, rho=1, theta=np.pi / 360,
        threshold=30, minLineLength=40, maxLineGap=50,
    )
    if lines is not None:
        print(f"\n[3] HoughLinesP 检测到 {len(lines)} 条线段:")
        for i, l in enumerate(lines[:5]):  # 只显示前5条
            x1, y1, x2, y2 = l  # HoughLinesP 返回 (N,4) 格式
            print(f"    线段 {i+1}: ({x1+FX},{y1+FY})→({x2+FX},{y2+FY})")
            # 画灰色线段（所有候选）
            cv2.line(debug, (x1+FX, y1+FY), (x2+FX, y2+FY), (128, 128, 128), 1)

    # 6. 保存标注截图
    cv2.imwrite("docs/images/debug_trajectory.png", debug)
    print(f"\n[4] 标注截图已保存: docs/images/debug_trajectory.png")
    print("    请打开这个文件查看检测结果")
    print("    黄色=发射点  品红=顶部端点  灰色=所有候选线段")


if __name__ == "__main__":
    main()
