"""
诊断 v3：在真实游戏截图上可视化边缘检测结果。
看 Canny 到底找到了哪些边缘，哪些线条被选中。
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

print("=" * 50)
print("诊断 v3: 边缘检测可视化")
print("=" * 50)
print("\n5秒后截图，请让游戏显示轨迹线...")
for i in range(5, 0, -1):
    print(f"  {i}...")
    time.sleep(1)

s = pyautogui.screenshot()
frame = cv2.cvtColor(np.array(s), cv2.COLOR_RGB2BGR)
print(f"截图: {frame.shape[1]}x{frame.shape[0]}")

roi = frame[FY:FY+FH, FX:FX+FW]
gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

# 1. 显示灰度图
cv2.imwrite("docs/images/dbg_gray.png", gray)

# 2. Canny 边缘
edges = cv2.Canny(gray, 30, 100)
edge_count = cv2.countNonZero(edges)
print(f"\nCanny 边缘像素: {edge_count}")
# 把边缘叠加到 roi 上（红色显示）
edge_overlay = roi.copy()
edge_overlay[edges > 0] = (0, 0, 255)
cv2.imwrite("docs/images/dbg_edges.png", edge_overlay)

# 3. 尝试不同 Canny 参数
for lo, hi in [(20, 60), (30, 100), (50, 150), (80, 200)]:
    e = cv2.Canny(gray, lo, hi)
    print(f"  Canny({lo},{hi}): {cv2.countNonZero(e)} 边缘像素")

# 4. HoughLinesP 结果
lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/360, threshold=40, minLineLength=50, maxLineGap=20)
print(f"\nHoughLinesP: {len(lines) if lines is not None else 0} 条线段")
line_overlay = roi.copy()
if lines is not None:
    for i, l in enumerate(lines):
        x1, y1, x2, y2 = l
        dx, dy = x2-x1, y2-y1
        length = np.sqrt(dx*dx + dy*dy)
        horiz = abs(dx / max(length, 1))
        max_y = max(y1, y2)
        min_y = min(y1, y2)
        upward = max_y - min_y
        print(f"  线{i}: ({x1+FX:4d},{y1+FY:4d})→({x2+FX:4d},{y2+FY:4d})  "
              f"len={length:.0f} horiz={horiz:.2f} upward={upward}")
        cv2.line(line_overlay, (x1, y1), (x2, y2), (0, 255, 0), 1)
cv2.imwrite("docs/images/dbg_hough_lines.png", line_overlay)

# 5. detect_trajectory 的结果
traj = detect_trajectory(frame)
result = frame.copy()
cv2.rectangle(result, (FX, FY), (FX+FW, FY+FH), (0, 0, 255), 2)
if traj:
    lx, ly, dx, dy = traj
    cv2.line(result, (lx, ly), (lx+dx, ly+dy), (0, 255, 255), 4)
    cv2.circle(result, (lx, ly), 8, (0, 255, 255), -1)
    cv2.putText(result, f"发射点({lx},{ly})", (lx+10, ly-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    cv2.putText(result, f"方向({dx},{dy})", (lx+dx+10, ly+dy-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
    print(f"\ndetect_trajectory: 发射点=({lx},{ly}) 方向=({dx},{dy})")
else:
    print(f"\ndetect_trajectory: 未检测到")
    cv2.putText(result, "未检测到", (100, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

cv2.imwrite("docs/images/dbg_result.png", result)
# 只保存 roi 区域的结果
roi_result = result[FY:FY+FH, FX:FX+FW]
cv2.imwrite("docs/images/dbg_result_roi.png", roi_result)

print(f"\n已保存:")
print(f"  docs/images/dbg_gray.png       - 网格灰度图")
print(f"  docs/images/dbg_edges.png       - Canny 边缘（红色）")
print(f"  docs/images/dbg_hough_lines.png - HoughLinesP 找到的线段（绿色）")
print(f"  docs/images/dbg_result_roi.png  - 最终检测结果（网格区域）")
