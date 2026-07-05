"""
根本原因诊断：对比 find_yellow_annotation 和 detect_trajectory
在相同截图上的检测结果。

运行方法：
    1. 5秒内让游戏显示轨迹线
    2. 截图保存
    3. 分别用两种方法检测
    4. 结果对比

运行：
    .venv/Scripts/python scripts/debug_root_cause.py
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
import numpy as np
import pyautogui

from src.config import FX, FY, FW, FH
from src.detection.launch_point import detect_trajectory, _find_best_line, _make_line_mask

print("=" * 60)
print("根本原因诊断：对比两种检测方法")
print("=" * 60)

# 截图
print("\n[1] 5秒后截图（请在游戏内显示轨迹线）...")
for i in range(5, 0, -1):
    print(f"    {i}...")
    time.sleep(1)
s = pyautogui.screenshot()
frame = cv2.cvtColor(np.array(s), cv2.COLOR_RGB2BGR)
print(f"    截图: {frame.shape[1]}x{frame.shape[0]}")
cv2.imwrite("docs/images/debug_root_frame.png", frame)

# 方法 A: 当前生产代码的 detect_trajectory
print("\n[2] 方法 A: detect_trajectory (生产代码)")
mask = _make_line_mask(frame)
white_px = cv2.countNonZero(mask)
print(f"    掩码白色像素: {white_px}")

traj = detect_trajectory(frame)
if traj:
    lx, ly, dx, dy = traj
    print(f"    ✅ 检测到: 发射点=({lx},{ly}) 方向=({dx},{dy})")
    print(f"               顶部端点=({lx+dx},{ly+dy})")
else:
    print(f"    ❌ 未检测到")

# 保存白像素位置统计
mask_debug = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
ys, xs = np.where(mask > 0)
if len(xs) > 0:
    print(f"\n[3] 掩码白色像素分布:")
    # 按 y 坐标分段统计
    for y_start in range(0, FH, FH // 8):
        y_end = y_start + FH // 8
        count = np.sum((ys >= y_start) & (ys < y_end))
        px = (count / max(len(xs), 1)) * 100
        print(f"    行 {FY+y_start:4d}-{FY+y_end:4d}: {count:5d} 像素 ({px:.0f}%)")
        # 在这一行区域画出检测到的线条
        cv2.line(mask_debug, (0, FY+y_start), (FW, FY+y_start), (0, 255, 0), 1)

# 画上所有 HoughLinesP 检测到的线条
lines = cv2.HoughLinesP(mask, rho=1, theta=np.pi/360, threshold=30, minLineLength=40, maxLineGap=50)
print(f"\n[4] HoughLinesP 检测到 {len(lines) if lines is not None else 0} 条线段")
if lines is not None:
    for i, l in enumerate(lines[:20]):
        x1, y1, x2, y2 = l
        dx, dy = x2 - x1, y2 - y1
        length = np.sqrt(dx*dx + dy*dy)
        horiz = abs(dx / max(length, 1))
        bottom_y = max(y1, y2)
        print(f"    线段 {i+1:2d}: ({x1+FX:4d},{y1+FY:4d})→({x2+FX:4d},{y2+FY:4d})  "
              f"len={length:.0f} horiz={horiz:.2f} bottom={FY+bottom_y:4d}")
        cv2.line(mask_debug, (x1, y1), (x2, y2), (0, 0, 255), 1)

cv2.imwrite("docs/images/debug_root_mask.png", mask_debug)

# 画最终结果
result = frame.copy()
cv2.rectangle(result, (FX, FY), (FX+FW, FY+FH), (0, 0, 255), 2)
if traj:
    lx, ly, dx, dy = traj
    cv2.line(result, (lx, ly), (lx+dx, ly+dy), (0, 255, 255), 4)
    cv2.circle(result, (lx, ly), 8, (0, 255, 255), -1)
cv2.imwrite("docs/images/debug_root_result.png", result)

print(f"\n[5] 已保存:")
print(f"    docs/images/debug_root_frame.png  - 原始截图")
print(f"    docs/images/debug_root_mask.png   - HSV掩码+检测线条")
print(f"    docs/images/debug_root_result.png - 最终检测结果")
print(f"\n请打开 debug_root_mask.png 看 HSV 掩码到底覆盖了什么")
print("红色线条 = HoughLinesP 找到的所有线段")
print("如果掩码中轨迹线很少但红色线条很多 = 颜色范围不对")
print("如果掩码中轨迹线很清楚但红色线条选错了 = 评分逻辑问题")
