"""
根本原因调查 - Phase 1
收集当前检测管线在真实游戏画面上的完整行为证据。
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
import numpy as np
import pyautogui

from src.config import FX, FY, FW, FH
from src.detection.launch_point import detect_trajectory
from src.detection.launch_point import _find_best_line

# HSV 颜色常量（从 launch_point.py 复制，避免 import 循环）
LINE_HUE_LOWER = 70
LINE_HUE_UPPER = 130
LINE_SAT_LOWER = 5
LINE_SAT_UPPER = 180
LINE_VAL_LOWER = 100

print("=" * 60)
print("PHASE 1: 根因证据收集")
print("=" * 60)

# ── 截图 ──
print("\n[证据1] 5秒后截图（请在游戏内拖拽显示轨迹线）...")
for i in range(5, 0, -1):
    print(f"  {i}...")
    time.sleep(1)
s = pyautogui.screenshot()
frame = cv2.cvtColor(np.array(s), cv2.COLOR_RGB2BGR)
h, w = frame.shape[:2]
print(f"  截图尺寸: {w}x{h}")
print(f"  网格区域: ({FX},{FY})-({FX+FW},{FY+FH})")

# ── 证据 A: HSV掩码分析 ──
print("\n[证据A] HSV颜色掩码分析")
roi = frame[FY:FY+FH, FX:FX+FW]
hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

# A1: 当前颜色范围的掩码
mask_current = cv2.inRange(hsv,
    np.array([LINE_HUE_LOWER, LINE_SAT_LOWER, LINE_VAL_LOWER]),
    np.array([LINE_HUE_UPPER, LINE_SAT_UPPER, 255]))
px_current = cv2.countNonZero(mask_current)

# A2: 膨胀后的掩码
kernel = np.ones((5,5), np.uint8)
mask_dilated = cv2.dilate(mask_current, kernel, iterations=2)
px_dilated = cv2.countNonZero(mask_dilated)

print(f"  颜色范围: H={LINE_HUE_LOWER}-{LINE_HUE_UPPER} S={LINE_SAT_LOWER}-{LINE_SAT_UPPER} V={LINE_VAL_LOWER}-255")
print(f"  掩码白色像素(原始): {px_current} ({px_current/(FW*FH)*100:.1f}%)")
print(f"  掩码白色像素(膨胀2x): {px_dilated} ({px_dilated/(FW*FH)*100:.1f}%)")

# A3: 保存掩码图
mask_rgb = cv2.cvtColor(mask_current, cv2.COLOR_GRAY2BGR)
cv2.imwrite("docs/images/rca_mask_raw.png", mask_rgb)
mask_dil_rgb = cv2.cvtColor(mask_dilated, cv2.COLOR_GRAY2BGR)
cv2.imwrite("docs/images/rca_mask_dilated.png", mask_dil_rgb)

# ── 证据 B: HoughLinesP 检测到的线条 ──
print(f"\n[证据B] HoughLinesP 候选线条")

# B1: 在膨胀掩码上运行 HoughLinesP
lines = cv2.HoughLinesP(mask_dilated, rho=1, theta=np.pi/360,
                         threshold=50, minLineLength=60, maxLineGap=30)

# B2: 保存候选线条可视化
line_img = roi.copy()
n_lines = 0
if lines is not None:
    if len(lines.shape) == 3:
        lines = lines[:, 0, :]
    n_lines = len(lines)
    for l in lines:
        x1, y1, x2, y2 = l
        cv2.line(line_img, (x1, y1), (x2, y2), (0, 255, 0), 1)

# 标记所有线条的端点
if lines is not None:
    for i, l in enumerate(lines[:30]):
        x1, y1, x2, y2 = l
        length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
        dx, dy = x2-x1, y2-y1
        horiz = abs(dx / max(length, 1)) if length > 0 else 0
        max_y = max(y1, y2)
        min_y = min(y1, y2)
        upward = max_y - min_y
        print(f"  候选{i}: ({x1+FX:4d},{y1+FY:4d})→({x2+FX:4d},{y2+FY:4d})  "
              f"len={length:.0f}  horiz={horiz:.2f}  bottom={FY+max_y:4d}  up={upward:3d}")

cv2.imwrite("docs/images/rca_candidates.png", line_img)
print(f"\n  HoughLinesP 总计: {n_lines} 条候选线段")
print(f"  (前30条已打印)")

# ── 证据 C: detect_trajectory 最终结果 ──
print(f"\n[证据C] detect_trajectory 最终输出")
traj = detect_trajectory(frame)
result = frame.copy()
cv2.rectangle(result, (FX, FY), (FX+FW, FY+FH), (0, 0, 255), 2)

if traj:
    lx, ly, dx, dy = traj
    cv2.line(result, (lx, ly), (lx+dx, ly+dy), (0, 255, 255), 4)
    cv2.circle(result, (lx, ly), 8, (0, 255, 255), -1)
    print(f"  检测到: 发射点=({lx},{ly}) 方向=({dx},{dy})")
    print(f"          顶部端点=({lx+dx},{ly+dy})")

    # 模拟完整路径
    from src.physics.trajectory import simulate
    waypoints, reason, col, row = simulate(lx, ly, dx, dy, [])
    print(f"  模拟路径: {len(waypoints)} 点, 终止={reason}")

    # 画模拟路径
    for i in range(len(waypoints)-1):
        cv2.line(result, waypoints[i], waypoints[i+1], (0, 200, 200), 2)
else:
    print(f"  未检测到")
    cv2.putText(result, "NOT DETECTED", (FX+50, FY+50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

cv2.imwrite("docs/images/rca_result.png", result)

print(f"\n[已保存]")
print(f"  docs/images/rca_mask_raw.png     - HSV颜色掩码（原始）")
print(f"  docs/images/rca_mask_dilated.png  - 膨胀后掩码")
print(f"  docs/images/rca_candidates.png    - HoughLinesP候选线条（绿色）")
print(f"  docs/images/rca_result.png        - 最终检测+模拟路径")
print(f"\n请查看以上图片，关键问题：")
print(f"1. rca_mask_raw.png - 轨迹线在白色区域里吗？被覆盖了多少？")
print(f"2. rca_candidates.png - 绿色线条中有没有正确选中轨迹线？")
print(f"3. rca_result.png - 最终路径（青色线条）是否正确？")
